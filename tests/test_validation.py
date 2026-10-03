import pandas as pd

from pipeline.validation.quality_checks import validate_frame


def test_validation_quarantines_bad_and_duplicate_products():
    frame = pd.DataFrame([
        {"product_id": "P0001", "product_name": "Valid", "category": "Home", "price": 20, "cost": 10},
        {"product_id": "P0001", "product_name": "Duplicate", "category": "Home", "price": 20, "cost": 10},
        {"product_id": "P0002", "product_name": "Bad margin", "category": "Home", "price": 5, "cost": 10},
    ])
    valid, invalid, report = validate_frame("products", frame)
    assert len(valid) == 1
    assert len(invalid) == 2
    assert report.duplicates == 1
    assert "quarantine_reason" in invalid
    assert set(invalid["quarantine_reason"]) == {"DUPLICATE_PRIMARY_KEY", "PRODUCT_COST_GT_PRICE"}


def test_campaign_funnel_validation():
    frame = pd.DataFrame([{"campaign_id": "M0001", "campaign_name": "Bad", "channel": "email",
        "spend": 10, "impressions": 100, "clicks": 120, "conversions": 2,
        "start_date": "2025-01-01", "end_date": "2025-01-02"}])
    valid, invalid, report = validate_frame("campaigns", frame)
    assert valid.empty and len(invalid) == 1 and report.invalid_records == 1
    assert invalid.iloc[0]["quarantine_reason"] == "CAMPAIGN_FUNNEL_INCONSISTENT"
