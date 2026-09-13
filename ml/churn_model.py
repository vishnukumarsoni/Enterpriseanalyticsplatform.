"""
Customer Churn Prediction
==========================
Builds features per customer, trains and compares Logistic Regression,
Random Forest and Gradient Boosting classifiers, selects the best model
by ROC-AUC, and writes predictions to:
    data/reports/customer_churn_predictions.csv
and the customer_churn_predictions table in PostgreSQL.

Churn definition: a customer is labeled "churned" if their most recent
order was more than 120 days before the dataset's max order date AND
they have not been acquired too recently to have had a fair chance to
re-purchase (label leakage guard).
"""
import os
import logging
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, confusion_matrix)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("churn_model")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/enterprise_analytics",
)
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

CHURN_WINDOW_DAYS = 120


def _load_orders_and_returns(engine):
    orders = pd.read_sql("""
        SELECT o.customer_id, o.order_id, o.order_date, o.revenue, o.discount, o.order_status,
               c.acquisition_date
        FROM orders o JOIN customers c ON c.customer_id = o.customer_id
    """, engine)
    returns = pd.read_sql("SELECT order_id, return_id FROM returns", engine)
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["acquisition_date"] = pd.to_datetime(orders["acquisition_date"])
    return orders, returns


def _features_as_of(completed, returns, cutoff_date):
    """Aggregate behavioral features using only orders on/before cutoff_date."""
    obs = completed[completed["order_date"] <= cutoff_date].copy()
    obs_returns = returns.merge(obs[["order_id"]], on="order_id", how="inner")
    return_counts = obs_returns.groupby(
        obs.set_index("order_id").loc[obs_returns["order_id"], "customer_id"].values
    ).size().rename("return_count") if len(obs_returns) else pd.Series(dtype=float, name="return_count")

    agg = obs.groupby("customer_id").agg(
        last_purchase=("order_date", "max"),
        first_purchase=("order_date", "min"),
        frequency=("order_date", "count"),
        total_spend=("revenue", "sum"),
        avg_order_value=("revenue", "mean"),
        avg_discount=("discount", "mean"),
    ).reset_index()

    agg["days_since_last_purchase"] = (cutoff_date - agg["last_purchase"]).dt.days
    agg["customer_tenure_days_at_cutoff"] = (cutoff_date - agg["first_purchase"]).dt.days
    agg = agg.merge(return_counts.rename_axis("customer_id").reset_index(), on="customer_id", how="left")
    agg["return_count"] = agg["return_count"].fillna(0)
    agg["return_rate"] = agg["return_count"] / agg["frequency"].replace(0, 1)
    return agg


def build_training_features(orders, returns):
    """
    Time-split feature construction to avoid label leakage.

    - Observation window: all orders up to cutoff_date (= max_date - CHURN_WINDOW_DAYS).
      Behavioral features (frequency, spend, discount use, returns, tenure) come only
      from this window.
    - Label window: strictly after cutoff_date, up to max_date. A customer is labeled
      churned (1) if they made ZERO purchases in this holdout window despite having
      purchase history before it.

    The model therefore has to predict future inactivity from past behavior alone —
    it never sees the quantity used to build the label.
    """
    completed = orders[orders["order_status"] != "Cancelled"].copy()
    max_date = completed["order_date"].max()
    cutoff_date = max_date - pd.Timedelta(days=CHURN_WINDOW_DAYS)

    agg = _features_as_of(completed, returns, cutoff_date)

    holdout = completed[completed["order_date"] > cutoff_date]
    purchased_in_holdout = set(holdout["customer_id"].unique())
    agg["is_churned"] = (~agg["customer_id"].isin(purchased_in_holdout)).astype(int)

    features = agg[[
        "customer_id", "frequency", "total_spend", "avg_order_value", "avg_discount",
        "return_rate", "customer_tenure_days_at_cutoff", "is_churned"
    ]].fillna(0)
    return features


