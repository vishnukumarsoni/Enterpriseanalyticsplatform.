"""
RFM Analysis
============
Computes Recency, Frequency, Monetary scores and customer segments,
writes results to data/reports/rfm_segments.csv and back to Postgres.
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("rfm_analysis")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/enterprise_analytics",
)
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def segment_customer(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r >= 3 and f <= 3 and m >= 3:
        return "Potential Loyalists"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost Customers"
    return "Hibernating"


def run_rfm():
    engine = create_engine(DATABASE_URL)
    orders = pd.read_sql(
        "SELECT customer_id, order_date, revenue FROM orders WHERE order_status <> 'Cancelled'",
        engine,
    )
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    snapshot_date = orders["order_date"].max() + pd.Timedelta(days=1)

    rfm = orders.groupby("customer_id").agg(
        recency=("order_date", lambda x: (snapshot_date - x.max()).days),
        frequency=("order_date", "count"),
        monetary=("revenue", "sum"),
    ).reset_index()

    rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["segment"] = rfm.apply(segment_customer, axis=1)

    out_path = os.path.join(REPORT_DIR, "rfm_segments.csv")
    rfm.to_csv(out_path, index=False)
    log.info(f"RFM analysis complete. {len(rfm):,} customers scored. Saved to {out_path}")
    log.info("Segment distribution:\n" + rfm["segment"].value_counts().to_string())
    return rfm


if __name__ == "__main__":
    run_rfm()
