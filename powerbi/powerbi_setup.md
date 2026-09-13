# Power BI Setup Guide

## 1. Connect to PostgreSQL

1. In Power BI Desktop: **Get Data → More → Database → PostgreSQL database**.
2. Server: `localhost` (or your Docker host), Port: `5432` (append as
   `localhost:5432` in the Server field).
3. Database: `enterprise_analytics`.
4. Authentication: Database, username `postgres`, password as set in `.env`.
5. Choose **DirectQuery** for a always-fresh dashboard, or **Import** for
   faster interaction with a static snapshot (refresh on a schedule).

## 2. Recommended tables/views to load

Load the pre-aggregated views rather than raw tables where possible — they
already encapsulate the correct joins and filters (`order_status <> 'Cancelled'`
etc.), so you avoid re-deriving business logic in DAX:

- `vw_sales_summary`
- `vw_monthly_revenue`
- `vw_customer_summary`
- `vw_product_summary`
- `vw_region_summary`
- `vw_salesperson_summary`
- `vw_rfm_segments`
- `vw_customer_churn`

Also load the raw `customers`, `products`, `employees`, `orders`, and
`date_dimension` tables if you want to build custom measures beyond what the
views expose.

## 3. Data Model

Set up relationships:

- `orders[customer_id]` → `customers[customer_id]` (many-to-one)
- `orders[product_id]` → `products[product_id]` (many-to-one)
- `orders[employee_id]` → `employees[employee_id]` (many-to-one)
- `orders[order_date]` → `date_dimension[date]` (many-to-one) — mark
  `date_dimension` as a **Date Table** in Power BI (Table tools → Mark as
  date table) to enable time-intelligence DAX functions.

## 4. Dashboard Pages

Mirror the web dashboard's structure:

1. **Executive Overview** — KPI cards (Revenue, Profit, Margin, Orders,
   YoY Growth) + revenue trend line + region/category bar charts.
2. **Sales** — target vs actual, salesperson ranking table, region ranking.
3. **Customers** — retention/churn KPIs, RFM segment donut, customer table.
4. **Products** — top/bottom products, category performance, margin matrix.
5. **Regions** — region comparison table + map visual (if you add lat/long).
6. **Churn & RFM** — risk distribution, at-risk customer table.

## 5. Filters and Slicers

Add slicers for: `date_dimension[year]`/`[month_name]`, `customers[region]`,
`customers[customer_segment]`, `products[category]`, `employees[employee_name]`
— sync them across pages via **View → Sync slicers**.

See `dax_measures.md` for the DAX formulas that power the KPI cards.
