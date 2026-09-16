from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from iciv.index.pulse_aggregator import PulseAggregator, PULSE_WEIGHTS
from iciv.ml.pulse_models import prepare_series
from iciv.analytics.sector_radar import SectorRadar, DIM_COLS
from iciv.data.loaders.index_loader import CPILoader

def test_pulse_append_invariant_and_missing(tmp_path):
    a=PulseAggregator(tmp_path)
    col=next(iter(PULSE_WEIGHTS))
    df=pd.DataFrame({"fecha":pd.date_range("2020-01-01",periods=4,freq="MS"), col:[2.,4.,np.nan,100.]})
    prefix=a.normalize(df.iloc[:3])[col]
    entire=a.normalize(df)[col]
    pd.testing.assert_series_equal(prefix,entire.iloc[:3])
    assert pd.isna(entire.iloc[0]) and pd.isna(entire.iloc[2])

def test_constant_pulse_does_not_fabricate_50(tmp_path):
    col=next(iter(PULSE_WEIGHTS))
    df=pd.DataFrame({"fecha":pd.date_range("2020-01-01",periods=3,freq="MS"),col:[2.,2.,np.nan]})
    assert PulseAggregator(tmp_path).normalize(df)[col].isna().all()

def test_calendar_gap_is_not_compressed():
    df=pd.DataFrame({"año":[2020,2020],"mes":[1,3],"pulse_score":[40,60],"cobertura_pct":[90,90]})
    result=prepare_series(df)
    assert len(result)==3 and pd.isna(result.loc["2020-02-01"])

def test_low_coverage_rejected_without_fill():
    df=pd.DataFrame({"año":[2020,2020],"mes":[1,2],"pulse_score":[40,60],"cobertura_pct":[90,60]})
    assert pd.isna(prepare_series(df).iloc[1])

def test_sector_missing_dimension_does_not_become_neutral():
    cfg={"sectores":{"test":{"label":"test","label_corto":"test","pesos":{d:1/6 for d in DIM_COLS}}}}
    df=pd.DataFrame([{**{d:50 for d in DIM_COLS},"D3_institucional":np.nan,"año":2020,"iciv_score":50}])
    assert SectorRadar(df,cfg).compute_all()["available"] is False

def test_sector_has_no_manual_bonus():
    cfg={"sectores":{"test":{"label":"test","label_corto":"test","pesos":{d:1/6 for d in DIM_COLS}}}}
    df=pd.DataFrame([{**{d:50 for d in DIM_COLS},"año":2020,"iciv_score":50}])
    assert SectorRadar(df,cfg).compute_all()["ranking"][0]["score"]==50


def test_satellite_quality_rejects_gapfilled_poor_and_few_observations():
    import importlib.util
    script=Path(__file__).resolve().parents[1]/"scripts/fetch_blackmarble_monthly.py"
    spec=importlib.util.spec_from_file_location("bm_quality_test",script)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    raw=np.array([20.,20.,20.,65535.,20.,20.])
    quality=np.array([0,1,2,0,0,0])
    counts=np.array([4,10,10,10,3,65535])
    assert mod._quality_mask(raw,65535,quality,counts,65535).tolist()==[True,False,False,False,False,False]
