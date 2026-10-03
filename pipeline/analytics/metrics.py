from __future__ import annotations

import pandas as pd


def commerce_kpis(orders: pd.DataFrame) -> dict[str, float]:
    completed = orders.loc[orders["status"] == "completed"]
    revenue = float(completed["revenue"].sum())
    order_count = int(len(completed))
    customer_orders = completed.groupby("customer_id")["order_id"].nunique()
    return {
        "revenue": revenue,
        "orders": order_count,
        "average_order_value": revenue / order_count if order_count else 0.0,
        "repeat_purchase_rate": float((customer_orders > 1).mean()) if len(customer_orders) else 0.0,
    }


def campaign_metrics(spend: float, revenue: float, customers: int,
                     clicks: int, conversions: int) -> dict[str, float]:
    return {
        "roas": revenue / spend if spend else 0.0,
        "customer_acquisition_cost": spend / customers if customers else 0.0,
        "conversion_rate": conversions / clicks if clicks else 0.0,
    }
