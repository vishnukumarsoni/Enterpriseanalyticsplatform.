"""
Automated Business Insights Engine
====================================
Generates natural-language business insight statements dynamically from
live database queries. No insight text is hard-coded — every statement is
built by inserting computed numbers into a template, and templates are only
selected when their underlying condition is actually true.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
def get_insights(db: Session = Depends(get_db)):
    insights = []

    # 1. Revenue growth: trailing 12 months vs the prior 12 months (fair
    # like-for-like comparison; avoids comparing a partial current year
    # against a full prior year, which would be misleading).
    ttm_sql = """
        WITH bounds AS (
            SELECT MAX(order_date) AS max_date FROM orders WHERE order_status <> 'Cancelled'
        )
        SELECT
            SUM(revenue) FILTER (
                WHERE order_date > (SELECT max_date FROM bounds) - INTERVAL '12 months'
            ) AS trailing_12m,
            SUM(revenue) FILTER (
                WHERE order_date <= (SELECT max_date FROM bounds) - INTERVAL '12 months'
                  AND order_date > (SELECT max_date FROM bounds) - INTERVAL '24 months'
            ) AS prior_12m
        FROM orders WHERE order_status <> 'Cancelled'
    """
    row = db.execute(text(ttm_sql)).mappings().first()
    if row and row["prior_12m"]:
        pct = round((row["trailing_12m"] - row["prior_12m"]) / row["prior_12m"] * 100, 1)
        direction = "increased" if pct >= 0 else "decreased"
        insights.append({
            "category": "Revenue",
            "text": f"Revenue {direction} {abs(pct)}% over the trailing 12 months "
                    f"compared to the prior 12-month period."
        })

    # 2. Best region by revenue
    region_sql = """
        SELECT c.region, SUM(o.revenue) AS revenue
        FROM orders o JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_status <> 'Cancelled' GROUP BY c.region ORDER BY revenue DESC LIMIT 1
    """
    row = db.execute(text(region_sql)).mappings().first()
    if row:
        insights.append({
            "category": "Regional",
            "text": f"The {row['region']} region generates the highest revenue at "
                    f"₹{row['revenue']:,.0f}."
        })

    # 3. Category with high revenue but below-average margin
    category_sql = """
        WITH cat_stats AS (
            SELECT p.category, SUM(o.revenue) AS revenue,
                   ROUND(SUM(o.profit) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS margin_pct
            FROM orders o JOIN products p ON p.product_id = o.product_id
            WHERE o.order_status <> 'Cancelled' GROUP BY p.category
        )
        SELECT category, revenue, margin_pct,
               (SELECT AVG(margin_pct) FROM cat_stats) AS avg_margin
        FROM cat_stats ORDER BY revenue DESC
    """
    rows = db.execute(text(category_sql)).mappings().all()
    if rows:
        avg_margin = rows[0]["avg_margin"]
        top_rev_cat = rows[0]
        if top_rev_cat["margin_pct"] is not None and avg_margin is not None and top_rev_cat["margin_pct"] < avg_margin:
            insights.append({
                "category": "Product",
                "text": f"{top_rev_cat['category']} has the highest revenue but a below-average "
                        f"profit margin of {top_rev_cat['margin_pct']}% versus a {round(avg_margin, 1)}% "
                        f"average across categories."
            })

    # 4. Churn risk share
    churn_sql = """
        SELECT
            COUNT(*) FILTER (WHERE risk_level = 'High') AS high_risk,
            COUNT(*) AS total
        FROM customer_churn_predictions
    """
    row = db.execute(text(churn_sql)).mappings().first()
    if row and row["total"]:
        pct = round(row["high_risk"] / row["total"] * 100, 1)
        insights.append({
            "category": "Customer",
            "text": f"{pct}% of customers are classified as high churn risk based on the "
                    f"churn prediction model."
        })

    # 5. Revenue concentration (top 10 customers)
    concentration_sql = """
        WITH cust_rev AS (
            SELECT customer_id, SUM(revenue) AS revenue
            FROM orders WHERE order_status <> 'Cancelled' GROUP BY customer_id
        )
        SELECT
            (SELECT SUM(revenue) FROM (SELECT revenue FROM cust_rev ORDER BY revenue DESC LIMIT 10) t) AS top10_revenue,
            (SELECT SUM(revenue) FROM cust_rev) AS total_revenue
    """
    row = db.execute(text(concentration_sql)).mappings().first()
    if row and row["total_revenue"]:
        pct = round(row["top10_revenue"] / row["total_revenue"] * 100, 1)
        insights.append({
            "category": "Customer",
            "text": f"The top 10 customers contribute {pct}% of total revenue."
        })

    # 6. Discount impact on margin
    discount_sql = """
        SELECT
            ROUND(AVG(profit / NULLIF(revenue, 0)) FILTER (WHERE discount > 0.15) * 100, 2) AS high_discount_margin,
            ROUND(AVG(profit / NULLIF(revenue, 0)) FILTER (WHERE discount <= 0.15) * 100, 2) AS low_discount_margin
        FROM orders WHERE order_status <> 'Cancelled' AND revenue > 0
    """
    row = db.execute(text(discount_sql)).mappings().first()
    if row and row["high_discount_margin"] is not None and row["low_discount_margin"] is not None:
        diff = round(row["low_discount_margin"] - row["high_discount_margin"], 1)
        if diff > 0:
            insights.append({
                "category": "Pricing",
                "text": f"Orders discounted above 15% carry an average margin of "
                        f"{row['high_discount_margin']}%, {diff} percentage points lower than "
                        f"orders discounted 15% or less."
            })

    # 7. Target achievement
    target_sql = """
        SELECT
            COUNT(*) FILTER (WHERE achievement_pct >= 100) AS meeting_target,
            COUNT(*) AS total
        FROM (
            SELECT e.employee_id,
                   ROUND(COALESCE(SUM(o.revenue), 0) / NULLIF(e.target_amount, 0) * 100, 2) AS achievement_pct
            FROM employees e
            LEFT JOIN orders o ON o.employee_id = e.employee_id AND o.order_status <> 'Cancelled'
            GROUP BY e.employee_id, e.target_amount
        ) t
    """
    row = db.execute(text(target_sql)).mappings().first()
    if row and row["total"]:
        pct = round(row["meeting_target"] / row["total"] * 100, 1)
        insights.append({
            "category": "Sales",
            "text": f"{pct}% of salespeople are meeting or exceeding their annual sales target."
        })

    # 8. Return rate outlier product
    return_sql = """
        SELECT p.product_name, COUNT(r.return_id)::numeric / NULLIF(COUNT(o.order_id), 0) * 100 AS return_rate
        FROM products p JOIN orders o ON o.product_id = p.product_id
        LEFT JOIN returns r ON r.order_id = o.order_id
        GROUP BY p.product_name
        HAVING COUNT(o.order_id) > 20
        ORDER BY return_rate DESC LIMIT 1
    """
    row = db.execute(text(return_sql)).mappings().first()
    if row and row["return_rate"] and row["return_rate"] > 0:
        insights.append({
            "category": "Product",
            "text": f"{row['product_name']} has the highest return rate at "
                    f"{round(row['return_rate'], 1)}% among frequently ordered products."
        })

    return {"insights": insights, "generated_from": "live database aggregation (not hard-coded)"}
