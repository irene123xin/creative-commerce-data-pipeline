from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://commerce:commerce@localhost:5432/commerce",
    )
    raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", ROOT / "data" / "raw"))
    processed_data_dir: Path = Path(os.getenv("PROCESSED_DATA_DIR", ROOT / "data" / "processed"))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", ROOT / "outputs"))
    dbt_dir: Path = ROOT / "dbt"


settings = Settings()

