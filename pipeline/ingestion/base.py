from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.utils.logging import get_logger
from pipeline.validation.quality_checks import QualityReport, report_dict, validate_frame

logger = get_logger(__name__)


@dataclass
class IngestedBatch:
    source: str
    path: Path
    batch_id: str
    file_hash: str
    frame: pd.DataFrame
    quarantined: pd.DataFrame
    quality: QualityReport


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ingest_csv(source: str, path: Path, quarantine_dir: Path,
               report_dir: Path) -> IngestedBatch:
    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")
    file_hash = file_sha256(path)
    batch_id = f"{source}-{file_hash[:12]}"
    logger.info("Ingesting %s from %s", source, path.name)
    frame = pd.read_csv(path)
    valid, invalid, report = validate_frame(source, frame)
    valid["_batch_id"] = batch_id
    valid["_ingested_at"] = datetime.now(timezone.utc)
    valid["_source_file"] = path.name
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    if not invalid.empty:
        invalid.assign(_batch_id=batch_id).to_csv(
            quarantine_dir / f"{path.stem}_{batch_id}_quarantine.csv", index=False)
    (report_dir / f"{batch_id}_quality.json").write_text(
        json.dumps(report_dict(report), indent=2), encoding="utf-8")
    logger.info("Validated %s: %d valid, %d quarantined", source,
                report.valid_records, report.invalid_records)
    return IngestedBatch(source, path, batch_id, file_hash, valid, invalid, report)


def discover_files(raw_dir: Path) -> list[tuple[str, Path]]:
    sources = ["customers", "products", "orders", "order_items", "campaigns", "website_events"]
    found = []
    for source in sources:
        found.extend((source, path) for path in sorted(raw_dir.glob(f"{source}*.csv")))
    return found