def build_scoring_features(orders, returns):
    """Current-state features (observation window = entire history to date) used to
    score every customer's churn risk today. No label is available/needed here."""
    completed = orders[orders["order_status"] != "Cancelled"].copy()
    max_date = completed["order_date"].max()
    agg = _features_as_of(completed, returns, max_date)
    features = agg[[
        "customer_id", "frequency", "total_spend", "avg_order_value", "avg_discount",
        "return_rate", "customer_tenure_days_at_cutoff", "days_since_last_purchase"
    ]].fillna(0)
    return features


def train_and_select_model(features: pd.DataFrame):
    feature_cols = ["frequency", "total_spend", "avg_order_value", "avg_discount",
                     "return_rate", "customer_tenure_days_at_cutoff"]
    X = features[feature_cols]
    y = features["is_churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=42),
    }

    results = []
    fitted = {}
    for name, model in models.items():
        if name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)
            proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "model": name,
            "accuracy": accuracy_score(y_test, preds),
            "precision": precision_score(y_test, preds, zero_division=0),
            "recall": recall_score(y_test, preds, zero_division=0),
            "f1_score": f1_score(y_test, preds, zero_division=0),
            "roc_auc": roc_auc_score(y_test, proba),
        }
        cm = confusion_matrix(y_test, preds)
        metrics["confusion_matrix"] = cm.tolist()
        results.append(metrics)
        fitted[name] = model
        log.info(f"{name}: accuracy={metrics['accuracy']:.3f} precision={metrics['precision']:.3f} "
                 f"recall={metrics['recall']:.3f} f1={metrics['f1_score']:.3f} roc_auc={metrics['roc_auc']:.3f}")
        log.info(f"  Confusion matrix: {cm.tolist()}")

    results_df = pd.DataFrame(results)
    best_row = results_df.loc[results_df["roc_auc"].idxmax()]
    best_name = best_row["model"]
    log.info(f"Best model selected: {best_name} (ROC-AUC={best_row['roc_auc']:.3f})")

    results_df.drop(columns=["confusion_matrix"]).to_csv(
        os.path.join(REPORT_DIR, "churn_model_comparison.csv"), index=False
    )

    return fitted[best_name], best_name, scaler if best_name == "Logistic Regression" else None, feature_cols


def score_all_customers(features, model, model_name, scaler, feature_cols):
    X_all = features[feature_cols]
    if model_name == "Logistic Regression":
        X_all_input = scaler.transform(X_all)
    else:
        X_all_input = X_all

    proba = model.predict_proba(X_all_input)[:, 1]
    pred = (proba >= 0.5).astype(int)

    out = features[["customer_id"]].copy()
    out["churn_probability"] = proba.round(5)
    out["churn_prediction"] = pred
    out["risk_level"] = pd.cut(out["churn_probability"], bins=[-0.01, 0.33, 0.66, 1.01],
                                labels=["Low", "Medium", "High"])
    return out


def write_to_db(predictions, engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE customer_churn_predictions"))
    predictions.to_sql("customer_churn_predictions", engine, if_exists="append", index=False)
    log.info(f"Wrote {len(predictions):,} churn predictions to customer_churn_predictions table")


def main():
    engine = create_engine(DATABASE_URL)
    log.info("Loading orders and returns from PostgreSQL ...")
    orders, returns = _load_orders_and_returns(engine)

    log.info(f"Building TRAINING features with a {CHURN_WINDOW_DAYS}-day held-out label window "
              "(no label leakage: label window is excluded from feature computation) ...")
    train_features = build_training_features(orders, returns)
    log.info(f"Training set built for {len(train_features):,} customers. "
             f"Churn rate: {train_features['is_churned'].mean():.2%}")

    model, model_name, scaler, feature_cols = train_and_select_model(train_features)

    log.info("Building CURRENT scoring features (full history to date) ...")
    score_features = build_scoring_features(orders, returns)
    predictions = score_all_customers(score_features, model, model_name, scaler, feature_cols)

    out_path = os.path.join(REPORT_DIR, "customer_churn_predictions.csv")
    predictions.to_csv(out_path, index=False)
    log.info(f"Predictions saved to {out_path}")
    log.info("Risk level distribution:\n" + predictions["risk_level"].value_counts().to_string())

    write_to_db(predictions, engine)


if __name__ == "__main__":
    main()
