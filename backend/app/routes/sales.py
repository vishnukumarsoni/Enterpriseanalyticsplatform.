from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.filters import AnalyticsFilters
from app.services.query_builder import build_order_filters

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("")
def get_sales(filters: AnalyticsFilters = Depends(), db: Session = Depends(get_db)):
    where_sql, params = build_order_filters(filters)

    trend_sql = f"""
        SELECT DATE_TRUNC('month', o.order_date)::date AS month,
               SUM(o.revenue) AS revenue, COUNT(DISTINCT o.order_id) AS orders
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql} GROUP BY 1 ORDER BY 1
    """
    monthly_trend = [dict(r) for r in db.execute(text(trend_sql), params).mappings().all()]

    # NOTE: targets and orders are pre-aggregated in separate subqueries before
    # joining, to avoid a join fan-out that would otherwise multiply
    # target_amount by the number of matching order rows.
    target_sql = """
        SELECT e.employee_id, e.employee_name, e.region,
               COALESCE(t.target_amount, 0) AS target_amount,
               COALESCE(o.actual_revenue, 0) AS actual_revenue,
               ROUND(COALESCE(o.actual_revenue, 0) / NULLIF(t.target_amount, 0) * 100, 2) AS achievement_pct
        FROM employees e
        LEFT JOIN (
            SELECT employee_id, SUM(target_amount) AS target_amount
            FROM targets GROUP BY employee_id
        ) t ON t.employee_id = e.employee_id
        LEFT JOIN (
            SELECT employee_id, SUM(revenue) AS actual_revenue
            FROM orders WHERE order_status <> 'Cancelled' GROUP BY employee_id
        ) o ON o.employee_id = e.employee_id
        ORDER BY achievement_pct DESC NULLS LAST
    """
    target_vs_actual = [dict(r) for r in db.execute(text(target_sql)).mappings().all()]

    ranking_sql = f"""
        SELECT e.employee_id, e.employee_name, e.region,
               SUM(o.revenue) AS revenue,
               RANK() OVER (ORDER BY SUM(o.revenue) DESC) AS rank
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql} GROUP BY e.employee_id, e.employee_name, e.region
        ORDER BY revenue DESC
    """
    salesperson_ranking = [dict(r) for r in db.execute(text(ranking_sql), params).mappings().all()]

    region_rank_sql = f"""
        SELECT c.region, SUM(o.revenue) AS revenue,
               RANK() OVER (ORDER BY SUM(o.revenue) DESC) AS rank
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql} GROUP BY c.region ORDER BY revenue DESC
    """
    region_ranking = [dict(r) for r in db.execute(text(region_rank_sql), params).mappings().all()]

    return {
        "monthly_trend": monthly_trend,
        "target_vs_actual": target_vs_actual,
        "salesperson_ranking": salesperson_ranking,
        "region_ranking": region_ranking,
    }
