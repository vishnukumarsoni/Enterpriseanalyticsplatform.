from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/rfm", tags=["rfm"])


@router.get("")
def get_rfm(
    segment: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    summary_sql = """
        SELECT segment, COUNT(*) AS count, ROUND(AVG(monetary), 2) AS avg_monetary,
               ROUND(AVG(frequency), 2) AS avg_frequency, ROUND(AVG(recency_days), 1) AS avg_recency_days
        FROM vw_rfm_segments GROUP BY segment ORDER BY count DESC
    """
    segment_summary = [dict(r) for r in db.execute(text(summary_sql)).mappings().all()]

    where = "1=1"
    params = {}
    if segment:
        where = "segment = :segment"
        params["segment"] = segment

    offset = (page - 1) * page_size
    params.update({"limit": page_size, "offset": offset})

    count_sql = f"SELECT COUNT(*) FROM vw_rfm_segments WHERE {where}"
    total_rows = db.execute(text(count_sql), params).scalar()

    table_sql = f"""
        SELECT customer_id, customer_name, recency_days, frequency, monetary,
               r_score, f_score, m_score, rfm_score, segment
        FROM vw_rfm_segments WHERE {where}
        ORDER BY rfm_score DESC
        LIMIT :limit OFFSET :offset
    """
    customers = [dict(r) for r in db.execute(text(table_sql), params).mappings().all()]

    return {
        "segment_summary": segment_summary,
        "customers": customers,
        "pagination": {"page": page, "page_size": page_size, "total_rows": total_rows},
    }
