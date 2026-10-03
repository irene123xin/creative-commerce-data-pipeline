import json

import pandas as pd

from pipeline.ingestion.base import ingest_csv


def test_ingestion_writes_quarantine_and_report(tmp_path):
    source = tmp_path / "products.csv"
    pd.DataFrame([
        {"product_id": "P0001", "product_name": "Good", "category": "Home", "price": 12, "cost": 5},
        {"product_id": "P0002", "product_name": "Bad", "category": "Home", "price": 2, "cost": 5},
    ]).to_csv(source, index=False)
    batch = ingest_csv("products", source, tmp_path / "quarantine", tmp_path / "reports")
    assert len(batch.frame) == 1 and len(batch.quarantined) == 1
    report_path = next((tmp_path / "reports").glob("*_quality.json"))
    assert json.loads(report_path.read_text())["invalid_records"] == 1


def test_missing_source_fails_clearly(tmp_path):
    try:
        ingest_csv("orders", tmp_path / "missing.csv", tmp_path, tmp_path)
    except FileNotFoundError as exc:
        assert "Missing source file" in str(exc)
    else:
        raise AssertionError("missing file should fail")

