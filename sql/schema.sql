-- ============================================================
-- Enterprise Sales, Customer & Revenue Analytics Platform
-- Database Schema (PostgreSQL)
-- ============================================================

DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS targets CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS date_dimension CASCADE;

-- ------------------------------------------------------------
-- date_dimension
-- ------------------------------------------------------------
CREATE TABLE date_dimension (
    date            DATE PRIMARY KEY,
    day             SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    month_name      VARCHAR(15) NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    week            SMALLINT NOT NULL,
    weekday         VARCHAR(10) NOT NULL,
    fiscal_year     SMALLINT NOT NULL
);

-- ------------------------------------------------------------
-- customers
-- ------------------------------------------------------------
CREATE TABLE customers (
    customer_id         VARCHAR(12) PRIMARY KEY,
    customer_name       VARCHAR(120) NOT NULL,
    email               VARCHAR(150) NOT NULL,
    city                VARCHAR(80) NOT NULL,
    state               VARCHAR(80) NOT NULL,
    region              VARCHAR(30) NOT NULL,
    customer_segment    VARCHAR(30) NOT NULL,
    acquisition_date    DATE NOT NULL,
    customer_status     VARCHAR(20) NOT NULL DEFAULT 'Active',
    CONSTRAINT chk_customer_status CHECK (customer_status IN ('Active','Inactive'))
);
CREATE INDEX idx_customers_region ON customers(region);
CREATE INDEX idx_customers_segment ON customers(customer_segment);
CREATE INDEX idx_customers_acq_date ON customers(acquisition_date);

-- ------------------------------------------------------------
-- products
-- ------------------------------------------------------------
CREATE TABLE products (
    product_id      VARCHAR(12) PRIMARY KEY,
    product_name    VARCHAR(150) NOT NULL,
    category        VARCHAR(60) NOT NULL,
    sub_category    VARCHAR(60) NOT NULL,
    unit_cost       NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    selling_price   NUMERIC(12,2) NOT NULL CHECK (selling_price >= 0),
    supplier        VARCHAR(120) NOT NULL,
    product_status  VARCHAR(20) NOT NULL DEFAULT 'Active',
    CONSTRAINT chk_product_status CHECK (product_status IN ('Active','Discontinued'))
);
CREATE INDEX idx_products_category ON products(category);

-- ------------------------------------------------------------
-- employees
-- ------------------------------------------------------------
CREATE TABLE employees (
    employee_id     VARCHAR(12) PRIMARY KEY,
    employee_name   VARCHAR(120) NOT NULL,
    department      VARCHAR(60) NOT NULL,
    region          VARCHAR(30) NOT NULL,
    joining_date    DATE NOT NULL,
    target_amount   NUMERIC(14,2) NOT NULL CHECK (target_amount >= 0)
);
CREATE INDEX idx_employees_region ON employees(region);

-- ------------------------------------------------------------
-- orders
-- ------------------------------------------------------------
CREATE TABLE orders (
    order_id        VARCHAR(14) PRIMARY KEY,
    order_date      DATE NOT NULL REFERENCES date_dimension(date),
    customer_id     VARCHAR(12) NOT NULL REFERENCES customers(customer_id),
    product_id      VARCHAR(12) NOT NULL REFERENCES products(product_id),
    employee_id     VARCHAR(12) NOT NULL REFERENCES employees(employee_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    discount        NUMERIC(5,4) NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 1),
    revenue         NUMERIC(14,2) NOT NULL CHECK (revenue >= 0),
    cost            NUMERIC(14,2) NOT NULL CHECK (cost >= 0),
    profit          NUMERIC(14,2) NOT NULL,
    payment_method  VARCHAR(30) NOT NULL,
    order_status    VARCHAR(20) NOT NULL DEFAULT 'Completed',
    CONSTRAINT chk_order_status CHECK (order_status IN ('Completed','Returned','Cancelled'))
);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_product ON orders(product_id);
CREATE INDEX idx_orders_employee ON orders(employee_id);
CREATE INDEX idx_orders_status ON orders(order_status);

-- ------------------------------------------------------------
-- returns
-- ------------------------------------------------------------
CREATE TABLE returns (
    return_id       VARCHAR(14) PRIMARY KEY,
    order_id        VARCHAR(14) NOT NULL REFERENCES orders(order_id),
    return_date     DATE NOT NULL,
    return_reason   VARCHAR(80) NOT NULL,
    refund_amount   NUMERIC(14,2) NOT NULL CHECK (refund_amount >= 0)
);
CREATE INDEX idx_returns_order ON returns(order_id);

-- ------------------------------------------------------------
-- targets
-- ------------------------------------------------------------
CREATE TABLE targets (
    target_id       SERIAL PRIMARY KEY,
    employee_id     VARCHAR(12) NOT NULL REFERENCES employees(employee_id),
    month           SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    year            SMALLINT NOT NULL,
    target_amount   NUMERIC(14,2) NOT NULL CHECK (target_amount >= 0),
    CONSTRAINT uq_target UNIQUE (employee_id, month, year)
);
CREATE INDEX idx_targets_employee ON targets(employee_id);
CREATE INDEX idx_targets_period ON targets(year, month);
