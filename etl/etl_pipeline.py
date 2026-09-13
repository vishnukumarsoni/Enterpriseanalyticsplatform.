"""
Master ETL Pipeline
====================
RAW DATA -> EXTRACT -> TRANSFORM -> VALIDATE -> LOAD -> POSTGRESQL

Run:
    python etl_pipeline.py
"""
import os
import sys
import logging
import time

sys.path.insert(0, os.path.dirname(__file__))
from extract import extract_all
from transform import transform_all
from validate import validate
from load import get_engine, apply_schema, load_all

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "etl_execution.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("etl_pipeline")

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
VIEWS_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "views.sql")


def main():
    start = time.time()
    log.info("=" * 60)
    log.info("ETL PIPELINE STARTED")
    log.info("=" * 60)

    log.info("STEP 1/5: EXTRACT")
    raw = extract_all()

    log.info("STEP 2/5: TRANSFORM")
    clean = transform_all(raw)

    log.info("STEP 3/5: VALIDATE")
    report = validate(clean["customers"], clean["products"], clean["employees"],
                       clean["orders"], clean["returns"], clean["targets"])
    n_fail = (report["Status"] == "FAIL").sum()
    if n_fail > 0:
        log.error(f"Validation found {n_fail} FAILING rules. Aborting load.")
        sys.exit(1)

    log.info("STEP 4/5: APPLY SCHEMA")
    engine = get_engine()
    apply_schema(engine, SCHEMA_PATH)

    log.info("STEP 5/5: LOAD")
    load_all(clean, engine)

    log.info("STEP 6/6: APPLY ANALYTICAL VIEWS")
    apply_schema(engine, VIEWS_PATH)

    elapsed = time.time() - start
    log.info("=" * 60)
    log.info(f"ETL PIPELINE COMPLETED SUCCESSFULLY in {elapsed:.1f}s")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
