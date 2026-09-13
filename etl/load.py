"""Load: write cleaned dataframes into PostgreSQL using SQLAlchemy."""
import os
import logging
from sqlalchemy import create_engine, text

log = logging.getLogger("load")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/enterprise_analytics",
)

TABLE_ORDER = ["date_dimension", "customers", "products", "employees", "orders", "returns", "targets"]


def get_engine():
    return create_engine(DATABASE_URL)


def apply_schema(engine, schema_path):
    with open(schema_path) as f:
        schema_sql = f.read()
    with engine.begin() as conn:
        for statement in schema_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
    log.info("Schema applied.")


def load_all(data: dict, engine):
    with engine.begin() as conn:
        # respect FK order: truncate children first
        for table in reversed(TABLE_ORDER):
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))

    for table in TABLE_ORDER:
        df = data[table]
        df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=5000)
        log.info(f"Loaded {len(df):,} rows into {table}")
