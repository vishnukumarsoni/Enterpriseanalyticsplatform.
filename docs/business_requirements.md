# Business Requirements Document

## Stakeholders
- Executive leadership (CEO, CFO, VP Sales) — revenue, profit, growth visibility
- Sales managers — salesperson performance and target tracking
- Marketing / Customer Success — churn risk, RFM segments, retention
- Merchandising / Category managers — product profitability and returns
- Regional managers — cross-region comparison
- Data/BI team — pipeline reliability, data quality, self-service reporting

## Business Problem
Company management currently lacks a unified, trustworthy view of sales,
customer, and product performance across regions. Decisions on discounting,
staffing, and inventory are made without consistent, validated data or
forward-looking forecasts.

## Objectives
1. Provide a single source of truth for revenue, profit, and margin.
2. Surface customer churn risk before it materializes in lost revenue.
3. Identify high- and low-performing products, regions, and salespeople.
4. Forecast near-term revenue with honest uncertainty bounds.
5. Automate data-quality checks so bad data is caught before it reaches
   dashboards.

## Key Performance Indicators
See `docs/architecture.md` and `sql/kpi_queries.sql` for the full list;
core KPIs are Total Revenue, Total Profit, Profit Margin %, YoY/MoM Growth,
Customer Retention/Churn Rate, Customer Lifetime Value, Target Achievement %,
and Category/Product Profitability.

## Functional Requirements
- FR1: System must ingest raw CSV data, validate it, and load it into a
  relational database with referential integrity enforced.
- FR2: System must expose KPIs via a documented REST API supporting
  filtering by date range, region, category, customer segment, and
  salesperson.
- FR3: System must classify customers by churn risk using a supervised ML
  model trained on historical behavior, and expose predictions via the API.
- FR4: System must segment customers using RFM analysis into named,
  actionable segments.
- FR5: System must forecast revenue for 30 days, 3 months, and 6 months,
  with reported error metrics.
- FR6: System must provide a web dashboard with at least: an executive
  overview, sales, customer, product, regional, employee, forecast, churn,
  RFM, and data-quality views.
- FR7: Users must be able to export underlying tables as CSV.

## Non-Functional Requirements
- NFR1: All API responses must be computed from live database queries —
  no hard-coded analytics values.
- NFR2: The system must handle a dataset of 100,000+ orders without loading
  raw records into the browser (aggregation happens server-side).
- NFR3: Credentials must never be hard-coded; configuration is via
  environment variables (`.env`), with `.env.example` provided and `.env`
  git-ignored.
- NFR4: The system must be runnable locally via `docker compose up --build`.
- NFR5: Errors (DB unavailable, invalid filters, empty results) must be
  handled gracefully with user-friendly messages, never exposing internals.

## Assumptions
- Currency is INR for the purposes of this synthetic dataset; formats can be
  changed by updating `fmtCurrency` in the frontend.
- The synthetic dataset approximates realistic retail/e-commerce behavior
  but is not derived from a real company.
- A single Postgres instance is sufficient for this scale of data; no
  read-replica or sharding is required.

## Constraints
- Must run without external paid services (no hosted ML APIs, no paid BI
  tool required to view the core dashboard).
- Must be deployable with the provided Docker Compose file.

## Success Metrics
- ETL pipeline runs end-to-end with zero FAILing data-quality rules.
- All API endpoints return HTTP 200 with live data.
- Churn model achieves ROC-AUC materially above 0.5 on a time-split holdout
  (achieved: ~0.77 with Random Forest).
- Automated test suite (`tests/`) passes in CI.
