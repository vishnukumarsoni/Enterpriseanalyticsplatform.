-- ============================================================
-- Core KPI queries — used as the basis for Power BI measures
-- and the FastAPI dashboard endpoint.
-- ============================================================

-- Total Revenue / Profit / Margin / Orders / Active Customers (all-time)
SELECT
    SUM(revenue) AS total_revenue,
    SUM(profit) AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS active_customers
FROM orders
WHERE order_status <> 'Cancelled';

-- Average Order Value
SELECT ROUND(AVG(revenue), 2) AS avg_order_value
FROM orders WHERE order_status <> 'Cancelled';

-- Average Profit per Order
SELECT ROUND(AVG(profit), 2) AS avg_profit_per_order
FROM orders WHERE order_status <> 'Cancelled';

-- Customer Retention Rate (customers active in month M who were also active in M-1)
WITH monthly_customers AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS month
    FROM orders WHERE order_status <> 'Cancelled'
)
SELECT
    curr.month,
    COUNT(DISTINCT curr.customer_id) AS active_customers,
    COUNT(DISTINCT prev.customer_id) AS retained_from_prior_month,
    ROUND(COUNT(DISTINCT prev.customer_id)::numeric / NULLIF(COUNT(DISTINCT curr.customer_id), 0) * 100, 2) AS retention_rate_pct
FROM monthly_customers curr
LEFT JOIN monthly_customers prev
    ON prev.customer_id = curr.customer_id AND prev.month = curr.month - INTERVAL '1 month'
GROUP BY curr.month ORDER BY curr.month;

-- Customer Churn Rate (from ML predictions table)
SELECT
    ROUND(COUNT(*) FILTER (WHERE churn_prediction = 1)::numeric / COUNT(*) * 100, 2) AS churn_rate_pct
FROM customer_churn_predictions;

-- Customer Lifetime Value (average total revenue per customer)
SELECT ROUND(AVG(total_revenue), 2) AS avg_customer_lifetime_value
FROM (
    SELECT customer_id, SUM(revenue) AS total_revenue
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY customer_id
) t;

-- Sales Target Achievement (overall, current year)
-- NOTE: targets and orders are aggregated independently first, then combined,
-- to avoid a join fan-out that would otherwise multiply target_amount by the
-- number of matching order rows.
WITH monthly_targets AS (
    SELECT employee_id, year, month, SUM(target_amount) AS target_amount
    FROM targets
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)::int
    GROUP BY employee_id, year, month
),
monthly_actuals AS (
    SELECT employee_id, EXTRACT(YEAR FROM order_date)::int AS year,
           EXTRACT(MONTH FROM order_date)::int AS month, SUM(revenue) AS revenue
    FROM orders
    WHERE order_status <> 'Cancelled'
      AND EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY employee_id, 2, 3
)
SELECT
    SUM(mt.target_amount) AS total_target,
    SUM(COALESCE(ma.revenue, 0)) AS total_actual,
    ROUND(SUM(COALESCE(ma.revenue, 0)) / NULLIF(SUM(mt.target_amount), 0) * 100, 2) AS achievement_pct
FROM monthly_targets mt
LEFT JOIN monthly_actuals ma
    ON ma.employee_id = mt.employee_id AND ma.year = mt.year AND ma.month = mt.month;

-- Best Selling / Highest Revenue / Highest Profit / Lowest Margin Product
SELECT product_id, product_name, SUM(quantity) AS units_sold
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY product_id, product_name ORDER BY units_sold DESC LIMIT 1;

SELECT product_id, product_name, SUM(revenue) AS revenue
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY product_id, product_name ORDER BY revenue DESC LIMIT 1;

SELECT product_id, product_name, SUM(profit) AS profit
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY product_id, product_name ORDER BY profit DESC LIMIT 1;

SELECT product_id, product_name,
       ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY product_id, product_name
HAVING SUM(revenue) > 0
ORDER BY margin_pct ASC LIMIT 1;
