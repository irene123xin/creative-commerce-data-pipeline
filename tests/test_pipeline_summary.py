from datetime import datetime, timezone

from pipeline.loading.postgres import LoadResult
from pipeline.orchestration.summary import build_run_summary, write_run_summary


def test_pipeline_summary_reconciles_counts_and_writes_json(tmp_path):
    results = [
        LoadResult("orders", "batch-1", "success", 8, 10, 9, 1, 1, True),
        LoadResult("customers", "batch-2", "duplicate_skipped", 0, 3, 3, 0, 3, True),
    ]
    summary = build_run_summary("run-1", datetime.now(timezone.utc), results, "passed")
    path = write_run_summary(summary, tmp_path)

    assert summary["records_received"] == 13
    assert summary["records_loaded"] == 8
    assert summary["records_quarantined"] == 1
    assert summary["batches_skipped"] == 1
    assert summary["quality_status"] == "passed"
    assert path.exists() and '"run_id": "run-1"' in path.read_text()
