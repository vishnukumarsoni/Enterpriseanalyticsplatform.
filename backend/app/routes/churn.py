from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/churn", tags=["churn"])


@router.get("")
def get_churn(
    risk_level: str | None = Query(None, description="Filter by Low/Medium/High"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    summary_sql = """
        SELECT risk_level, COUNT(*) AS count, ROUND(AVG(churn_probability), 4) AS avg_probability
        FROM customer_churn_predictions GROUP BY risk_level
    """
    risk_summary = [dict(r) for r in db.execute(text(summary_sql)).mappings().all()]

    overall_sql = "SELECT ROUND(AVG(churn_probability), 4) AS avg_churn_probability FROM customer_churn_predictions"
    overall = dict(db.execute(text(overall_sql)).mappings().first())

    where = "1=1"
    params = {}
    if risk_level:
        where = "cp.risk_level = :risk_level"
        params["risk_level"] = risk_level

    offset = (page - 1) * page_size
    params.update({"limit": page_size, "offset": offset})

    count_sql = f"SELECT COUNT(*) FROM customer_churn_predictions cp WHERE {where}"
    total_rows = db.execute(text(count_sql), params).scalar()

    table_sql = f"""
        SELECT cp.customer_id, c.customer_name, c.region,
               COALESCE(orev.revenue, 0) AS revenue,
               COALESCE(orev.orders, 0) AS orders,
               orev.last_purchase,
               rfm.segment AS rfm_segment,
               cp.churn_probability, cp.risk_level
        FROM customer_churn_predictions cp
        JOIN customers c ON c.customer_id = cp.customer_id
        LEFT JOIN (
            SELECT customer_id, SUM(revenue) AS revenue, COUNT(*) AS orders, MAX(order_date) AS last_purchase
            FROM orders WHERE order_status <> 'Cancelled' GROUP BY customer_id
        ) orev ON orev.customer_id = cp.customer_id
        LEFT JOIN vw_rfm_segments rfm ON rfm.customer_id = cp.customer_id
        WHERE {where}
        ORDER BY cp.churn_probability DESC
        LIMIT :limit OFFSET :offset
    """
    at_risk_customers = [dict(r) for r in db.execute(text(table_sql), params).mappings().all()]

    return {
        "risk_summary": risk_summary,
        "overall": overall,
        "at_risk_customers": at_risk_customers,
        "pagination": {"page": page, "page_size": page_size, "total_rows": total_rows},
    }
