"""
Revenue Forecasting
====================
Forecasts daily/monthly revenue using Holt-Winters exponential smoothing
(triple exponential smoothing with trend + seasonality), producing:
    - Next 30 days (daily forecast)
    - Next 3 months / 6 months (monthly forecast)
Also reports backtesting error metrics (MAE, RMSE, MAPE) on a held-out tail
of history so the forecast's reliability is honestly represented.
"""
import os
import logging
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from statsmodels.tsa.holtwinters import ExponentialSmoothing

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("forecasting")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/enterprise_analytics",
)
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def load_daily_revenue(engine):
    df = pd.read_sql("""
        SELECT order_date, SUM(revenue) AS revenue
        FROM orders WHERE order_status <> 'Cancelled'
        GROUP BY order_date ORDER BY order_date
    """, engine)
    df["order_date"] = pd.to_datetime(df["order_date"])
    full_range = pd.date_range(df["order_date"].min(), df["order_date"].max(), freq="D")
    daily = df.set_index("order_date").reindex(full_range).fillna(0)
    daily.index.name = "date"
    return daily["revenue"]


def backtest(series, horizon=30, seasonal_periods=7):
    train = series.iloc[:-horizon]
    test = series.iloc[-horizon:]
    model = ExponentialSmoothing(
        train, trend="add", seasonal="add", seasonal_periods=seasonal_periods,
        initialization_method="estimated"
    ).fit()
    preds = model.forecast(horizon)
    mae = float(np.mean(np.abs(test.values - preds.values)))
    rmse = float(np.sqrt(np.mean((test.values - preds.values) ** 2)))
    denom = np.where(test.values == 0, np.nan, test.values)
    mape = float(np.nanmean(np.abs((test.values - preds.values) / denom)) * 100)
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE_pct": round(mape, 2)}


def forecast_daily(series, days=30, seasonal_periods=7):
    model = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=seasonal_periods,
        initialization_method="estimated"
    ).fit()
    forecast = model.forecast(days)
    resid_std = np.std(model.resid)
    lower = forecast - 1.96 * resid_std
    upper = forecast + 1.96 * resid_std
    out = pd.DataFrame({
        "date": forecast.index.strftime("%Y-%m-%d"),
        "forecast_revenue": forecast.values.round(2),
        "lower_bound": np.clip(lower.values, 0, None).round(2),
        "upper_bound": upper.values.round(2),
    })
    return out


def forecast_monthly(series, months=6):
    monthly = series.resample("MS").sum()
    model = ExponentialSmoothing(
        monthly, trend="add", seasonal="add", seasonal_periods=12 if len(monthly) >= 24 else None,
        initialization_method="estimated"
    ).fit()
    forecast = model.forecast(months)
    resid_std = np.std(model.resid)
    lower = forecast - 1.96 * resid_std
    upper = forecast + 1.96 * resid_std
    out = pd.DataFrame({
        "month": forecast.index.strftime("%Y-%m"),
        "forecast_revenue": forecast.values.round(2),
        "lower_bound": np.clip(lower.values, 0, None).round(2),
        "upper_bound": upper.values.round(2),
    })
    return out, monthly


def main():
    engine = create_engine(DATABASE_URL)
    log.info("Loading daily revenue history ...")
    series = load_daily_revenue(engine)
    log.info(f"History: {series.index.min().date()} to {series.index.max().date()} ({len(series)} days)")

    log.info("Backtesting 30-day-ahead forecast accuracy ...")
    metrics = backtest(series, horizon=30)
    log.info(f"Backtest error metrics: {metrics}")
    pd.DataFrame([metrics]).to_csv(os.path.join(REPORT_DIR, "forecast_backtest_metrics.csv"), index=False)

    log.info("Forecasting next 30 days (daily) ...")
    daily_forecast = forecast_daily(series, days=30)
    daily_forecast.to_csv(os.path.join(REPORT_DIR, "forecast_next_30_days.csv"), index=False)

    log.info("Forecasting next 3 and 6 months ...")
    monthly_forecast_6, monthly_hist = forecast_monthly(series, months=6)
    monthly_forecast_3 = monthly_forecast_6.head(3)
    monthly_forecast_3.to_csv(os.path.join(REPORT_DIR, "forecast_next_3_months.csv"), index=False)
    monthly_forecast_6.to_csv(os.path.join(REPORT_DIR, "forecast_next_6_months.csv"), index=False)

    actual_monthly = pd.DataFrame({
        "month": monthly_hist.index.strftime("%Y-%m"),
        "actual_revenue": monthly_hist.values.round(2)
    })
    actual_monthly.to_csv(os.path.join(REPORT_DIR, "actual_monthly_revenue.csv"), index=False)

    log.info("Forecasting complete. Reports written to data/reports/")
    log.info(f"Next 3 months forecast:\n{monthly_forecast_3.to_string(index=False)}")


if __name__ == "__main__":
    main()
