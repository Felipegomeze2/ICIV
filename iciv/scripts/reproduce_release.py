"""Reproduce frozen numerical outputs in a new workspace, without fetching data.

The source checkout and the frozen release are never written by this command.
Publication timestamps and HTML are intentionally excluded from numeric comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (
    "iciv_normalizado.csv", "iciv_scores_ahp.csv", "iciv_dataset_largo.csv",
    "iciv_pulse_monthly.csv", "external_validation_summary.csv",
    "robustness_summary.csv", "pulse_forecast_backtest_summary.csv",
)


def compare_csv(expected: Path, actual: Path) -> None:
    """Compare row identity, missingness, labels and numeric values, not bytes."""
    left, right = pd.read_csv(expected), pd.read_csv(actual)
    if left.shape != right.shape or list(left.columns) != list(right.columns):
        raise ValueError(f"Structure differs: {expected.name}")
    for col in left:
        a, b = left[col], right[col]
        if not a.isna().equals(b.isna()):
            raise ValueError(f"Missingness differs: {expected.name}:{col}")
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            same = np.allclose(a, b, rtol=1e-7, atol=1e-8, equal_nan=True)
        else:
            same = a.fillna("").astype(str).equals(b.fillna("").astype(str))
        if not same:
            raise ValueError(f"Values differ: {expected.name}:{col}")


def prepare(release: Path, output: Path) -> Path:
    release, output = release.resolve(), output.resolve()
    if output.exists():
        raise ValueError("--output must name a new directory; existing files are never replaced")
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest.get("code_sha256", {}).items():
        data = (ROOT / name).read_bytes()
        hashes = {hashlib.sha256(data).hexdigest(), hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()}
        if digest not in hashes:
            raise ValueError(f"Code differs from the frozen release: {name}")
    if not (release / "raw").is_dir():
        raise ValueError("This release does not contain frozen raw inputs")
    work = output / "iciv"
    work.mkdir(parents=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    for name in ("src", "scripts", "config", "assets"):
        if (ROOT / name).is_dir():
            shutil.copytree(ROOT / name, work / name, ignore=ignore)
    for name in ("main.py", "pyproject.toml"):
        shutil.copy2(ROOT / name, work / name)
    shutil.copytree(release / "raw", work / "data/raw")
    if (ROOT / "data/sources").exists():
        shutil.copytree(ROOT / "data/sources", work / "data/sources", ignore=ignore)
    # Seed packaged metadata (including audited observation lineage), never mutable raw/.
    processed = work / "data/processed"
    processed.mkdir(parents=True)
    for file in release.iterdir():
        if file.is_file() and file.suffix in (".csv", ".json", ".html", ".md"):
            shutil.copy2(file, processed / file.name)
    for name in ("README.md", "docs"):
        source = ROOT.parent / name
        if source.is_dir():
            shutil.copytree(source, output / name, ignore=ignore)
        elif source.is_file():
            shutil.copy2(source, output / name)
    return work


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    release = args.release.resolve()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts/verify_release.py"), "--release", str(release)], check=True, env=env)
    work = prepare(release, args.output)
    log = args.output.resolve() / "pipeline.log"
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run([sys.executable, str(work / "main.py"), "--no-fetch", "--no-open", "--no-package"],
                       cwd=work.parent, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    checks = []
    for name in OUTPUTS:
        compare_csv(release / name, work / "data/processed" / name)
        checks.append({"file": name, "status": "PASS"})
    report = {"release": release.name, "source_manifest_sha256": hashlib.sha256((release / "manifest.json").read_bytes()).hexdigest(),
              "mode": "isolated_frozen_raw_no_fetch", "comparisons": checks,
              "excluded_from_comparison": "execution timestamps, HTML layout and current-source freshness labels"}
    (args.output.resolve() / "reproduction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"PASS: {len(checks)} numerical outputs reproduced. Report: {args.output.resolve()}")


if __name__ == "__main__":
    main()
