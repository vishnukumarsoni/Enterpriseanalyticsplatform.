from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.filters import AnalyticsFilters
from app.services.query_builder import build_order_filters

router = APIRouter(prefix="/api/regions", tags=["regions"])


@router.get("")
def get_regions(filters: AnalyticsFilters = Depends(), db: Session = Depends(get_db)):
    where_sql, params = build_order_filters(filters)

    summary_sql = f"""
        SELECT c.region,
               COUNT(DISTINCT c.customer_id) AS customer_count,
               COUNT(o.order_id) AS total_orders,
               SUM(o.revenue) AS total_revenue,
               SUM(o.profit) AS total_profit,
               ROUND(SUM(o.profit) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS profit_margin_pct
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql}
        GROUP BY c.region ORDER BY total_revenue DESC
    """
    region_summary = [dict(r) for r in db.execute(text(summary_sql), params).mappings().all()]

    growth_sql = f"""
        WITH monthly AS (
            SELECT c.region, DATE_TRUNC('month', o.order_date)::date AS month, SUM(o.revenue) AS revenue
            FROM orders o JOIN customers c ON c.customer_id=o.customer_id
            JOIN products p ON p.product_id=o.product_id
            JOIN employees e ON e.employee_id=o.employee_id
            WHERE {where_sql}
            GROUP BY c.region, 2
        )
        SELECT region, month, revenue,
               LAG(revenue) OVER (PARTITION BY region ORDER BY month) AS prev_month_revenue
        FROM monthly ORDER BY region, month
    """
    region_trend = [dict(r) for r in db.execute(text(growth_sql), params).mappings().all()]

    return {"region_summary": region_summary, "region_trend": region_trend}
