from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.orchestration.flows import commerce_pipeline
from pipeline.synthetic import generate_daily_batch, generate_dataset
from pipeline.utils.config import settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true", help="Generate an initial synthetic source set")
    parser.add_argument("--daily", type=date.fromisoformat, help="Generate and load an incremental daily batch")
    parser.add_argument("--skip-dbt", action="store_true", help="Load raw data without running dbt")
    args = parser.parse_args()
    if args.generate:
        generate_dataset(settings.raw_data_dir)
    if args.daily:
        generate_daily_batch(settings.raw_data_dir, args.daily)
    commerce_pipeline(execute_dbt=not args.skip_dbt)


if __name__ == "__main__":
    main()

