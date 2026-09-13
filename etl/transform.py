"""Transform: clean, dedupe, fix types, and enrich the raw dataframes."""
import pandas as pd
import numpy as np
import logging

log = logging.getLogger("transform")


def transform_all(data: dict) -> dict:
    customers = data["customers"].copy()
    products = data["products"].copy()
    employees = data["employees"].copy()
    orders = data["orders"].copy()
    returns = data["returns"].copy()
    targets = data["targets"].copy()
    date_dimension = data["date_dimension"].copy()

    # ---- customers ----
    before = len(customers)
    customers = customers.drop_duplicates(subset="customer_id")
    customers["acquisition_date"] = pd.to_datetime(customers["acquisition_date"]).dt.date
    customers["customer_name"] = customers["customer_name"].str.strip()
    customers["email"] = customers["email"].str.lower().str.strip()
    log.info(f"customers: removed {before - len(customers)} duplicates")

    # ---- products ----
    before = len(products)
    products = products.drop_duplicates(subset="product_id")
    products["unit_cost"] = products["unit_cost"].astype(float).round(2)
    products["selling_price"] = products["selling_price"].astype(float).round(2)
    log.info(f"products: removed {before - len(products)} duplicates")

    # ---- employees ----
    employees = employees.drop_duplicates(subset="employee_id")
    employees["joining_date"] = pd.to_datetime(employees["joining_date"]).dt.date

    # ---- orders ----
    before = len(orders)
    orders = orders.drop_duplicates(subset="order_id")
    orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.date

    # drop rows with invalid FKs (defensive; generator already guarantees validity)
    orders = orders[orders["customer_id"].isin(customers["customer_id"])]
    orders = orders[orders["product_id"].isin(products["product_id"])]
    orders = orders[orders["employee_id"].isin(employees["employee_id"])]

    # enforce business rule: quantity > 0, non-negative revenue/cost
    orders = orders[(orders["quantity"] > 0) & (orders["revenue"] >= 0) & (orders["cost"] >= 0)]

    # recompute profit to guarantee correctness (revenue - cost)
    orders["profit"] = (orders["revenue"] - orders["cost"]).round(2)
    log.info(f"orders: removed {before - len(orders)} invalid/duplicate rows")

    # ---- returns ----
    returns = returns.drop_duplicates(subset="return_id")
    returns = returns[returns["order_id"].isin(orders["order_id"])]
    returns["return_date"] = pd.to_datetime(returns["return_date"]).dt.date

    # ---- targets ----
    targets = targets.drop_duplicates(subset=["employee_id", "month", "year"])
    targets = targets[targets["employee_id"].isin(employees["employee_id"])]

    # ---- date_dimension ----
    date_dimension["date"] = pd.to_datetime(date_dimension["date"]).dt.date

    return {
        "date_dimension": date_dimension,
        "customers": customers,
        "products": products,
        "employees": employees,
        "orders": orders,
        "returns": returns,
        "targets": targets,
    }
