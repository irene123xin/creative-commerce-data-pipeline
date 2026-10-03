from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
from pydantic import ValidationError

from pipeline.validation.schemas import SCHEMAS

RULE_NAMES = {
    ("products", "value_error"): "PRODUCT_COST_GT_PRICE",
    ("campaigns", "value_error"): "CAMPAIGN_FUNNEL_INCONSISTENT",
    ("orders", "greater_than_equal"): "ORDER_NEGATIVE_REVENUE",
    ("website_events", "literal_error"): "INVALID_EVENT_TYPE",
}


@dataclass
class QualityReport:
    source: str
    records_processed: int
    valid_records: int
    invalid_records: int
    duplicates: int
    missing_values: int
    validation_failures: dict[str, int]


def validate_frame(source: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, QualityReport]:
    if source not in SCHEMAS:
        raise ValueError(f"Unsupported source: {source}")
    schema, primary_key = SCHEMAS[source]
    expected = set(schema.model_fields)
    missing_columns = expected - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{source} missing columns: {sorted(missing_columns)}")

    duplicate_mask = frame.duplicated(primary_key, keep="first")
    failures: dict[str, int] = {}
    valid_indices: list[int] = []
    invalid_reasons: dict[int, str] = {}
    for index, row in frame.iterrows():
        if duplicate_mask.loc[index]:
            invalid_reasons[index] = "DUPLICATE_PRIMARY_KEY"
            failures["DUPLICATE_PRIMARY_KEY"] = failures.get("DUPLICATE_PRIMARY_KEY", 0) + 1
            continue
        try:
            values = {key: (None if pd.isna(value) else value)
                      for key, value in row[list(expected)].to_dict().items()}
            schema.model_validate(values)
            valid_indices.append(index)
        except ValidationError as exc:
            error = exc.errors()[0]
            location = error.get("loc") or ("RECORD",)
            field = str(location[0]).upper()
            reason = RULE_NAMES.get(
                (source, error["type"]),
                f"{source[:-1].upper()}_{field}_{error['type'].upper()}",
            )
            invalid_reasons[index] = reason
            failures[reason] = failures.get(reason, 0) + 1

    valid = frame.loc[valid_indices].copy()
    invalid = frame.loc[list(invalid_reasons)].copy()
    if not invalid.empty:
        invalid["quarantine_reason"] = invalid.index.map(invalid_reasons)
    report = QualityReport(source, len(frame), len(valid), len(invalid), int(duplicate_mask.sum()),
                           int(frame.isna().sum().sum()), failures)
    return valid.reset_index(drop=True), invalid.reset_index(drop=True), report


def report_dict(report: QualityReport) -> dict:
    return asdict(report)
