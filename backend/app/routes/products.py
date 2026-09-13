from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.filters import AnalyticsFilters
from app.services.query_builder import build_order_filters

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_products(filters: AnalyticsFilters = Depends(), db: Session = Depends(get_db)):
    where_sql, params = build_order_filters(filters)

    perf_sql = f"""
        SELECT p.product_id, p.product_name, p.category, p.sub_category,
               SUM(o.revenue) AS revenue, SUM(o.profit) AS profit,
               ROUND(SUM(o.profit) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS margin_pct,
               SUM(o.quantity) AS units_sold
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql}
        GROUP BY p.product_id, p.product_name, p.category, p.sub_category
    """
    all_products = [dict(r) for r in db.execute(text(perf_sql), params).mappings().all()]
    sorted_by_rev = sorted(all_products, key=lambda x: x["revenue"] or 0, reverse=True)
    top_10 = sorted_by_rev[:10]
    bottom_10 = sorted_by_rev[-10:]
    sorted_by_margin = sorted(all_products, key=lambda x: x["margin_pct"] or 0, reverse=True)
    highest_margin = sorted_by_margin[:10]
    lowest_margin = sorted_by_margin[-10:]

    category_sql = f"""
        SELECT p.category, SUM(o.revenue) AS revenue, SUM(o.profit) AS profit
        FROM orders o JOIN customers c ON c.customer_id=o.customer_id
        JOIN products p ON p.product_id=o.product_id
        JOIN employees e ON e.employee_id=o.employee_id
        WHERE {where_sql} GROUP BY p.category ORDER BY revenue DESC
    """
    category_performance = [dict(r) for r in db.execute(text(category_sql), params).mappings().all()]

    returns_sql = """
        SELECT p.product_id, p.product_name,
               COUNT(o.order_id) AS total_orders, COUNT(r.return_id) AS total_returns,
               ROUND(COUNT(r.return_id)::numeric / NULLIF(COUNT(o.order_id), 0) * 100, 2) AS return_rate_pct
        FROM products p JOIN orders o ON o.product_id = p.product_id
        LEFT JOIN returns r ON r.order_id = o.order_id
        GROUP BY p.product_id, p.product_name
        ORDER BY return_rate_pct DESC LIMIT 10
    """
    most_returned = [dict(r) for r in db.execute(text(returns_sql)).mappings().all()]

    return {
        "top_10_products": top_10,
        "bottom_10_products": bottom_10,
        "highest_margin_products": highest_margin,
        "lowest_margin_products": lowest_margin,
        "category_performance": category_performance,
        "most_returned_products": most_returned,
        "all_products": all_products,
    }
