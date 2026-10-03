from datetime import date

from pipeline.synthetic import generate_daily_batch, generate_dataset


def test_synthetic_data_is_relational_and_deterministic(tmp_path, small_dataset):
    raw, frames = small_dataset
    assert set(frames) == {"customers", "products", "orders", "order_items", "campaigns", "website_events"}
    assert len(frames["order_items"]) >= len(frames["orders"])
    assert set(frames["orders"]["customer_id"]) <= set(frames["customers"]["customer_id"])
    assert (raw / "orders.csv").exists()


def test_daily_batch_preserves_initial_files(tmp_path):
    raw = tmp_path / "raw"
    generate_dataset(raw, customers=10, products=5, orders=15, events=40, seed=1)
    initial_contents = (raw / "customers.csv").read_bytes()

    generate_daily_batch(raw, date(2026, 1, 2), customers=3, orders=4, events=8)

    assert (raw / "customers.csv").read_bytes() == initial_contents
    assert (raw / "customers_20260102.csv").exists()
