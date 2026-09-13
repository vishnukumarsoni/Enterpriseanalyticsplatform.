"""
Synthetic Enterprise Dataset Generator
=======================================
Generates realistic raw CSV data for the Enterprise Sales, Customer & Revenue
Analytics Platform: customers, products, employees, orders, returns, targets,
and a date dimension.

Run:
    python generate_data.py
"""
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import random
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("generate_data")

RNG_SEED = 42
np.random.seed(RNG_SEED)
random.seed(RNG_SEED)
fake = Faker()
Faker.seed(RNG_SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

N_CUSTOMERS = 10500
N_PRODUCTS = 550
N_EMPLOYEES = 120
N_ORDERS = 105000
N_YEARS = 3

START_DATE = date.today().replace(day=1) - timedelta(days=365 * N_YEARS + 30)
END_DATE = date.today()

REGIONS = ["North", "South", "East", "West", "Central"]

STATE_BY_REGION = {
    "North": ["Punjab", "Haryana", "Himachal Pradesh", "Uttarakhand", "Delhi"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"],
    "East": ["West Bengal", "Odisha", "Bihar", "Jharkhand", "Assam"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
    "Central": ["Madhya Pradesh", "Chhattisgarh", "Uttar Pradesh"],
}

CITY_BY_STATE = {
    "Punjab": ["Chandigarh", "Ludhiana", "Amritsar"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat"],
    "Himachal Pradesh": ["Shimla", "Manali"],
    "Uttarakhand": ["Dehradun", "Haridwar"],
    "Delhi": ["New Delhi", "Dwarka", "Rohini"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada"],
    "Telangana": ["Hyderabad", "Warangal"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Bihar": ["Patna", "Gaya"],
    "Jharkhand": ["Ranchi", "Jamshedpur"],
    "Assam": ["Guwahati", "Dibrugarh"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
    "Goa": ["Panaji", "Margao"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
    "Chhattisgarh": ["Raipur", "Bilaspur"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Varanasi"],
}

SEGMENTS = ["Consumer", "Small Business", "Corporate", "Enterprise"]
SEGMENT_WEIGHTS = [0.45, 0.25, 0.20, 0.10]

CATEGORY_TREE = {
    "Electronics": ["Laptops", "Smartphones", "Audio", "Cameras", "Accessories"],
    "Office Supplies": ["Paper Products", "Binders", "Storage", "Writing Instruments"],
    "Furniture": ["Chairs", "Desks", "Bookcases", "Furnishings"],
    "Apparel": ["Menswear", "Womenswear", "Footwear", "Accessories"],
    "Home & Kitchen": ["Cookware", "Small Appliances", "Storage & Organization"],
    "Sports & Outdoors": ["Fitness Equipment", "Outdoor Gear", "Team Sports"],
}

SUPPLIERS = [f"{fake.company()} {suffix}" for suffix in
             ["Supply Co.", "Distribution Ltd.", "Wholesale Group", "Industries", "Trading Co."]
             for _ in range(1)]
SUPPLIERS = list(set([fake.company() + " " + random.choice(["Supply Co.", "Distribution Ltd.", "Wholesale", "Industries", "Traders"]) for _ in range(60)]))

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery", "Wallet"]
PAYMENT_WEIGHTS = [0.30, 0.15, 0.30, 0.12, 0.08, 0.05]

RETURN_REASONS = ["Defective Product", "Wrong Item Shipped", "Not as Described",
                  "Changed Mind", "Late Delivery", "Better Price Found", "Quality Issue"]

DEPARTMENTS = ["Sales", "Key Accounts", "Field Sales", "Inside Sales"]


def gen_date_dimension():
    log.info("Generating date_dimension ...")
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    df = pd.DataFrame({"date": dates})
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["weekday"] = df["date"].dt.strftime("%A")
    # Fiscal year starts April 1 (Apr Y -> Mar Y+1 = FY Y+1)
    df["fiscal_year"] = np.where(df["month"] >= 4, df["year"] + 1, df["year"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def gen_customers(n):
    log.info(f"Generating {n} customers ...")
    rows = []
    for i in range(1, n + 1):
        region = random.choice(REGIONS)
        state = random.choice(STATE_BY_REGION[region])
        city = random.choice(CITY_BY_STATE[state])
        name = fake.name()
        acquisition_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)
        status = np.random.choice(["Active", "Inactive"], p=[0.88, 0.12])
        rows.append({
            "customer_id": f"CUST{i:06d}",
            "customer_name": name,
            "email": f"{name.lower().replace(' ', '.')}{i}@{fake.free_email_domain()}",
            "city": city,
            "state": state,
            "region": region,
            "customer_segment": np.random.choice(SEGMENTS, p=SEGMENT_WEIGHTS),
            "acquisition_date": acquisition_date.isoformat(),
            "customer_status": status,
        })
    return pd.DataFrame(rows)


def gen_products(n):
    log.info(f"Generating {n} products ...")
    rows = []
    adjectives = ["Pro", "Ultra", "Max", "Elite", "Classic", "Prime", "Advanced", "Compact", "Deluxe", "Essential"]
    for i in range(1, n + 1):
        category = random.choice(list(CATEGORY_TREE.keys()))
        sub_category = random.choice(CATEGORY_TREE[category])
        unit_cost = round(np.random.lognormal(mean=4.0, sigma=1.0) + 5, 2)
        margin_multiplier = np.random.uniform(1.15, 1.85)
        selling_price = round(unit_cost * margin_multiplier, 2)
        product_name = f"{sub_category[:-1] if sub_category.endswith('s') else sub_category} {random.choice(adjectives)} {random.randint(100,999)}"
        rows.append({
            "product_id": f"PROD{i:05d}",
            "product_name": product_name,
            "category": category,
            "sub_category": sub_category,
            "unit_cost": unit_cost,
            "selling_price": selling_price,
            "supplier": random.choice(SUPPLIERS),
            "product_status": np.random.choice(["Active", "Discontinued"], p=[0.92, 0.08]),
        })
    return pd.DataFrame(rows)


def gen_employees(n, n_customers, n_orders_target, avg_order_revenue_estimate=460):
    log.info(f"Generating {n} employees ...")
    rows = []
    # Calibrate annual target around what's actually achievable: total expected
    # revenue over the ~3-year history, divided across employees and years,
    # with realistic variance so achievement naturally spreads above/below 100%.
    n_years = N_YEARS
    expected_total_revenue = n_orders_target * avg_order_revenue_estimate
    avg_annual_revenue_per_emp = expected_total_revenue / n / n_years
    for i in range(1, n + 1):
        region = random.choice(REGIONS)
        joining_date = fake.date_between(start_date=START_DATE, end_date=END_DATE - timedelta(days=60))
        target = avg_annual_revenue_per_emp * np.random.uniform(0.75, 1.25)
        rows.append({
            "employee_id": f"EMP{i:04d}",
            "employee_name": fake.name(),
            "department": random.choice(DEPARTMENTS),
            "region": region,
            "joining_date": joining_date.isoformat(),
            "target_amount": round(target, 2),
        })
    return pd.DataFrame(rows)


def gen_orders(n, customers_df, products_df, employees_df):
    """
    Generates orders with PERSISTENT per-customer behavior so that churn/RFM/
    forecasting have real signal to learn from:
      - each customer has a latent activity_score (how often they buy)
      - ~30% of customers are "churners": they stop purchasing entirely after
        some point in their lifetime, well before the dataset's end date
      - active customers keep buying up to the dataset's end date
    This makes recency/frequency/monetary genuinely predictive of future
    (in)activity, instead of every order being independently random.
    """
    log.info(f"Generating ~{n} orders with persistent customer behavior ...")
    rng = np.random.default_rng(RNG_SEED)

    cust_ids = customers_df["customer_id"].values
    n_cust = len(cust_ids)
    acq_dates = pd.to_datetime(customers_df["acquisition_date"]).values
    cust_region = customers_df.set_index("customer_id")["region"].to_dict()

    max_date = np.datetime64(END_DATE)
    total_span_days = (max_date - acq_dates).astype("timedelta64[D]").astype(int)
    total_span_days = np.clip(total_span_days, 1, None)

    # Latent per-customer activity level (lognormal -> most customers moderate,
    # a long tail of high-frequency buyers)
    activity_score = rng.lognormal(mean=0.0, sigma=0.7, size=n_cust)

    # ~30% of customers churn (stop buying) at some point before the dataset ends,
    # leaving a real gap of at least 150 days with zero activity at the end.
    is_churner = rng.random(n_cust) < 0.30
    min_active_days = 60
    churn_offset = rng.integers(min_active_days, np.maximum(total_span_days - 150, min_active_days + 1))
    active_end_days = np.where(is_churner, np.minimum(churn_offset, total_span_days), total_span_days)
    active_end_days = np.clip(active_end_days, 1, total_span_days)

    # Expected number of orders per customer, scaled to hit ~n total orders
    raw_weight = activity_score * (active_end_days / total_span_days.mean())
    scale = n / raw_weight.sum()
    expected_orders = np.clip(raw_weight * scale, 0.3, None)
    order_counts = rng.poisson(expected_orders)
    order_counts = np.maximum(order_counts, 1)  # every customer has at least 1 order

    log.info(f"  Target orders: {n}, generated (pre-trim) total: {order_counts.sum()}, "
             f"churners: {is_churner.sum()} ({is_churner.mean():.1%})")

    # Build flat arrays: repeat each customer by its order_count
    cust_idx_flat = np.repeat(np.arange(n_cust), order_counts)
    total_rows = len(cust_idx_flat)

    acq_flat = acq_dates[cust_idx_flat]
    active_end_flat = active_end_days[cust_idx_flat]

    # Uniform random day offset within each customer's active window
    day_offsets = (rng.random(total_rows) * active_end_flat).astype(int)
    order_dates = acq_flat + day_offsets.astype("timedelta64[D]")

    cust_choice = cust_ids[cust_idx_flat]

    prod_ids = products_df["product_id"].values
    prod_price_map = products_df.set_index("product_id")["selling_price"].to_dict()
    prod_cost_map = products_df.set_index("product_id")["unit_cost"].to_dict()
    prod_choice = rng.choice(prod_ids, size=total_rows)

    emp_by_region = employees_df.groupby("region")["employee_id"].apply(list).to_dict()
    all_employee_ids = employees_df["employee_id"].tolist()

    qty = np.clip(rng.poisson(2, size=total_rows) + 1, 1, 15)
    price = np.array([prod_price_map[p] for p in prod_choice])
    cost_unit = np.array([prod_cost_map[p] for p in prod_choice])
    discount = rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20, 0.25],
                           size=total_rows,
                           p=[0.35, 0.1, 0.1, 0.15, 0.15, 0.08, 0.04, 0.03])
    revenue = np.round(qty * price * (1 - discount), 2)
    cost = np.round(qty * cost_unit, 2)
    profit = np.round(revenue - cost, 2)
    payment = rng.choice(PAYMENT_METHODS, size=total_rows, p=PAYMENT_WEIGHTS)
    status = rng.choice(["Completed", "Returned", "Cancelled"], size=total_rows, p=[0.90, 0.07, 0.03])

    employee_choice = np.empty(total_rows, dtype=object)
    for region, emp_list in emp_by_region.items():
        mask = np.array([cust_region[c] == region for c in cust_choice])
        n_mask = mask.sum()
        if n_mask:
            employee_choice[mask] = rng.choice(emp_list or all_employee_ids, size=n_mask)

    df = pd.DataFrame({
        "order_id": [f"ORD{i+1:08d}" for i in range(total_rows)],
        "order_date": pd.to_datetime(order_dates).strftime("%Y-%m-%d"),
        "customer_id": cust_choice,
        "product_id": prod_choice,
        "employee_id": employee_choice,
        "quantity": qty,
        "unit_price": price,
        "discount": discount,
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "payment_method": payment,
        "order_status": status,
    })
    log.info(f"  Final orders generated: {len(df):,}")
    return df


def gen_returns(orders_df):
    log.info("Generating returns ...")
    returned = orders_df[orders_df["order_status"] == "Returned"].copy()
    rows = []
    for i, r in enumerate(returned.itertuples(), start=1):
        return_date = pd.Timestamp(r.order_date) + timedelta(days=int(np.random.randint(1, 21)))
        rows.append({
            "return_id": f"RET{i:07d}",
            "order_id": r.order_id,
            "return_date": return_date.strftime("%Y-%m-%d"),
            "return_reason": random.choice(RETURN_REASONS),
            "refund_amount": r.revenue,
        })
    return pd.DataFrame(rows)


def gen_targets(employees_df):
    log.info("Generating monthly targets ...")
    rows = []
    months = pd.period_range(START_DATE, END_DATE, freq="M")
    for emp in employees_df.itertuples():
        base = emp.target_amount / 12
        for p in months:
            seasonal_factor = np.random.uniform(0.85, 1.15)
            rows.append({
                "employee_id": emp.employee_id,
                "month": p.month,
                "year": p.year,
                "target_amount": round(base * seasonal_factor, 2),
            })
    return pd.DataFrame(rows)


def main():
    date_dim = gen_date_dimension()
    customers = gen_customers(N_CUSTOMERS)
    products = gen_products(N_PRODUCTS)
    employees = gen_employees(N_EMPLOYEES, N_CUSTOMERS, N_ORDERS)
    orders = gen_orders(N_ORDERS, customers, products, employees)
    returns = gen_returns(orders)
    targets = gen_targets(employees)

    date_dim.to_csv(os.path.join(OUT_DIR, "date_dimension.csv"), index=False)
    customers.to_csv(os.path.join(OUT_DIR, "customers.csv"), index=False)
    products.to_csv(os.path.join(OUT_DIR, "products.csv"), index=False)
    employees.to_csv(os.path.join(OUT_DIR, "employees.csv"), index=False)
    orders.to_csv(os.path.join(OUT_DIR, "orders.csv"), index=False)
    returns.to_csv(os.path.join(OUT_DIR, "returns.csv"), index=False)
    targets.to_csv(os.path.join(OUT_DIR, "targets.csv"), index=False)

    log.info("Raw dataset generation complete.")
    log.info(f"  customers: {len(customers):,}")
    log.info(f"  products: {len(products):,}")
    log.info(f"  employees: {len(employees):,}")
    log.info(f"  orders: {len(orders):,}")
    log.info(f"  returns: {len(returns):,}")
    log.info(f"  targets: {len(targets):,}")
    log.info(f"  date_dimension: {len(date_dim):,}")


if __name__ == "__main__":
    main()
