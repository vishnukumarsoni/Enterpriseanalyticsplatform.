from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/employees", tags=["employees"])


def classify_performance(pct):
    if pct is None:
        return "No Data"
    if pct >= 110:
        return "Top Performer"
    if pct >= 90:
        return "Strong Performer"
    if pct >= 70:
        return "Average Performer"
    return "Needs Improvement"


@router.get("")
def get_employees(db: Session = Depends(get_db)):
    sql = """
        SELECT e.employee_id, e.employee_name, e.department, e.region, e.joining_date,
               e.target_amount AS annual_target,
               COALESCE(t.total_target, 0) AS total_target_full_period,
               COALESCE(o.total_revenue, 0) AS total_revenue,
               COALESCE(o.total_profit, 0) AS total_profit,
               COALESCE(o.total_orders, 0) AS total_orders,
               COALESCE(o.customer_count, 0) AS customer_count,
               ROUND(COALESCE(o.total_revenue, 0) / NULLIF(t.total_target, 0) * 100, 2) AS target_achievement_pct
        FROM employees e
        LEFT JOIN (
            SELECT employee_id, SUM(target_amount) AS total_target
            FROM targets GROUP BY employee_id
        ) t ON t.employee_id = e.employee_id
        LEFT JOIN (
            SELECT employee_id, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit,
                   COUNT(*) AS total_orders, COUNT(DISTINCT customer_id) AS customer_count
            FROM orders WHERE order_status <> 'Cancelled' GROUP BY employee_id
        ) o ON o.employee_id = e.employee_id
        ORDER BY target_achievement_pct DESC NULLS LAST
    """
    rows = [dict(r) for r in db.execute(text(sql)).mappings().all()]
    for r in rows:
        r["performance_tier"] = classify_performance(r["target_achievement_pct"])

    tier_counts = {}
    for r in rows:
        tier_counts[r["performance_tier"]] = tier_counts.get(r["performance_tier"], 0) + 1

    tier_order = ["Top Performer", "Strong Performer", "Average Performer", "Needs Improvement", "No Data"]
    performance_tier_summary = [
        {"performance_tier": tier, "count": tier_counts.get(tier, 0)}
        for tier in tier_order if tier_counts.get(tier, 0) > 0
    ]

    return {"employees": rows, "performance_tier_summary": performance_tier_summary}
