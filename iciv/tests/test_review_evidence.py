"""Failure and invariance checks for the working evidence review."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import numpy as np
import pandas as pd
from iciv.analytics.robustness import alternative_normalization, common_basket_changes, VARIABLES
from iciv.data.observation_lineage import verified_metadata

def test_alternative_normalization_preserves_missing_and_direction():
    d = pd.DataFrame({"año": [2020,2021,2022,2023], "inflacion_ipc_imf_pct": [1.,2.,np.nan,3.],
                      "pib_crecimiento_real_pct": [4.,4.,np.nan,4.]})
    for method in ("rank", "winsor05", "minmax"):
        out = alternative_normalization(d, method)
        assert out.loc[0,"inflacion_ipc_imf_pct"] == 100
        assert out.loc[3,"inflacion_ipc_imf_pct"] == 0
        assert pd.isna(out.loc[2,"inflacion_ipc_imf_pct"])
        assert out.pib_crecimiento_real_pct.isna().all()

def test_common_basket_isolates_composition_without_filling():
    d = pd.DataFrame([{**{v:50. for v in VARIABLES}, "año":2020},
                      {**{v:50. for v in VARIABLES}, "año":2021}])
    d.loc[0,"inflacion_ipc_imf_pct"] = 100
    d.loc[1,"inflacion_ipc_imf_pct"] = np.nan
    result = common_basket_changes(d).iloc[0]
    assert result.delta_canasta_comun == 0
    assert result.delta_publicado < 0
    assert result.efecto_composicion_neto == result.delta_publicado
    assert result.n_variables_comunes == len(VARIABLES)-1
    assert pd.isna(d.loc[1,"inflacion_ipc_imf_pct"])

def test_verified_metadata_rejects_changed_raw_and_evidence(tmp_path):
    raw = tmp_path/"raw"; raw.mkdir()
    audit = tmp_path/"sources/audit_20260917"; audit.mkdir(parents=True)
    r = raw/"imf.csv"; r.write_text("year,value\n2026,3\n")
    e = audit/"official.xlsx"; e.write_bytes(b"test evidence")
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    pd.DataFrame([{"variable":"inflacion_ipc_imf_pct", "año":2026, "archivo_origen":"imf.csv",
                   "valor_verificado":3., "raw_sha256":sha(r), "evidencia":e.name,
                   "evidence_sha256":sha(e), "estado_observacion":"estimate",
                   "fecha_publicacion":"2026-04-14", "url":"https://example.test"}]).to_csv(audit/"verified_observations.csv",index=False)
    settings = SimpleNamespace(paths=SimpleNamespace(data_raw=raw))
    assert verified_metadata("inflacion_ipc_imf_pct",2026,3.,settings)["estado_observacion"] == "estimate"
    assert verified_metadata("inflacion_ipc_imf_pct",2026,4.,settings) == {}
    e.write_bytes(b"changed evidence")
    assert verified_metadata("inflacion_ipc_imf_pct",2026,3.,settings) == {}
    e.write_bytes(b"test evidence")
    r.write_text("year,value\n2026,4\n")
    assert verified_metadata("inflacion_ipc_imf_pct",2026,3.,settings) == {}

def test_canonical_hash_accepts_only_line_ending_equivalence(tmp_path):
    from iciv.data.observation_lineage import _current_sha
    path=tmp_path/"raw.csv"
    path.write_bytes(b"year,value\r\n2026,3\r\n")
    original=_current_sha(path)
    canonical=_current_sha(path,True)
    path.write_bytes(b"year,value\n2026,3\n")
    assert _current_sha(path,True)==canonical
    assert _current_sha(path)!=original
    path.write_bytes(b"year,value\n2026,4\n")
    assert _current_sha(path,True)!=canonical

def test_official_cpi_strict_workbook_matches_active_years():
    import sys
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/"scripts"))
    from audit_sources import cpi_values
    values=cpi_values(root/"data/sources/audit_20260917/cpi2025.xlsx")
    raw=pd.read_csv(root/"data/raw/cpi.csv")
    active=raw[raw["año"].ge(2012)].set_index("año").valor.to_dict()
    assert values == active
