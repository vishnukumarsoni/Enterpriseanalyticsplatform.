import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.filters import AnalyticsFilters
from app.services.query_builder import build_order_filters

log = logging.getLogger("routes.dashboard")
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(filters: AnalyticsFilters = Depends(), db: Session = Depends(get_db)):
    where_sql, params = build_order_filters(filters)

    kpi_sql = f"""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(o.revenue), 0) AS total_revenue,
            COALESCE(SUM(o.profit), 0) AS total_profit,
            ROUND(COALESCE(SUM(o.profit), 0) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS profit_margin_pct,
            COUNT(DISTINCT o.customer_id) AS active_customers
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
    """
    kpis = dict(db.execute(text(kpi_sql), params).mappings().first())

    ttm_sql = f"""
        WITH bounds AS (
            SELECT MAX(o.order_date) AS max_date
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN products p ON p.product_id = o.product_id
            JOIN employees e ON e.employee_id = o.employee_id
            WHERE {where_sql}
        )
        SELECT
            SUM(o.revenue) FILTER (
                WHERE o.order_date > (SELECT max_date FROM bounds) - INTERVAL '12 months'
            ) AS trailing_12m,
            SUM(o.revenue) FILTER (
                WHERE o.order_date <= (SELECT max_date FROM bounds) - INTERVAL '12 months'
                  AND o.order_date > (SELECT max_date FROM bounds) - INTERVAL '24 months'
            ) AS prior_12m
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
    """
    ttm_row = db.execute(text(ttm_sql), params).mappings().first()
    if ttm_row and ttm_row["prior_12m"]:
        kpis["yoy_growth_pct"] = round(
            (ttm_row["trailing_12m"] - ttm_row["prior_12m"]) / ttm_row["prior_12m"] * 100, 2
        )
    else:
        kpis["yoy_growth_pct"] = None

    trend_sql = f"""
        SELECT DATE_TRUNC('month', o.order_date)::date AS month,
               SUM(o.revenue) AS revenue, SUM(o.profit) AS profit
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
        GROUP BY 1 ORDER BY 1
    """
    revenue_trend = [dict(r) for r in db.execute(text(trend_sql), params).mappings().all()]

    region_sql = f"""
        SELECT c.region, SUM(o.revenue) AS revenue
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
        GROUP BY c.region ORDER BY revenue DESC
    """
    revenue_by_region = [dict(r) for r in db.execute(text(region_sql), params).mappings().all()]

    category_sql = f"""
        SELECT p.category, SUM(o.revenue) AS revenue
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
        GROUP BY p.category ORDER BY revenue DESC
    """
    revenue_by_category = [dict(r) for r in db.execute(text(category_sql), params).mappings().all()]

    top_products_sql = f"""
        SELECT p.product_name, SUM(o.revenue) AS revenue
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
        GROUP BY p.product_name ORDER BY revenue DESC LIMIT 10
    """
    top_products = [dict(r) for r in db.execute(text(top_products_sql), params).mappings().all()]

    segment_sql = f"""
        SELECT c.customer_segment, COUNT(DISTINCT c.customer_id) AS customer_count
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p ON p.product_id = o.product_id
        JOIN employees e ON e.employee_id = o.employee_id
        WHERE {where_sql}
        GROUP BY c.customer_segment
    """
    segment_distribution = [dict(r) for r in db.execute(text(segment_sql), params).mappings().all()]

    return {
        "kpis": kpis,
        "revenue_trend": revenue_trend,
        "revenue_by_region": revenue_by_region,
        "revenue_by_category": revenue_by_category,
        "top_products": top_products,
        "customer_segment_distribution": segment_distribution,
    }
