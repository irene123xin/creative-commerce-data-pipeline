from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_run_summary(run_id: str, started_at: datetime, results: list,
                      dbt_status: str, overall_status: str = "success",
                      failure_reason: str | None = None) -> dict:
    finished_at = datetime.now(timezone.utc)
    reconciled = all(result.reconciled for result in results)
    return {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "datasets_processed": len(results),
        "records_received": sum(result.records_received for result in results),
        "records_valid": sum(result.records_valid for result in results),
        "records_quarantined": sum(result.records_quarantined for result in results),
        "records_loaded": sum(result.records_loaded for result in results),
        "existing_keys_skipped": sum(result.existing_keys_skipped for result in results),
        "batches_skipped": sum(result.status == "duplicate_skipped" for result in results),
        "dbt_status": dbt_status,
        "quality_status": "passed" if reconciled else "failed",
        "overall_status": overall_status,
        "failure_reason": failure_reason,
    }


def write_run_summary(summary: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"pipeline_run_{summary['run_id']}.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path
