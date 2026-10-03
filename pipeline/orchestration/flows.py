from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from prefect import flow, task

from pipeline.ingestion.base import discover_files, ingest_csv
from pipeline.loading.postgres import WarehouseLoader
from pipeline.orchestration.summary import build_run_summary, write_run_summary
from pipeline.transformation.clean_customers import clean_customers
from pipeline.transformation.clean_orders import clean_orders
from pipeline.transformation.normalize_campaigns import normalize_campaigns
from pipeline.utils.config import settings
from pipeline.utils.logging import get_logger

logger = get_logger(__name__)


@task(retries=2, retry_delay_seconds=2)
def ingest_and_validate(source: str, path: Path):
    return ingest_csv(source, path, settings.processed_data_dir / "quarantine", settings.output_dir)


@task
def transform_batch(batch):
    if batch.source == "orders":
        batch.frame = clean_orders(batch.frame)
    elif batch.source == "customers":
        batch.frame = clean_customers(batch.frame)
    elif batch.source == "campaigns":
        batch.frame = normalize_campaigns(batch.frame)
    return batch


@task(retries=2, retry_delay_seconds=3)
def load_batch(batch, database_url: str):
    return WarehouseLoader(database_url=database_url).load(batch)


@task
def run_dbt(command: str = "build") -> None:
    environment = os.environ.copy()
    environment.setdefault("DBT_PROFILES_DIR", str(settings.dbt_dir))
    logger.info("Running dbt %s", command)
    subprocess.run(["dbt", command, "--project-dir", str(settings.dbt_dir),
                    "--profiles-dir", str(settings.dbt_dir)], check=True, env=environment)


@flow(name="creative-commerce-pipeline", log_prints=False)
def commerce_pipeline(database_url: str = settings.database_url, execute_dbt: bool = True) -> dict:
    run_id = uuid4().hex[:12]
    started_at = datetime.now(timezone.utc)
    logger.info("pipeline_started run_id=%s", run_id)
    results = []
    dbt_status = "not_run"
    try:
        files = discover_files(settings.raw_data_dir)
        if not files:
            raise FileNotFoundError(f"No source CSV files found in {settings.raw_data_dir}")
        for source, path in files:
            batch = ingest_and_validate(source, path)
            batch = transform_batch(batch)
            results.append(load_batch(batch, database_url))
        if execute_dbt:
            run_dbt("build")
            dbt_status = "passed"
        summary = build_run_summary(run_id, started_at, results, dbt_status)
        write_run_summary(summary, settings.output_dir)
        logger.info("pipeline_completed run_id=%s records_loaded=%d quality_status=%s",
                    run_id, summary["records_loaded"], summary["quality_status"])
        return summary
    except Exception as exc:
        if execute_dbt and results:
            dbt_status = "failed"
        summary = build_run_summary(run_id, started_at, results, dbt_status,
                                    overall_status="failed", failure_reason=str(exc))
        write_run_summary(summary, settings.output_dir)
        logger.exception("pipeline_failed run_id=%s error_category=%s", run_id, type(exc).__name__)
        raise
