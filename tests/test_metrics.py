import pandas as pd

from pipeline.analytics.metrics import campaign_metrics, commerce_kpis


def test_commerce_metrics():
    orders = pd.DataFrame([
        {"order_id": "1", "customer_id": "A", "status": "completed", "revenue": 100},
        {"order_id": "2", "customer_id": "A", "status": "completed", "revenue": 50},
        {"order_id": "3", "customer_id": "B", "status": "cancelled", "revenue": 0},
    ])
    metrics = commerce_kpis(orders)
    assert metrics == {"revenue": 150.0, "orders": 2, "average_order_value": 75.0,
                       "repeat_purchase_rate": 1.0}


def test_campaign_metrics():
    metrics = campaign_metrics(100, 400, 10, 200, 20)
    assert metrics["roas"] == 4
    assert metrics["customer_acquisition_cost"] == 10
    assert metrics["conversion_rate"] == .1

