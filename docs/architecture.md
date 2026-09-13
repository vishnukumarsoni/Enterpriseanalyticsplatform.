# Architecture

## Overview

```
Raw CSV (Faker-generated)
        │
        ▼
  Data Validation  ──► data_quality_report.csv
        │
        ▼
  Python ETL (pandas)  ──► etl_execution.log
        │
        ▼
     PostgreSQL 16
    (7 tables, FKs, indexes)
        │
   ┌────┴─────┐
   ▼          ▼
SQL Views   Python/ML
(sql/*.sql) (rfm, churn, forecast)
   │          │
   └────┬─────┘
        ▼
   FastAPI Backend (11 endpoints)
        │
        ▼
  React + TypeScript Dashboard
  (Vite, Tailwind, Recharts)
```

## Components

- **Dataset generator** (`etl/generate_data.py`): produces a 3-year synthetic
  dataset (10,500 customers, 550 products, 120 employees, ~106k orders) with
  *persistent per-customer behavior* — each customer has a latent activity
  level and ~30% are modeled as genuine churners who stop purchasing before
  the end of the period. This is what makes the churn model and RFM
  segmentation meaningful rather than trivially random.
- **ETL pipeline** (`etl/etl_pipeline.py`): extract → transform → validate →
  load, in one runnable script. Aborts the load if any validation rule FAILs.
- **Database** (`sql/schema.sql`): PostgreSQL with declared primary keys,
  foreign keys, check constraints, and indexes on all commonly filtered
  columns.
- **SQL analytics** (`sql/views.sql`, `sql/business_queries.sql`): 8
  reusable views plus 32 standalone analytical queries covering window
  functions, CTEs, ranking, running totals, and growth calculations.
- **ML** (`ml/`):
  - `rfm_analysis.py` — Recency/Frequency/Monetary scoring and 8-segment
    classification.
  - `churn_model.py` — trains Logistic Regression, Random Forest, and
    Gradient Boosting on a **time-split** feature set (features computed from
    an observation window, label computed from a strictly later holdout
    window) to avoid label leakage, selects the best model by ROC-AUC, and
    writes probability + risk-tier predictions back to Postgres.
  - `forecasting.py` — Holt-Winters exponential smoothing for daily/monthly
    revenue, with backtested MAE/RMSE/MAPE reported honestly rather than
    invented confidence numbers.
- **API** (`backend/`): FastAPI, SQLAlchemy, Pydantic filters, CORS,
  structured logging, global exception handlers, Swagger docs at `/docs`.
- **Frontend** (`frontend/`): React 19 + TypeScript + Vite + Tailwind v4 +
  Recharts. All values are fetched from the API; nothing is hard-coded.

## Data flow guarantee

Every number the dashboard displays traces back to a live SQL query against
Postgres — there is no mock data layer in the production code path.
