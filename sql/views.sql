-- ============================================================
-- Analytical Views (used by API, Power BI, and reporting)
-- ============================================================

-- ------------------------------------------------------------
-- vw_monthly_revenue: revenue/profit/orders per calendar month
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_TRUNC('month', o.order_date)::date AS month_start,
    EXTRACT(YEAR FROM o.order_date)::int AS year,
    EXTRACT(MONTH FROM o.order_date)::int AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.revenue) AS total_revenue,
    SUM(o.profit) AS total_profit,
    SUM(o.quantity) AS units_sold,
    ROUND(AVG(o.revenue), 2) AS avg_order_value
FROM orders o
WHERE o.order_status <> 'Cancelled'
GROUP BY 1, 2, 3
ORDER BY 1;

-- ------------------------------------------------------------
-- vw_sales_summary: overall KPI snapshot
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_sales_summary AS
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.revenue) AS total_revenue,
    SUM(o.profit) AS total_profit,
    ROUND(SUM(o.profit) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(o.revenue), 2) AS avg_order_value,
    COUNT(DISTINCT o.customer_id) AS active_customers,
    SUM(o.quantity) AS units_sold
FROM orders o
WHERE o.order_status <> 'Cancelled';

-- ------------------------------------------------------------
-- vw_customer_summary: per-customer rollup
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
    c.customer_id,
    c.customer_name,
    c.region,
    c.customer_segment,
    c.customer_status,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.revenue), 0) AS total_revenue,
    COALESCE(SUM(o.profit), 0) AS total_profit,
    MIN(o.order_date) AS first_purchase_date,
    MAX(o.order_date) AS last_purchase_date,
    (CURRENT_DATE - MAX(o.order_date)) AS days_since_last_purchase
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status <> 'Cancelled'
GROUP BY c.customer_id, c.customer_name, c.region, c.customer_segment, c.customer_status;

-- ------------------------------------------------------------
-- vw_product_summary: per-product rollup
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_product_summary AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.quantity), 0) AS units_sold,
    COALESCE(SUM(o.revenue), 0) AS total_revenue,
    COALESCE(SUM(o.profit), 0) AS total_profit,
    ROUND(COALESCE(SUM(o.profit), 0) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS profit_margin_pct,
    COUNT(r.return_id) AS return_count,
    ROUND(AVG(o.discount) * 100, 2) AS avg_discount_pct
FROM products p
LEFT JOIN orders o ON o.product_id = p.product_id AND o.order_status <> 'Cancelled'
LEFT JOIN returns r ON r.order_id = o.order_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category;

-- ------------------------------------------------------------
-- vw_region_summary: per-region rollup
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_region_summary AS
SELECT
    c.region,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.revenue), 0) AS total_revenue,
    COALESCE(SUM(o.profit), 0) AS total_profit,
    ROUND(COALESCE(SUM(o.profit), 0) / NULLIF(SUM(o.revenue), 0) * 100, 2) AS profit_margin_pct
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status <> 'Cancelled'
GROUP BY c.region;

-- ------------------------------------------------------------
-- vw_salesperson_summary: per-employee rollup vs target
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_salesperson_summary AS
SELECT
    e.employee_id,
    e.employee_name,
    e.region,
    e.department,
    e.target_amount AS annual_target,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.revenue), 0) AS total_revenue,
    COALESCE(SUM(o.profit), 0) AS total_profit,
    COUNT(DISTINCT o.customer_id) AS customer_count,
    ROUND(COALESCE(SUM(o.revenue), 0) / NULLIF(e.target_amount, 0) * 100, 2) AS target_achievement_pct
FROM employees e
LEFT JOIN orders o ON o.employee_id = e.employee_id AND o.order_status <> 'Cancelled'
GROUP BY e.employee_id, e.employee_name, e.region, e.department, e.target_amount;

-- ------------------------------------------------------------
-- vw_rfm_segments: RFM inputs per customer (segmentation done in Python/SQL below)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_rfm_base AS
SELECT
    c.customer_id,
    c.customer_name,
    (CURRENT_DATE - MAX(o.order_date)) AS recency_days,
    COUNT(o.order_id) AS frequency,
    COALESCE(SUM(o.revenue), 0) AS monetary
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id AND o.order_status <> 'Cancelled'
GROUP BY c.customer_id, c.customer_name;

CREATE OR REPLACE VIEW vw_rfm_segments AS
WITH scored AS (
    SELECT
        customer_id,
        customer_name,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM vw_rfm_base
)
SELECT
    customer_id,
    customer_name,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
        WHEN r_score >= 3 AND f_score <= 3 AND m_score >= 3 THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'Can''t Lose Them'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Lost Customers'
        ELSE 'Hibernating'
    END AS segment
FROM scored;

-- ------------------------------------------------------------
-- vw_customer_churn (placeholder view, populated from ML predictions table)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_churn_predictions (
    customer_id VARCHAR(12) PRIMARY KEY REFERENCES customers(customer_id),
    churn_probability NUMERIC(6,5),
    churn_prediction SMALLINT,
    risk_level VARCHAR(10)
);

CREATE OR REPLACE VIEW vw_customer_churn AS
SELECT
    cp.customer_id,
    c.customer_name,
    c.region,
    c.customer_segment,
    cp.churn_probability,
    cp.churn_prediction,
    cp.risk_level
FROM customer_churn_predictions cp
JOIN customers c ON c.customer_id = cp.customer_id;
