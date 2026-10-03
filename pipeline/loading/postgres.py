from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import (JSON, Column, DateTime, Integer, MetaData, String, Table,
                        UniqueConstraint, create_engine, inspect, select)
from sqlalchemy.engine import Engine

from pipeline.ingestion.base import IngestedBatch
from pipeline.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LoadResult:
    source: str
    batch_id: str
    status: str
    records_loaded: int
    records_received: int
    records_valid: int
    records_quarantined: int
    existing_keys_skipped: int
    reconciled: bool


class WarehouseLoader:
    """Idempotent raw loader keyed by file hash and source primary keys."""

    def __init__(self, database_url: str | None = None, engine: Engine | None = None):
        if engine is None and not database_url:
            raise ValueError("database_url or engine is required")
        self.engine = engine or create_engine(database_url, future=True)
        self.schema = "raw" if self.engine.dialect.name == "postgresql" else None
        self.metadata = MetaData(schema=self.schema)
        self.ingestion_batches = Table(
            "ingestion_batches", self.metadata,
            Column("batch_id", String(80), primary_key=True),
            Column("source", String(40), nullable=False),
            Column("source_type", String(20), nullable=False),
            Column("file_hash", String(64), nullable=False),
            Column("source_file", String(255), nullable=False),
            Column("ingested_at", DateTime(timezone=True), nullable=False),
            Column("source_row_count", Integer, nullable=False),
            Column("valid_row_count", Integer, nullable=False),
            Column("quarantined_row_count", Integer, nullable=False),
            Column("loaded_row_count", Integer, nullable=False),
            Column("status", String(20), nullable=False),
            Column("failure_reason", String(500), nullable=True),
            Column("quality_report", JSON, nullable=False),
            UniqueConstraint("source", "file_hash", name="uq_ingestion_source_hash"),
        )

    def initialize(self) -> None:
        if self.schema:
            with self.engine.begin() as connection:
                connection.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS raw")
        self.metadata.create_all(self.engine)

    def already_loaded(self, source: str, file_hash: str) -> bool:
        self.initialize()
        statement = select(self.ingestion_batches.c.batch_id).where(
            self.ingestion_batches.c.source == source,
            self.ingestion_batches.c.file_hash == file_hash,
            self.ingestion_batches.c.status == "success",
        )
        with self.engine.connect() as connection:
            return connection.execute(statement).first() is not None

    def table_name(self, source: str) -> str:
        return source if self.schema else f"raw_{source}"

    def load(self, batch: IngestedBatch) -> LoadResult:
        self.initialize()
        if self.already_loaded(batch.source, batch.file_hash):
            logger.info("Skipping duplicate batch %s", batch.batch_id)
            return LoadResult(batch.source, batch.batch_id, "duplicate_skipped", 0,
                              batch.quality.records_processed, batch.quality.valid_records,
                              batch.quality.invalid_records, batch.quality.valid_records, True)
        table_name = self.table_name(batch.source)
        frame = batch.frame.copy()
        primary_key = {"customers": "customer_id", "products": "product_id", "orders": "order_id",
                       "order_items": "order_item_id", "campaigns": "campaign_id",
                       "website_events": "event_id"}[batch.source]
        existing_keys_skipped = 0
        with self.engine.begin() as connection:
            if inspect(connection).has_table(table_name, schema=self.schema):
                existing = set(pd.read_sql(select(Table(table_name, MetaData(), autoload_with=connection,
                                                        schema=self.schema).c[primary_key]), connection)[primary_key])
                existing_mask = frame[primary_key].isin(existing)
                existing_keys_skipped = int(existing_mask.sum())
                frame = frame[~existing_mask]
            if not frame.empty:
                frame.to_sql(table_name, connection, schema=self.schema, if_exists="append",
                             index=False, method="multi", chunksize=1000)
            connection.execute(self.ingestion_batches.insert().values(
                batch_id=batch.batch_id, source=batch.source, source_type="csv", file_hash=batch.file_hash,
                source_file=batch.path.name, ingested_at=datetime.now(timezone.utc),
                source_row_count=batch.quality.records_processed,
                valid_row_count=batch.quality.valid_records,
                quarantined_row_count=batch.quality.invalid_records,
                loaded_row_count=len(frame), status="success", failure_reason=None,
                quality_report={"processed": batch.quality.records_processed,
                                "valid": batch.quality.valid_records,
                                "invalid": batch.quality.invalid_records,
                                "duplicates": batch.quality.duplicates},
            ))
        logger.info("Loaded %d new %s rows", len(frame), batch.source)
        reconciled = batch.quality.valid_records == len(frame) + existing_keys_skipped
        return LoadResult(batch.source, batch.batch_id, "success", len(frame),
                          batch.quality.records_processed, batch.quality.valid_records,
                          batch.quality.invalid_records, existing_keys_skipped, reconciled)
