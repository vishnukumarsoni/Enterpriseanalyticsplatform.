-- ============================================================
-- Enterprise Analytics: Business Query Library (30+ queries)
-- Run against the enterprise_analytics PostgreSQL database
-- ============================================================

-- 1. Top 10 customers by revenue
SELECT c.customer_id, c.customer_name, SUM(o.revenue) AS total_revenue
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC
LIMIT 10;

-- 2. Top 10 products by revenue
SELECT p.product_id, p.product_name, SUM(o.revenue) AS total_revenue
FROM products p JOIN orders o ON o.product_id = p.product_id
WHERE o.order_status <> 'Cancelled'
GROUP BY p.product_id, p.product_name
ORDER BY total_revenue DESC
LIMIT 10;

-- 3. Monthly revenue
SELECT DATE_TRUNC('month', order_date)::date AS month, SUM(revenue) AS revenue
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY 1 ORDER BY 1;

-- 4. Monthly profit
SELECT DATE_TRUNC('month', order_date)::date AS month, SUM(profit) AS profit
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY 1 ORDER BY 1;

-- 5. Year-over-year revenue growth
WITH yearly AS (
    SELECT EXTRACT(YEAR FROM order_date)::int AS yr, SUM(revenue) AS revenue
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY 1
)
SELECT yr, revenue,
       LAG(revenue) OVER (ORDER BY yr) AS prev_year_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY yr)) / NULLIF(LAG(revenue) OVER (ORDER BY yr), 0) * 100, 2) AS yoy_growth_pct
FROM yearly ORDER BY yr;

-- 6. Month-over-month revenue growth
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date)::date AS month, SUM(revenue) AS revenue
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY 1
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2) AS mom_growth_pct
FROM monthly ORDER BY month;

-- 7. Regional ranking by revenue
SELECT region, SUM(revenue) AS revenue,
       RANK() OVER (ORDER BY SUM(revenue) DESC) AS region_rank
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY region;

-- 8. Salesperson ranking by revenue
SELECT e.employee_id, e.employee_name, SUM(o.revenue) AS revenue,
       DENSE_RANK() OVER (ORDER BY SUM(o.revenue) DESC) AS sales_rank
FROM employees e JOIN orders o ON o.employee_id = e.employee_id
WHERE o.order_status <> 'Cancelled'
GROUP BY e.employee_id, e.employee_name
ORDER BY sales_rank;

-- 9. Customer retention (customers with orders in consecutive months)
WITH cust_months AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS month
    FROM orders WHERE order_status <> 'Cancelled'
),
with_prev AS (
    SELECT customer_id, month,
           LAG(month) OVER (PARTITION BY customer_id ORDER BY month) AS prev_month
    FROM cust_months
)
SELECT month,
       COUNT(*) FILTER (WHERE prev_month = month - INTERVAL '1 month') AS retained_customers,
       COUNT(*) AS total_active_customers
FROM with_prev GROUP BY month ORDER BY month;

-- 10. Repeat customers (more than one order)
SELECT customer_id, COUNT(*) AS order_count
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY customer_id HAVING COUNT(*) > 1
ORDER BY order_count DESC;

-- 11. Average order value overall and by segment
SELECT c.customer_segment, ROUND(AVG(o.revenue), 2) AS avg_order_value
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY c.customer_segment;

-- 12. Running total of revenue by month
SELECT month, revenue,
       SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM (
    SELECT DATE_TRUNC('month', order_date)::date AS month, SUM(revenue) AS revenue
    FROM orders WHERE order_status <> 'Cancelled' GROUP BY 1
) m ORDER BY month;

-- 13. Revenue contribution % by region
SELECT region, SUM(revenue) AS revenue,
       ROUND(SUM(revenue) / SUM(SUM(revenue)) OVER () * 100, 2) AS pct_of_total
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY region ORDER BY revenue DESC;

-- 14. Product profitability (margin %)
SELECT product_id, product_name,
       SUM(revenue) AS revenue, SUM(profit) AS profit,
       ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY product_id, product_name
ORDER BY margin_pct DESC;

-- 15. Customers with declining purchases (last 3 months vs prior 3 months)
WITH recent AS (
    SELECT customer_id, SUM(revenue) AS rev_recent
    FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '3 months' AND order_status <> 'Cancelled'
    GROUP BY customer_id
),
prior AS (
    SELECT customer_id, SUM(revenue) AS rev_prior
    FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '6 months'
                  AND order_date < CURRENT_DATE - INTERVAL '3 months' AND order_status <> 'Cancelled'
    GROUP BY customer_id
)
SELECT COALESCE(r.customer_id, p.customer_id) AS customer_id,
       COALESCE(r.rev_recent, 0) AS rev_recent, COALESCE(p.rev_prior, 0) AS rev_prior
FROM recent r FULL OUTER JOIN prior p ON r.customer_id = p.customer_id
WHERE COALESCE(r.rev_recent, 0) < COALESCE(p.rev_prior, 0);

-- 16. Customers with no purchase in the last 90 days
SELECT c.customer_id, c.customer_name, MAX(o.order_date) AS last_purchase
FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status <> 'Cancelled'
GROUP BY c.customer_id, c.customer_name
HAVING MAX(o.order_date) < CURRENT_DATE - INTERVAL '90 days' OR MAX(o.order_date) IS NULL;

-- 17. Target achievement by employee (current year)
SELECT e.employee_id, e.employee_name,
       SUM(t.target_amount) AS annual_target,
       COALESCE(SUM(o.revenue), 0) AS actual_revenue,
       ROUND(COALESCE(SUM(o.revenue), 0) / NULLIF(SUM(t.target_amount), 0) * 100, 2) AS achievement_pct
