"""
Tests for the ETL pipeline: extraction, transformation, and data validation.
Run with: pytest tests/test_etl.py
"""
import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
from transform import transform_all  # noqa: E402
from validate import validate  # noqa: E402


@pytest.fixture
def raw_data():
    customers = pd.DataFrame([
        {"customer_id": "C1", "customer_name": " Alice ", "email": "A@X.com", "city": "Pune",
         "state": "MH", "region": "West", "customer_segment": "Consumer",
         "acquisition_date": "2024-01-01", "customer_status": "Active"},
        {"customer_id": "C1", "customer_name": "Alice", "email": "a@x.com", "city": "Pune",
         "state": "MH", "region": "West", "customer_segment": "Consumer",
         "acquisition_date": "2024-01-01", "customer_status": "Active"},  # duplicate
    ])
    products = pd.DataFrame([
        {"product_id": "P1", "product_name": "Widget", "category": "Electronics",
         "sub_category": "Accessories", "unit_cost": 10.0, "selling_price": 15.0,
         "supplier": "Acme", "product_status": "Active"},
    ])
    employees = pd.DataFrame([
        {"employee_id": "E1", "employee_name": "Bob", "department": "Sales",
         "region": "West", "joining_date": "2023-01-01", "target_amount": 100000},
    ])
    orders = pd.DataFrame([
        {"order_id": "O1", "order_date": "2024-02-01", "customer_id": "C1", "product_id": "P1",
         "employee_id": "E1", "quantity": 2, "unit_price": 15.0, "discount": 0.0,
         "revenue": 30.0, "cost": 20.0, "profit": 999.0,  # intentionally wrong profit
         "payment_method": "UPI", "order_status": "Completed"},
        {"order_id": "O2", "order_date": "2024-02-02", "customer_id": "C1", "product_id": "P1",
         "employee_id": "E1", "quantity": -1, "unit_price": 15.0, "discount": 0.0,  # invalid qty
         "revenue": -15.0, "cost": 10.0, "profit": -25.0,
         "payment_method": "Cash on Delivery", "order_status": "Completed"},
    ])
    returns = pd.DataFrame([
        {"return_id": "R1", "order_id": "O1", "return_date": "2024-02-10",
         "return_reason": "Defective Product", "refund_amount": 30.0},
    ])
    targets = pd.DataFrame([
        {"employee_id": "E1", "month": 2, "year": 2024, "target_amount": 8000},
    ])
    date_dimension = pd.DataFrame([
        {"date": "2024-02-01", "day": 1, "month": 2, "month_name": "February", "quarter": 1,
         "year": 2024, "week": 5, "weekday": "Thursday", "fiscal_year": 2024},
    ])
    return {
        "customers": customers, "products": products, "employees": employees,
        "orders": orders, "returns": returns, "targets": targets, "date_dimension": date_dimension,
    }


def test_transform_removes_duplicate_customers(raw_data):
    cleaned = transform_all(raw_data)
    assert len(cleaned["customers"]) == 1


def test_transform_removes_invalid_orders(raw_data):
    cleaned = transform_all(raw_data)
    # the negative-quantity order should be dropped
    assert len(cleaned["orders"]) == 1
    assert (cleaned["orders"]["quantity"] > 0).all()


def test_transform_recomputes_profit_correctly(raw_data):
    cleaned = transform_all(raw_data)
    row = cleaned["orders"].iloc[0]
    assert row["profit"] == round(row["revenue"] - row["cost"], 2)


def test_validate_flags_profit_mismatch_before_cleaning(raw_data):
    report = validate(
        raw_data["customers"].drop_duplicates(subset="customer_id"),
        raw_data["products"], raw_data["employees"],
        raw_data["orders"], raw_data["returns"], raw_data["targets"],
    )
    profit_rule = report[report["Rule"].str.contains("profit calculation")]
    assert profit_rule.iloc[0]["Failed Records"] >= 1


def test_validate_flags_negative_quantity(raw_data):
    report = validate(
        raw_data["customers"].drop_duplicates(subset="customer_id"),
        raw_data["products"], raw_data["employees"],
        raw_data["orders"], raw_data["returns"], raw_data["targets"],
    )
    qty_rule = report[report["Rule"].str.contains("Negative or zero quantity")]
    assert qty_rule.iloc[0]["Failed Records"] == 1


def test_validate_output_schema(raw_data):
    report = validate(
        raw_data["customers"].drop_duplicates(subset="customer_id"),
        raw_data["products"], raw_data["employees"],
        raw_data["orders"], raw_data["returns"], raw_data["targets"],
    )
    expected_cols = {"Rule", "Total Records", "Failed Records", "Failure Percentage", "Status"}
    assert expected_cols.issubset(set(report.columns))
