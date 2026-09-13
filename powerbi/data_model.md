# Power BI Data Model

## Star schema

```
                 ┌───────────────┐
                 │ date_dimension │  (mark as Date Table)
                 └───────┬────────┘
                         │ date
                         │
┌───────────┐     ┌──────▼──────┐     ┌───────────┐
│ customers │────►│   orders    │◄────│  products │
└───────────┘     │  (fact)     │     └───────────┘
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  employees  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   targets   │
                   └─────────────┘

┌───────────┐     ┌────────────────────────────┐
│  orders   │────►│          returns           │
└───────────┘     └────────────────────────────┘

┌───────────┐     ┌────────────────────────────┐
│ customers │────►│ customer_churn_predictions │
└───────────┘     └────────────────────────────┘
```

## Relationship cardinality

| From | To | Cardinality | Cross-filter |
|---|---|---|---|
| orders[customer_id] | customers[customer_id] | many-to-one | Single |
| orders[product_id] | products[product_id] | many-to-one | Single |
| orders[employee_id] | employees[employee_id] | many-to-one | Single |
| orders[order_date] | date_dimension[date] | many-to-one | Single |
| returns[order_id] | orders[order_id] | many-to-one | Single |
| targets[employee_id] | employees[employee_id] | many-to-one | Single |
| customer_churn_predictions[customer_id] | customers[customer_id] | one-to-one | Single |

## Why a star schema

`orders` is the single fact table at the grain of one row per order line
item. All dimensions (who, what, when, whom-sold-by) hang off it with
single-direction filtering, which keeps DAX measures predictable and avoids
ambiguous filter propagation — critical once you add Target Achievement and
retention measures that span two time periods.