FROM employees e
JOIN targets t ON t.employee_id = e.employee_id AND t.year = EXTRACT(YEAR FROM CURRENT_DATE)::int
LEFT JOIN orders o ON o.employee_id = e.employee_id
     AND EXTRACT(YEAR FROM o.order_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND o.order_status <> 'Cancelled'
GROUP BY e.employee_id, e.employee_name;

-- 18. Top products by region
WITH ranked AS (
    SELECT c.region, p.product_name, SUM(o.revenue) AS revenue,
           ROW_NUMBER() OVER (PARTITION BY c.region ORDER BY SUM(o.revenue) DESC) AS rn
    FROM orders o JOIN customers c ON c.customer_id = o.customer_id
                  JOIN products p ON p.product_id = o.product_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY c.region, p.product_name
)
SELECT region, product_name, revenue FROM ranked WHERE rn <= 5 ORDER BY region, revenue DESC;

-- 19. Revenue by category
SELECT category, SUM(revenue) AS revenue, SUM(profit) AS profit
FROM products p JOIN orders o USING (product_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY category ORDER BY revenue DESC;

-- 20. Quarterly performance
SELECT EXTRACT(YEAR FROM order_date)::int AS year, EXTRACT(QUARTER FROM order_date)::int AS quarter,
       SUM(revenue) AS revenue, SUM(profit) AS profit
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY 1, 2 ORDER BY 1, 2;

-- 21. Customer lifetime value (total revenue and profit per customer)
SELECT customer_id, SUM(revenue) AS lifetime_revenue, SUM(profit) AS lifetime_profit,
       COUNT(*) AS total_orders
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY customer_id ORDER BY lifetime_revenue DESC;

-- 22. First vs repeat purchase revenue split
WITH ordered AS (
    SELECT customer_id, order_id, revenue,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS purchase_seq
    FROM orders WHERE order_status <> 'Cancelled'
)
SELECT CASE WHEN purchase_seq = 1 THEN 'First Purchase' ELSE 'Repeat Purchase' END AS purchase_type,
       SUM(revenue) AS revenue, COUNT(*) AS orders
FROM ordered GROUP BY 1;

-- 23. Return rate by product
SELECT p.product_id, p.product_name,
       COUNT(o.order_id) AS total_orders,
       COUNT(r.return_id) AS total_returns,
       ROUND(COUNT(r.return_id)::numeric / NULLIF(COUNT(o.order_id), 0) * 100, 2) AS return_rate_pct
FROM products p JOIN orders o ON o.product_id = p.product_id
LEFT JOIN returns r ON r.order_id = o.order_id
GROUP BY p.product_id, p.product_name
ORDER BY return_rate_pct DESC;

-- 24. Discount impact on profit margin
SELECT
    CASE
        WHEN discount = 0 THEN '0%'
        WHEN discount <= 0.10 THEN '1-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        ELSE '20%+'
    END AS discount_band,
    ROUND(AVG(profit / NULLIF(revenue, 0)) * 100, 2) AS avg_margin_pct,
    COUNT(*) AS orders
FROM orders WHERE order_status <> 'Cancelled' AND revenue > 0
GROUP BY 1 ORDER BY 1;

-- 25. High-value customers (top 5% by revenue)
WITH ranked AS (
    SELECT customer_id, SUM(revenue) AS revenue,
           NTILE(20) OVER (ORDER BY SUM(revenue) DESC) AS pct_bucket
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY customer_id
)
SELECT customer_id, revenue FROM ranked WHERE pct_bucket = 1 ORDER BY revenue DESC;

-- 26. At-risk customers (RFM-based)
SELECT customer_id, customer_name, recency_days, frequency, monetary, segment
FROM vw_rfm_segments WHERE segment IN ('At Risk', 'Can''t Lose Them')
ORDER BY monetary DESC;

-- 27. Revenue concentration (Pareto: top 20% customers vs total revenue)
WITH cust_rev AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM orders WHERE order_status <> 'Cancelled' GROUP BY customer_id
),
ranked AS (
    SELECT *, NTILE(5) OVER (ORDER BY revenue DESC) AS quintile FROM cust_rev
)
SELECT quintile, SUM(revenue) AS revenue,
       ROUND(SUM(revenue) / SUM(SUM(revenue)) OVER () * 100, 2) AS pct_of_total
FROM ranked GROUP BY quintile ORDER BY quintile;

-- 28. Salesperson performance vs prior period
WITH monthly_sales AS (
    SELECT employee_id, DATE_TRUNC('month', order_date) AS month, SUM(revenue) AS revenue
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY employee_id, DATE_TRUNC('month', order_date)
)
SELECT employee_id, month, revenue,
       LAG(revenue) OVER (PARTITION BY employee_id ORDER BY month) AS prev_month_revenue
FROM monthly_sales ORDER BY employee_id, month;

-- 29. Best-performing region by profit margin
SELECT region, ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY region ORDER BY margin_pct DESC;

-- 30. Revenue forecast preparation (monthly time series input for Python/ML)
SELECT DATE_TRUNC('month', order_date)::date AS month, SUM(revenue) AS revenue
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY 1 ORDER BY 1;

-- 31. Customer acquisition trend by month
SELECT DATE_TRUNC('month', acquisition_date)::date AS month, COUNT(*) AS new_customers
FROM customers GROUP BY 1 ORDER BY 1;

-- 32. Most discounted products
SELECT p.product_id, p.product_name, ROUND(AVG(o.discount) * 100, 2) AS avg_discount_pct
FROM products p JOIN orders o USING (product_id)
GROUP BY p.product_id, p.product_name
ORDER BY avg_discount_pct DESC LIMIT 10;
