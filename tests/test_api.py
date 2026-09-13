"""
Integration tests for the FastAPI backend.
Requires the Postgres database to be populated (run etl_pipeline.py first)
and the `backend` directory to be importable.

Run with: pytest tests/test_api.py
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert "status" in resp.json()


@pytest.mark.parametrize("endpoint", [
    "/api/dashboard", "/api/sales", "/api/customers", "/api/products",
    "/api/regions", "/api/employees", "/api/churn", "/api/rfm",
    "/api/forecast", "/api/insights", "/api/data-quality",
])
def test_endpoint_returns_200(endpoint):
    resp = client.get(endpoint)
    assert resp.status_code == 200
    assert resp.json() is not None


def test_dashboard_kpis_present():
    resp = client.get("/api/dashboard")
    body = resp.json()
    assert "kpis" in body
    for key in ["total_revenue", "total_profit", "profit_margin_pct", "total_orders"]:
        assert key in body["kpis"]


def test_dashboard_region_filter_narrows_results():
    all_resp = client.get("/api/dashboard").json()
    filtered_resp = client.get("/api/dashboard", params={"region": "North"}).json()
    assert filtered_resp["kpis"]["total_revenue"] <= all_resp["kpis"]["total_revenue"]


def test_invalid_date_range_returns_422():
    resp = client.get("/api/dashboard", params={"date_from": "2025-01-01", "date_to": "2024-01-01"})
    assert resp.status_code == 422


def test_customers_pagination():
    resp = client.get("/api/customers", params={"page": 1, "page_size": 5})
    body = resp.json()
    assert len(body["customers"]) <= 5
    assert body["pagination"]["page"] == 1


def test_employees_summary_is_array():
    resp = client.get("/api/employees")
    body = resp.json()
    assert isinstance(body["performance_tier_summary"], list)
    assert all(
        isinstance(item, dict) and "performance_tier" in item and "count" in item
        for item in body["performance_tier_summary"]
    )


def test_churn_risk_levels_valid():
    resp = client.get("/api/churn").json()
    valid = {"Low", "Medium", "High"}
    for row in resp["risk_summary"]:
        assert row["risk_level"] in valid


def test_insights_are_generated_not_hardcoded():
    resp = client.get("/api/insights").json()
    assert "insights" in resp
    assert isinstance(resp["insights"], list)
    assert resp.get("generated_from") == "live database aggregation (not hard-coded)"
