# Data Dictionary

## customers

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| customer_id | VARCHAR(12) PK | Unique customer identifier | CUST000123 | No | Primary key for customer records |
| customer_name | VARCHAR(120) | Full name | Priya Sharma | No | Display name |
| email | VARCHAR(150) | Contact email | priya.sharma123@example.com | No | Contact channel |
| city | VARCHAR(80) | City of residence | Bengaluru | No | Geographic detail |
| state | VARCHAR(80) | State of residence | Karnataka | No | Geographic rollup |
| region | VARCHAR(30) | Sales region | South | No | Used for regional analytics |
| customer_segment | VARCHAR(30) | Business segment | Consumer / Small Business / Corporate / Enterprise | No | Segmentation for KPIs |
| acquisition_date | DATE | Date customer first acquired | 2024-03-11 | No | Used for cohort/growth analysis |
| customer_status | VARCHAR(20) | Active/Inactive flag | Active | No | Filters active customer base |

## products

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| product_id | VARCHAR(12) PK | Unique product identifier | PROD00042 | No | Primary key |
| product_name | VARCHAR(150) | Product display name | Laptop Pro 482 | No | Display name |
| category | VARCHAR(60) | Top-level category | Electronics | No | Category rollups |
| sub_category | VARCHAR(60) | Sub-category | Laptops | No | Finer-grained rollups |
| unit_cost | NUMERIC(12,2) | Cost to acquire/produce one unit | 245.50 | No | Used to compute profit |
| selling_price | NUMERIC(12,2) | List selling price | 399.00 | No | Base price before discount |
| supplier | VARCHAR(120) | Supplier name | Sharma Supply Co. | No | Supply chain reference |
| product_status | VARCHAR(20) | Active/Discontinued | Active | No | Filters sellable catalog |

## employees

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| employee_id | VARCHAR(12) PK | Unique employee identifier | EMP0034 | No | Primary key |
| employee_name | VARCHAR(120) | Full name | Rahul Verma | No | Display name |
| department | VARCHAR(60) | Department/team | Field Sales | No | Org rollup |
| region | VARCHAR(30) | Assigned sales region | West | No | Regional performance rollup |
| joining_date | DATE | Date hired | 2023-06-01 | No | Tenure calculations |
| target_amount | NUMERIC(14,2) | Annual sales target | 1200000.00 | No | Basis for achievement % |

## orders

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| order_id | VARCHAR(14) PK | Unique order identifier | ORD00012345 | No | Primary key |
| order_date | DATE FK→date_dimension | Date of order | 2024-05-02 | No | Time-series joins |
| customer_id | VARCHAR(12) FK→customers | Ordering customer | CUST000123 | No | Customer rollup |
| product_id | VARCHAR(12) FK→products | Ordered product | PROD00042 | No | Product rollup |
| employee_id | VARCHAR(12) FK→employees | Salesperson credited | EMP0034 | No | Sales attribution |
| quantity | INTEGER | Units ordered | 3 | No | Volume metric |
| unit_price | NUMERIC(12,2) | Price per unit at time of sale | 399.00 | No | Pricing detail |
| discount | NUMERIC(5,4) | Discount fraction applied | 0.10 | No | Discount analysis |
| revenue | NUMERIC(14,2) | Net revenue for the line item | 1077.30 | No | Core revenue metric |
| cost | NUMERIC(14,2) | Total cost for the line item | 736.50 | No | Core cost metric |
| profit | NUMERIC(14,2) | revenue − cost | 340.80 | No | Core profit metric |
| payment_method | VARCHAR(30) | Payment channel | UPI | No | Payment mix analysis |
| order_status | VARCHAR(20) | Completed/Returned/Cancelled | Completed | No | Filters valid revenue |

## returns

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| return_id | VARCHAR(14) PK | Unique return identifier | RET0001234 | No | Primary key |
| order_id | VARCHAR(14) FK→orders | Associated order | ORD00012345 | No | Links return to sale |
| return_date | DATE | Date of return | 2024-05-15 | No | Return timing analysis |
| return_reason | VARCHAR(80) | Reason given | Defective Product | No | Root-cause analysis |
| refund_amount | NUMERIC(14,2) | Amount refunded | 1077.30 | No | Refund impact on revenue |

## targets

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| target_id | SERIAL PK | Surrogate key | 1 | No | Primary key |
| employee_id | VARCHAR(12) FK→employees | Employee assigned | EMP0034 | No | Links target to employee |
| month | SMALLINT | Target month (1–12) | 5 | No | Monthly granularity |
| year | SMALLINT | Target year | 2024 | No | Yearly granularity |
| target_amount | NUMERIC(14,2) | Monthly target amount | 100000.00 | No | Basis for achievement % |

## date_dimension

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| date | DATE PK | Calendar date | 2024-05-02 | No | Join key for time-series |
| day | SMALLINT | Day of month | 2 | No | Daily granularity |
| month | SMALLINT | Month number | 5 | No | Monthly rollups |
| month_name | VARCHAR(15) | Month name | May | No | Display label |
| quarter | SMALLINT | Quarter number | 2 | No | Quarterly rollups |
| year | SMALLINT | Calendar year | 2024 | No | Yearly rollups |
| week | SMALLINT | ISO week number | 18 | No | Weekly rollups |
| weekday | VARCHAR(10) | Day name | Thursday | No | Day-of-week analysis |
| fiscal_year | SMALLINT | Fiscal year (Apr–Mar) | 2025 | No | Fiscal reporting |

## customer_churn_predictions (ML output table)

| Column | Type | Description | Example | Nullable | Business Meaning |
|---|---|---|---|---|---|
| customer_id | VARCHAR(12) PK, FK→customers | Customer scored | CUST000123 | No | Links prediction to customer |
| churn_probability | NUMERIC(6,5) | Model probability of churn | 0.73210 | No | Risk score |
| churn_prediction | SMALLINT | Binary prediction (0/1) | 1 | No | Thresholded label |
| risk_level | VARCHAR(10) | Low/Medium/High | High | No | Business-friendly tier |
