from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.filters import AnalyticsFilters
from app.services.query_builder import build_order_filters

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def get_customers(
    filters: AnalyticsFilters = Depends(),
    search: str | None = Query(None, description="Search by customer name or ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    where_sql, params = build_order_filters(filters)

    summary_sql = """
        SELECT
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (SELECT COUNT(*) FROM customers WHERE customer_status='Active') AS active_customers,
            (SELECT COUNT(DISTINCT customer_id) FROM orders WHERE order_status <> 'Cancelled') AS purchasing_customers
    """
    summary = dict(db.execute(text(summary_sql)).mappings().first())

    new_returning_sql = """
        WITH order_seq AS (
            SELECT customer_id, order_id,
                   ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS seq
            FROM orders WHERE order_status <> 'Cancelled'
        )
        SELECT
            COUNT(*) FILTER (WHERE seq = 1) AS new_customer_orders,
            COUNT(*) FILTER (WHERE seq > 1) AS returning_customer_orders
        FROM order_seq
    """
    new_returning = dict(db.execute(text(new_returning_sql)).mappings().first())
    summary.update(new_returning)

    growth_sql = """
        SELECT DATE_TRUNC('month', acquisition_date)::date AS month, COUNT(*) AS new_customers
        FROM customers GROUP BY 1 ORDER BY 1
    """
    customer_growth = [dict(r) for r in db.execute(text(growth_sql)).mappings().all()]

    rfm_sql = "SELECT segment, COUNT(*) AS count FROM vw_rfm_segments GROUP BY segment"
    rfm_segments = [dict(r) for r in db.execute(text(rfm_sql)).mappings().all()]

    # Searchable, paginated table
    table_where = ["1=1"]
    table_params = {}
    if search:
        table_where.append("(c.customer_name ILIKE :search OR c.customer_id ILIKE :search)")
        table_params["search"] = f"%{search}%"
    if filters.region:
        table_where.append("c.region = :region")
        table_params["region"] = filters.region
    if filters.customer_segment:
        table_where.append("c.customer_segment = :customer_segment")
        table_params["customer_segment"] = filters.customer_segment

    table_where_sql = " AND ".join(table_where)
    offset = (page - 1) * page_size
    table_params.update({"limit": page_size, "offset": offset})

    count_sql = f"SELECT COUNT(*) FROM customers c WHERE {table_where_sql}"
    total_rows = db.execute(text(count_sql), table_params).scalar()

    table_sql = f"""
        SELECT c.customer_id, c.customer_name, c.region, c.customer_segment, c.customer_status,
               COALESCE(SUM(o.revenue), 0) AS total_revenue,
               COUNT(o.order_id) AS total_orders,
               MAX(o.order_date) AS last_purchase_date
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status <> 'Cancelled'
        WHERE {table_where_sql}
        GROUP BY c.customer_id, c.customer_name, c.region, c.customer_segment, c.customer_status
        ORDER BY total_revenue DESC
        LIMIT :limit OFFSET :offset
    """
    customers_table = [dict(r) for r in db.execute(text(table_sql), table_params).mappings().all()]

    return {
        "summary": summary,
        "customer_growth": customer_growth,
        "rfm_segments": rfm_segments,
        "customers": customers_table,
        "pagination": {"page": page, "page_size": page_size, "total_rows": total_rows},
    }
