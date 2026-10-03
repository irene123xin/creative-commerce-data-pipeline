from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

CHANNELS = ["organic", "paid_search", "paid_social", "email", "referral"]
CATEGORIES = ["Home", "Accessories", "Stationery", "Wellness", "Apparel"]


def generate_dataset(output_dir: Path, customers: int = 2000, products: int = 100,
                     orders: int = 5500, events: int = 45000, seed: int = 42,
                     start_date: date = date(2025, 1, 1), id_offset: int = 0) -> dict[str, pd.DataFrame]:
    """Generate relational, deterministic commerce data without personal information."""
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    customer_ids = np.array([f"C{id_offset + i:06d}" for i in range(1, customers + 1)])
    product_ids = np.array([f"P{id_offset + i:04d}" for i in range(1, products + 1)])
    campaign_ids = np.array([f"M{id_offset + i:04d}" for i in range(1, 41)])
    channels = rng.choice(CHANNELS, customers, p=[.28, .23, .22, .17, .10])
    signup_offsets = rng.integers(0, 365, customers)
    customer_frame = pd.DataFrame({
        "customer_id": customer_ids,
        "signup_date": [start_date + timedelta(days=int(value)) for value in signup_offsets],
        "acquisition_channel": channels,
        "region": rng.choice(["Northeast", "South", "Midwest", "West"], customers),
        "age_group": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], customers,
                                p=[.12, .29, .27, .19, .13]),
    })

    category = rng.choice(CATEGORIES, products)
    costs = rng.uniform(4, 70, products).round(2)
    prices = (costs * rng.uniform(1.7, 3.1, products)).round(2)
    product_frame = pd.DataFrame({
        "product_id": product_ids,
        "product_name": [f"{category[i]} Product {i + 1:03d}" for i in range(products)],
        "category": category,
        "price": prices,
        "cost": costs,
    })

    campaign_channels = rng.choice(["paid_search", "paid_social", "email", "affiliate"], 40)
    campaign_starts = rng.integers(0, 330, 40)
    impressions = rng.integers(25_000, 400_000, 40)
    clicks = (impressions * rng.uniform(.008, .055, 40)).astype(int)
    conversions = (clicks * rng.uniform(.015, .09, 40)).astype(int)
    campaign_frame = pd.DataFrame({
        "campaign_id": campaign_ids,
        "campaign_name": [f"{campaign_channels[i].replace('_', ' ').title()} {i + 1:02d}" for i in range(40)],
        "channel": campaign_channels,
        "spend": rng.uniform(800, 18_000, 40).round(2),
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "start_date": [start_date + timedelta(days=int(value)) for value in campaign_starts],
        "end_date": [start_date + timedelta(days=int(value) + 34) for value in campaign_starts],
    })

    weights = rng.pareto(2.3, customers) + .2
    order_customers = rng.choice(customer_ids, orders, p=weights / weights.sum())
    order_dates = [datetime.combine(start_date + timedelta(days=int(value)), datetime.min.time(), tzinfo=timezone.utc)
                   + timedelta(seconds=int(rng.integers(0, 86400))) for value in rng.integers(0, 365, orders)]
    statuses = rng.choice(["completed", "refunded", "cancelled"], orders, p=[.91, .06, .03])
    order_campaigns = rng.choice(np.append(campaign_ids, None), orders,
                                 p=np.append(np.full(40, .55 / 40), .45))
    item_rows = []
    order_rows = []
    item_counter = 1
    price_map = product_frame.set_index("product_id")["price"].to_dict()
    cost_map = product_frame.set_index("product_id")["cost"].to_dict()
    for index in range(orders):
        order_id = f"O{id_offset + index + 1:07d}"
        count = int(rng.integers(1, 5))
        chosen = rng.choice(product_ids, count, replace=False)
        discount = float(rng.choice([0, 0, 0, 5, 10, 15]))
        gross = 0.0
        for product_id in chosen:
            quantity = int(rng.integers(1, 4))
            gross += price_map[product_id] * quantity
            item_rows.append({"order_item_id": f"OI{id_offset + item_counter:08d}", "order_id": order_id,
                              "product_id": product_id, "quantity": quantity,
                              "unit_price": price_map[product_id], "unit_cost": cost_map[product_id]})
            item_counter += 1
        revenue = max(0, gross - discount) if statuses[index] == "completed" else 0
        order_rows.append({"order_id": order_id, "customer_id": order_customers[index],
                           "order_date": order_dates[index].isoformat(), "status": statuses[index],
                           "discount": discount, "revenue": round(revenue, 2),
                           "campaign_id": order_campaigns[index]})
    order_frame = pd.DataFrame(order_rows)
    item_frame = pd.DataFrame(item_rows)

    event_rows = []
    event_types = rng.choice(["session_start", "product_view", "add_to_cart", "purchase"], events,
                             p=[.37, .43, .15, .05])
    sessions = np.array([f"S{i:08d}" for i in rng.integers(1, events // 3 + 1, events)])
    for index, event_type in enumerate(event_types):
        known = rng.random() < .62
        event_rows.append({
            "event_id": f"E{id_offset + index + 1:09d}",
            "customer_id": rng.choice(customer_ids) if known else None,
            "anonymous_session_id": sessions[index],
            "timestamp": (datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
                          + timedelta(seconds=int(rng.integers(0, 365 * 86400)))).isoformat(),
            "event_type": event_type,
            "product_id": rng.choice(product_ids) if event_type in {"product_view", "add_to_cart", "purchase"} else None,
            "campaign_id": rng.choice(campaign_ids) if rng.random() < .48 else None,
        })
    event_frame = pd.DataFrame(event_rows)

    frames = {"customers": customer_frame, "products": product_frame, "orders": order_frame,
              "order_items": item_frame, "campaigns": campaign_frame,
              "website_events": event_frame}
    for name, frame in frames.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    return frames


def generate_daily_batch(output_dir: Path, batch_date: date, seed: int = 99,
                         customers: int = 40, orders: int = 160, events: int = 1200) -> dict[str, pd.DataFrame]:
    """Generate a small independently keyed batch suitable for incremental loading."""
    offset = (batch_date - date(2025, 1, 1)).days * 100_000
    suffix = batch_date.strftime("%Y%m%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Generate away from the source directory so a daily batch can never
    # overwrite the initial full-load files with the same canonical names.
    with TemporaryDirectory(prefix="commerce-batch-") as temporary_dir:
        frames = generate_dataset(Path(temporary_dir), customers=customers, products=20,
                                  orders=orders, events=events, seed=seed,
                                  start_date=batch_date, id_offset=offset)
        for name in frames:
            frames[name].to_csv(output_dir / f"{name}_{suffix}.csv", index=False)
    return frames
