"""Verify release integrity and reproduce annual scores from packaged values."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.index.aggregator import ICIVAggregator
from iciv.processing.transformers.normalizer import MinMaxNormalizer

def verify(path):
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf8"))
    errors = []
    for name, meta in manifest["files"].items():
        target = path / name
        if not target.is_file():
            errors.append(f"missing: {name}"); continue
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta["sha256"] and hashlib.sha256(raw.replace(b"\r\n",b"\n")).hexdigest() != meta.get("canonical_lf_sha256"):
            errors.append(f"hash mismatch: {name}")
    transformed = pd.read_csv(path / "iciv_transformado.csv")
    norm = pd.read_csv(path / "iciv_normalizado.csv")
    reproduced_norm = MinMaxNormalizer().fit_transform(transformed)
    if not np.allclose(reproduced_norm[norm.columns].to_numpy(float), norm.to_numpy(float), equal_nan=True):
        errors.append("normalization does not reproduce")
    scores = ICIVAggregator().compute(norm)
    published = pd.read_csv(path / "iciv_scores_ahp.csv")
    for col in ("iciv_score", "cobertura_pct", "cobertura_observada_pct"):
        if not np.allclose(scores[col], published[col], equal_nan=True):
            errors.append(f"annual {col} does not reproduce")
    long = pd.read_csv(path / "iciv_dataset_largo.csv")
    wide = pd.read_csv(path / "iciv_dataset_wide.csv").set_index("year")
    for variable, group in long.groupby("variable"):
        if not np.allclose(group.set_index("year")["valor_crudo"].reindex(wide.index), wide[variable],equal_nan=True):
            errors.append(f"original value mismatch: {variable}")
    if long["imputado_por_proyecto"].fillna(True).any():
        errors.append("imputed or unidentified observations")
    if errors: raise RuntimeError("\n".join(errors))
    print(f"PASS: {len(manifest['files'])} hashes; normalización, AHP, cobertura y valores originales reproducidos.")
    return True

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[1]/"data/releases/latest")
    verify(parser.parse_args().release)
