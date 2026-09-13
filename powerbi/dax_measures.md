# DAX Measures

Assumes a fact table `orders` (with `order_status <> "Cancelled"` filtered via
a measure-level `CALCULATE` or a filtered view) and a marked date table
`date_dimension` joined on `orders[order_date] = date_dimension[date]`.

```DAX
Total Revenue =
CALCULATE(SUM(orders[revenue]), orders[order_status] <> "Cancelled")

Total Profit =
CALCULATE(SUM(orders[profit]), orders[order_status] <> "Cancelled")

Profit Margin % =
DIVIDE([Total Profit], [Total Revenue], 0) * 100

Total Orders =
CALCULATE(DISTINCTCOUNT(orders[order_id]), orders[order_status] <> "Cancelled")

Total Customers =
DISTINCTCOUNT(customers[customer_id])

Average Order Value =
DIVIDE([Total Revenue], [Total Orders], 0)

Revenue Growth (YoY) =
VAR CurrentRevenue = [Total Revenue]
VAR PriorYearRevenue =
    CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(date_dimension[date]))
RETURN
    DIVIDE(CurrentRevenue - PriorYearRevenue, PriorYearRevenue, 0) * 100

YoY Revenue =
CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(date_dimension[date]))

MoM Revenue =
CALCULATE([Total Revenue], DATEADD(date_dimension[date], -1, MONTH))

Target Achievement % =
VAR TotalTarget = SUM(targets[target_amount])
RETURN
    DIVIDE([Total Revenue], TotalTarget, 0) * 100

Customer Retention % =
-- Customers active in the current period who were also active in the prior period
VAR CurrentCustomers =
    CALCULATETABLE(VALUES(orders[customer_id]), orders[order_status] <> "Cancelled")
VAR PriorCustomers =
    CALCULATETABLE(
        VALUES(orders[customer_id]),
        orders[order_status] <> "Cancelled",
        DATEADD(date_dimension[date], -1, MONTH)
    )
RETURN
    DIVIDE(COUNTROWS(INTERSECT(CurrentCustomers, PriorCustomers)), COUNTROWS(CurrentCustomers), 0) * 100

Customer Churn % =
DIVIDE(
    CALCULATE(COUNTROWS(customer_churn_predictions), customer_churn_predictions[churn_prediction] = 1),
    COUNTROWS(customer_churn_predictions),
    0
) * 100

Revenue per Customer =
DIVIDE([Total Revenue], [Total Customers], 0)
```

## Calculated columns

```DAX
-- On orders: convenient month-year label for slicers/axes
Order Month = FORMAT(orders[order_date], "MMM YYYY")

-- On products: margin band for grouping
Margin Band =
VAR M = DIVIDE(products[selling_price] - products[unit_cost], products[selling_price], 0) * 100
RETURN
    SWITCH(TRUE(),
        M >= 40, "High Margin",
        M >= 20, "Medium Margin",
        "Low Margin"
    )
```
