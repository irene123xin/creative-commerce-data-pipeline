import pandas as pd
from sqlalchemy import create_engine, text

from pipeline.ingestion.base import ingest_csv
from pipeline.loading.postgres import WarehouseLoader


def test_incremental_loader_skips_identical_batch(tmp_path, small_dataset):
    raw, _ = small_dataset
    batch = ingest_csv("customers", raw / "customers.csv", tmp_path / "q", tmp_path / "reports")
    engine = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}")
    loader = WarehouseLoader(engine=engine)
    first = loader.load(batch)
    second = loader.load(batch)
    with engine.connect() as connection:
        count = connection.execute(text("select count(*) from raw_customers")).scalar_one()
    assert first.records_loaded == 30
    assert second.status == "duplicate_skipped" and second.records_loaded == 0
    assert count == 30


def test_changed_batch_with_only_existing_keys_loads_zero(tmp_path, small_dataset):
    raw, frames = small_dataset
    engine = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}")
    loader = WarehouseLoader(engine=engine)
    first = ingest_csv("customers", raw / "customers.csv", tmp_path / "q", tmp_path / "reports")
    loader.load(first)

    changed_path = raw / "customers_changed.csv"
    changed = frames["customers"].copy()
    changed.loc[0, "region"] = "West" if changed.loc[0, "region"] != "West" else "South"
    changed.to_csv(changed_path, index=False)
    result = loader.load(ingest_csv("customers", changed_path, tmp_path / "q", tmp_path / "reports"))

    assert result.records_loaded == 0
    assert result.existing_keys_skipped == len(changed)
    assert result.reconciled


def test_changed_batch_with_overlap_loads_only_new_keys(tmp_path, small_dataset):
    raw, frames = small_dataset
    engine = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}")
    loader = WarehouseLoader(engine=engine)
    loader.load(ingest_csv("customers", raw / "customers.csv", tmp_path / "q", tmp_path / "reports"))

    overlap = frames["customers"].head(2).copy()
    new_row = overlap.iloc[0].copy()
    new_row["customer_id"] = "C999999"
    changed = pd.concat([overlap, new_row.to_frame().T], ignore_index=True)
    changed_path = raw / "customers_increment.csv"
    changed.to_csv(changed_path, index=False)
    result = loader.load(ingest_csv("customers", changed_path, tmp_path / "q", tmp_path / "reports"))

    with engine.connect() as connection:
        count = connection.execute(text("select count(*) from raw_customers")).scalar_one()
        metadata = connection.execute(text(
            "select valid_row_count, loaded_row_count from ingestion_batches "
            "where source_file = 'customers_increment.csv'"
        )).one()
    assert result.records_loaded == 1 and result.existing_keys_skipped == 2
    assert result.reconciled and count == 31
    assert metadata == (3, 1)
