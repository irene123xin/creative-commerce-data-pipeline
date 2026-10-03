from pathlib import Path

import pytest

from pipeline.synthetic import generate_dataset


@pytest.fixture
def small_dataset(tmp_path: Path):
    raw = tmp_path / "raw"
    frames = generate_dataset(raw, customers=30, products=12, orders=60, events=300, seed=7)
    return raw, frames

