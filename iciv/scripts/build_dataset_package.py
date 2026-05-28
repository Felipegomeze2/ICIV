"""Build the ICIV auditable dataset package from processed artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from iciv.config import settings  # noqa: E402
from iciv.data.dataset_package import build_dataset_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id", default="latest")
    args = parser.parse_args()

    raw_path = settings.paths.data_processed / "iciv_normalizado.csv"
    # The package needs the annual raw panel. Rebuild from wide if main.py has
    # already run; otherwise ask the user to run the pipeline first.
    wide_path = settings.paths.data_processed / "iciv_dataset_wide.csv"
    long_path = settings.paths.data_processed / "iciv_dataset_largo.csv"

    if not wide_path.exists() or not long_path.exists():
        raise FileNotFoundError(
            "Missing processed dataset files. Run: python main.py --no-fetch --no-open"
        )

    if not raw_path.exists():
        raise FileNotFoundError(
            "Missing iciv_normalizado.csv. Run: python main.py --no-fetch --no-open"
        )

    # For standalone rebuilds, annual coverage is computed from the wide public
    # dataset. main.py passes the richer raw panel directly.
    df_wide = pd.read_csv(wide_path).rename(columns={"year": "año"})
    result = build_dataset_package(df_wide, wide_path, long_path, settings, args.release_id)
    print(f"Dataset package: {result.release_dir}")
    print(f"Manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
