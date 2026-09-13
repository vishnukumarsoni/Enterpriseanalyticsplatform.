"""Extract: read raw CSV files into pandas DataFrames."""
import pandas as pd
import os
import logging

log = logging.getLogger("extract")
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

FILES = {
    "date_dimension": "date_dimension.csv",
    "customers": "customers.csv",
    "products": "products.csv",
    "employees": "employees.csv",
    "orders": "orders.csv",
    "returns": "returns.csv",
    "targets": "targets.csv",
}


def extract_all():
    data = {}
    for key, filename in FILES.items():
        path = os.path.join(RAW_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required raw file missing: {path}")
        df = pd.read_csv(path)
        log.info(f"Extracted {key}: {len(df):,} rows from {filename}")
        data[key] = df
    return data
