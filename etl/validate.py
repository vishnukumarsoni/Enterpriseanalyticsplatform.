"""
Data Validation
================
Runs automated data-quality checks across the raw dataset and produces
data/reports/data_quality_report.csv
"""
import pandas as pd
import numpy as np
import os
import logging

log = logging.getLogger("validate")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def _row(rule, total, failed):
    pct = round((failed / total) * 100, 4) if total else 0.0
    status = "PASS" if pct == 0 else ("WARN" if pct < 1 else "FAIL")
    return {"Rule": rule, "Total Records": total, "Failed Records": failed,
            "Failure Percentage": pct, "Status": status}


def validate(customers, products, employees, orders, returns, targets):
    results = []

    # Missing values
    for name, df in [("customers", customers), ("products", products),
                      ("employees", employees), ("orders", orders)]:
        missing = int(df.isnull().sum().sum())
        results.append(_row(f"Missing values in {name}", df.size, missing))

    # Duplicate records
    results.append(_row("Duplicate customer_id", len(customers), int(customers["customer_id"].duplicated().sum())))
    results.append(_row("Duplicate product_id", len(products), int(products["product_id"].duplicated().sum())))
    results.append(_row("Duplicate order_id", len(orders), int(orders["order_id"].duplicated().sum())))

    # Invalid dates
    order_dates = pd.to_datetime(orders["order_date"], errors="coerce")
    results.append(_row("Invalid order dates", len(orders), int(order_dates.isna().sum())))
    future_dates = (order_dates > pd.Timestamp.today()).sum()
    results.append(_row("Order dates in the future", len(orders), int(future_dates)))

    # Negative quantities / revenue
    results.append(_row("Negative or zero quantity", len(orders), int((orders["quantity"] <= 0).sum())))
    results.append(_row("Negative revenue", len(orders), int((orders["revenue"] < 0).sum())))
    results.append(_row("Negative cost", len(orders), int((orders["cost"] < 0).sum())))

    # Referential integrity
    valid_customers = set(customers["customer_id"])
    valid_products = set(products["product_id"])
    valid_employees = set(employees["employee_id"])
    results.append(_row("Invalid customer_id references", len(orders),
                         int((~orders["customer_id"].isin(valid_customers)).sum())))
    results.append(_row("Invalid product_id references", len(orders),
                         int((~orders["product_id"].isin(valid_products)).sum())))
    results.append(_row("Invalid employee_id references", len(orders),
                         int((~orders["employee_id"].isin(valid_employees)).sum())))

    # Outliers (revenue > 99.5th percentile treated as extreme, informational)
    p995 = orders["revenue"].quantile(0.995)
    results.append(_row("Extreme revenue outliers (>99.5th pct)", len(orders),
                         int((orders["revenue"] > p995).sum())))

    # Profit calculation correctness: profit should equal revenue - cost
    expected_profit = (orders["revenue"] - orders["cost"]).round(2)
    mismatch = (expected_profit != orders["profit"].round(2)).sum()
    results.append(_row("Incorrect profit calculation (profit != revenue - cost)", len(orders), int(mismatch)))

    # Discount range sanity
    results.append(_row("Discount outside [0,1] range", len(orders),
                         int(((orders["discount"] < 0) | (orders["discount"] > 1)).sum())))

    report = pd.DataFrame(results)
    report_path = os.path.join(REPORT_DIR, "data_quality_report.csv")
    report.to_csv(report_path, index=False)
    log.info(f"Data quality report written to {report_path}")

    n_fail = (report["Status"] == "FAIL").sum()
    n_warn = (report["Status"] == "WARN").sum()
    log.info(f"Validation summary: {n_fail} FAIL, {n_warn} WARN, "
             f"{len(report) - n_fail - n_warn} PASS out of {len(report)} rules")
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    customers = pd.read_csv(os.path.join(RAW_DIR, "customers.csv"))
    products = pd.read_csv(os.path.join(RAW_DIR, "products.csv"))
    employees = pd.read_csv(os.path.join(RAW_DIR, "employees.csv"))
    orders = pd.read_csv(os.path.join(RAW_DIR, "orders.csv"))
    returns = pd.read_csv(os.path.join(RAW_DIR, "returns.csv"))
    targets = pd.read_csv(os.path.join(RAW_DIR, "targets.csv"))
    validate(customers, products, employees, orders, returns, targets)
