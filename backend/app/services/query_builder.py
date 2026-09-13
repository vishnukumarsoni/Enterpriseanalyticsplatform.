"""Builds parameterized WHERE clauses from AnalyticsFilters for use across endpoints."""
from app.schemas.filters import AnalyticsFilters


def build_order_filters(filters: AnalyticsFilters, alias_orders="o", alias_customers="c", alias_products="p", alias_employees="e"):
    clauses = [f"{alias_orders}.order_status <> 'Cancelled'"]
    params = {}

    if filters.date_from:
        clauses.append(f"{alias_orders}.order_date >= :date_from")
        params["date_from"] = filters.date_from
    if filters.date_to:
        clauses.append(f"{alias_orders}.order_date <= :date_to")
        params["date_to"] = filters.date_to
    if filters.region:
        clauses.append(f"{alias_customers}.region = :region")
        params["region"] = filters.region
    if filters.category:
        clauses.append(f"{alias_products}.category = :category")
        params["category"] = filters.category
    if filters.customer_segment:
        clauses.append(f"{alias_customers}.customer_segment = :customer_segment")
        params["customer_segment"] = filters.customer_segment
    if filters.salesperson:
        clauses.append(f"{alias_employees}.employee_name = :salesperson")
        params["salesperson"] = filters.salesperson

    where_sql = " AND ".join(clauses)
    return where_sql, params
