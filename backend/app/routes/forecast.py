import os
import pandas as pd
from fastapi import APIRouter, HTTPException
import logging

log = logging.getLogger("routes.forecast")
router = APIRouter(prefix="/api/forecast", tags=["forecast"])

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "reports")


def _read_csv(filename):
    path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=503,
            detail=f"Forecast artifact '{filename}' not found. Run `python ml/forecasting.py` to generate it."
        )
    return pd.read_csv(path).to_dict(orient="records")


@router.get("")
def get_forecast():
    try:
        actual = _read_csv("actual_monthly_revenue.csv")
        forecast_30d = _read_csv("forecast_next_30_days.csv")
        forecast_3m = _read_csv("forecast_next_3_months.csv")
        forecast_6m = _read_csv("forecast_next_6_months.csv")
        backtest_metrics = _read_csv("forecast_backtest_metrics.csv")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to load forecast artifacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to load forecast data")

    return {
        "actual_monthly_revenue": actual,
        "forecast_next_30_days": forecast_30d,
        "forecast_next_3_months": forecast_3m,
        "forecast_next_6_months": forecast_6m,
        "backtest_error_metrics": backtest_metrics[0] if backtest_metrics else None,
    }
