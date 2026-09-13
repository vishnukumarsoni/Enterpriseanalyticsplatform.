import os
import pandas as pd
from fastapi import APIRouter, HTTPException
import logging

log = logging.getLogger("routes.data_quality")
router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "reports")


@router.get("")
def get_data_quality():
    path = os.path.join(REPORT_DIR, "data_quality_report.csv")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=503,
            detail="Data quality report not found. Run the ETL pipeline (python etl/etl_pipeline.py) first."
        )
    try:
        df = pd.read_csv(path)
    except Exception as e:
        log.error(f"Failed to read data quality report: {e}")
        raise HTTPException(status_code=500, detail="Failed to read data quality report")

    rules = df.to_dict(orient="records")
    summary = {
        "total_rules": len(df),
        "passed": int((df["Status"] == "PASS").sum()),
        "warnings": int((df["Status"] == "WARN").sum()),
        "failed": int((df["Status"] == "FAIL").sum()),
    }
    return {"summary": summary, "rules": rules}
