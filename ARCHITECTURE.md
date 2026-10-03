# Architecture

## Scope

Creative Commerce Intelligence Pipeline is a local production-style reference implementation for batch analytics engineering. It separates source generation, data contracts, ingestion, warehouse loading, SQL modeling, orchestration, and presentation so each boundary can be tested independently.

## Source and ingestion layer

Six deterministic CSV feeds represent customers, products, orders, order items, campaigns, and website events. Discovery maps canonical filename prefixes to source contracts. Each file receives a SHA-256 hash and stable batch ID. The loader records batch lineage and prevents the same source/hash pair from succeeding twice.

Raw rows gain `_batch_id`, `_ingested_at`, and `_source_file`. Loads are transactional per file. New batches append only previously unseen source primary keys; PostgreSQL enforces unique batch metadata. The metadata table exposes source/valid/quarantined/loaded counts and load status for each hash. Missing files, missing columns, malformed rows, and database failures surface as explicit errors.

## Validation and quarantine

Pydantic source schemas implement field and cross-field rules before warehouse loading. Duplicate source keys and invalid records are excluded from the valid frame but retained as CSV quarantine records with a reason. A JSON quality report makes row counts and failure categories inspectable without querying the warehouse.

Quarantine is not an error sink: operators can repair a source and submit a changed file, which produces a new hash and batch. No invalid row is silently deleted.

## Warehouse and dbt

PostgreSQL is the primary warehouse. Python creates the `raw` schema and ingestion metadata; dbt owns the downstream layers:

- `staging`: typed, consistently named source views
- `intermediate`: reusable attribution, order-sequence, LTV, and product calculations
- `analytics`: dimensions, facts, and business-facing marts

A custom dbt schema macro creates these exact schemas rather than target-prefixed variants. Relationships and domain tests protect model contracts. `mart_revenue_daily` is incremental by order date; late rows for the latest loaded date are rebuilt through the model's unique key.

## Metric definitions

- Revenue: sum of completed order revenue
- AOV: completed revenue / completed orders
- ROAS: campaign-attributed revenue / spend
- CAC: spend / distinct customers with attributed completed orders
- Repeat purchase rate: customers with more than one completed order / customers with a completed order
- Observed customer value: cumulative completed revenue per customer; not predicted LTV
- Funnel rates: session-level presence of view, cart, and purchase events
- Cohort retention: active purchasing customers by months since first completed purchase / first-purchase cohort size

Attribution uses the final campaign ID supplied on an order. Orders without one are grouped into `DIRECT_OR_UNKNOWN`; no synthetic multi-touch claim or inferred lookback window is made.

These are analytical conventions for synthetic data, not claims about a real company.

## Orchestration

Prefect tasks wrap ingestion/validation, transformation, loading, and dbt execution. Retry behavior is limited to I/O tasks where a transient failure is plausible. A flow summary records processed files, inserted rows, and skipped duplicate batches. Logs cover pipeline start, validation counts, loads, dbt execution, and completion.

## Runtime topology

Docker Compose supplies PostgreSQL 16 and an optional dashboard container. Environment variables configure connections; no production secrets are committed. The Streamlit application reads only analytics marts. GitHub Actions runs fast Python tests and a separate PostgreSQL/dbt integration job.

## Failure and recovery behavior

- Missing or structurally invalid source: fail before loading that batch.
- Invalid rows: quarantine with reasons; load the valid subset.
- Identical batch: return `duplicate_skipped` without modifying raw data.
- Existing business key in a changed batch: ignore the existing key and append new keys.
- Database unavailable: SQLAlchemy raises the connection error and the flow fails.
- dbt test failure: `dbt build` exits nonzero and the flow fails.

## Design decisions

Pandas is restricted to boundary work—CSV parsing, row contract validation, and bulk loading. Business transformations live in SQL/dbt so warehouse logic is inspectable and portable. SQLAlchemy handles database connectivity and metadata without hiding SQL modeling. SQLite is used only for quick loader tests; PostgreSQL is required for dbt models and the full local run.
