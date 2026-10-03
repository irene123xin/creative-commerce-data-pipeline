from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.synthetic import generate_daily_batch, generate_dataset
from pipeline.utils.config import settings
from pipeline.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily", type=date.fromisoformat, help="Generate an incremental batch for YYYY-MM-DD")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.daily:
        frames = generate_daily_batch(settings.raw_data_dir, args.daily, args.seed)
        logger.info("Generated daily batch %s with %s records", args.daily,
                    sum(len(frame) for frame in frames.values()))
    else:
        frames = generate_dataset(settings.raw_data_dir, seed=args.seed)
        logger.info("Generated initial dataset with %s records", sum(len(frame) for frame in frames.values()))


if __name__ == "__main__":
    main()
