"""Reglas de plausibilidad del proveedor, tramo oficial de la serie y semáforo SATV."""
import numpy as np
import pandas as pd

from iciv.data.plausibility import apply_plausibility
from iciv.index.aggregator import (
    OFFICIAL_SERIES_START, TRAMO_EXPLORATORIO, TRAMO_OFICIAL, ICIVAggregator, tramo_serie,
)
from iciv.index.dimensions import DIMENSIONS
from iciv.satv.pulse_engine import PulseSATVEngine


def test_impossible_zero_becomes_missing_and_is_registered():
    master = pd.DataFrame({"año": [2010, 2011, 2012],
                           "exportaciones_pct_pib": [0.0, 0.0, 29.6]})
    out, registry = apply_plausibility(master)
    assert out["exportaciones_pct_pib"].isna().tolist() == [True, True, False]
    assert out.loc[2, "exportaciones_pct_pib"] == 29.6
    # El panel original no se toca y el valor del proveedor queda registrado.
    assert master["exportaciones_pct_pib"].tolist() == [0.0, 0.0, 29.6]
    assert registry["valor_proveedor"].tolist() == [0.0, 0.0]
    assert set(registry["accion"]) == {"excluido_del_calculo"}


def test_impossible_rule_never_fills_or_substitutes():
    master = pd.DataFrame({"año": [2010, 2011], "exportaciones_pct_pib": [np.nan, 0.0]})
    out, _ = apply_plausibility(master)
    assert out["exportaciones_pct_pib"].isna().all()


def test_repeated_values_are_flagged_but_not_changed():
    years = list(range(2014, 2026))
    values = [15.8, 16.5] + [21.2] * 9 + [np.nan]
    master = pd.DataFrame({"año": years, "mortalidad_infantil_x1000": values})
    out, registry = apply_plausibility(master)
    pd.testing.assert_series_equal(out["mortalidad_infantil_x1000"], master["mortalidad_infantil_x1000"])
    flagged = registry[registry["regla"] == "valor_repetido"]
    assert flagged["año"].tolist() == list(range(2016, 2025))
    assert set(flagged["accion"]) == {"marcado_sin_cambio"}


def test_short_repeats_are_not_flagged():
    master = pd.DataFrame({"año": [2020, 2021, 2022, 2023],
                           "mortalidad_infantil_x1000": [10.0, 10.0, 10.0, 11.0]})
    _, registry = apply_plausibility(master)
    assert registry.empty


def test_tramo_serie_boundary():
    assert OFFICIAL_SERIES_START == 2012
    assert tramo_serie(2011) == TRAMO_EXPLORATORIO
    assert tramo_serie(2012) == TRAMO_OFICIAL
    assert tramo_serie(2026) == TRAMO_OFICIAL


def test_aggregator_exports_tramo_column():
    cols = [v.column for d in DIMENSIONS.values() for v in d.variables]
    df = pd.DataFrame({"año": [2011, 2012], **{c: [50.0, 60.0] for c in cols}})
    result = ICIVAggregator().compute(df)
    assert result["tramo_serie"].tolist() == [TRAMO_EXPLORATORIO, TRAMO_OFICIAL]


def test_satv_groups_use_last_eligible_month():
    pulse = pd.DataFrame({"año": [2026, 2026, 2026], "mes": [5, 6, 7],
                          "pulse_score": [60.0, 57.0, 80.0], "cobertura_pct": [100.0, 100.0, 30.0],
                          "elegible_modelo": [True, True, False]})
    comps = pd.DataFrame({"año": [2026, 2026, 2026], "mes": [5, 6, 7],
                          "petroleo_liquidos_totales_tbpd": [40.0, 45.0, np.nan],
                          "wti_precio_usd": [70.0, 72.0, 99.0]})
    result = PulseSATVEngine(pulse, comps).compute_all()
    assert result["fecha_referencia_grupos"] == "2026-06"
    assert result["dimensiones"]["energia"]["score_actual"] == 45.0
    # La alerta de mes provisional sigue mirando el último mes publicado.
    assert any(a["tipo"] == "Mes provisional" for a in result["alertas_activas"])
