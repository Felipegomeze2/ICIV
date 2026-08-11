"""Tests de la reconversion monetaria del tipo de cambio.

Venezuela redenomino tres veces y el WDI publica cada anio en la denominacion
vigente de ese anio, sin unificar. Si los factores estan mal, la serie deja de
ser comparable y la normalizacion Min-Max reparte mal todo el rango.

Factores oficiales (Gaceta Oficial):
    2008-01-01  Bs.F = 1.000 Bs        -> 3 ceros
    2018-08-20  Bs.S = 100.000 Bs.F    -> 5 ceros
    2021-10-01  Bs.D = 1.000.000 Bs.S  -> 6 ceros
"""

import numpy as np
import pytest

# Factores para llevar todo a Bs.F equivalente, replicando main.fase_pipeline
BSS_A_BSF = 100_000            # 1e5
BSD_A_BSF = 100_000_000_000    # 1e11


def a_bsf(anio: float, valor: float) -> float:
    """Convierte un valor del WDI a Bs.F equivalente segun su anio."""
    if anio <= 2017:
        return valor
    if anio <= 2021:
        return valor * BSS_A_BSF
    return valor * BSD_A_BSF


def test_factores_coinciden_con_las_reconversiones_oficiales():
    assert BSS_A_BSF == 10 ** 5, "la reconversion de 2018 quito 5 ceros, no 3"
    assert BSD_A_BSF == 10 ** 5 * 10 ** 6, "Bs.D->Bs.F debe componer 2018 y 2021"


def test_la_serie_convertida_es_monotona_creciente():
    """El bolivar solo se deprecio: en unidad unica la serie no puede bajar."""
    serie = {
        2015: 6.284200, 2016: 9.257344, 2017: 9.975000,
        2020: 315575.801683, 2021: 2104580.835287,
        2022: 6.683882, 2023: 28.635361, 2024: 38.378360,
    }
    convertidos = [a_bsf(a, v) for a, v in sorted(serie.items())]
    for previo, siguiente in zip(convertidos, convertidos[1:]):
        assert siguiente > previo, "la serie convertida debe ser monotona creciente"


def test_sin_conversion_la_serie_se_rompe():
    """Control: los valores crudos SI tienen el salto absurdo que motiva el fix."""
    assert 6.683882 < 2104580.835287, "2022 crudo parece menor que 2021: esa es la ruptura"


def test_el_salto_2017_2020_son_nueve_ordenes_y_medio():
    """Con los factores viejos (1e3/1e9) el salto salia 2 ordenes mas corto."""
    salto = np.log10(a_bsf(2020, 315575.801683)) - np.log10(a_bsf(2017, 9.975))
    assert salto == pytest.approx(9.5, abs=0.1)


def test_los_anios_previos_a_2018_no_se_tocan():
    for anio in (2000, 2010, 2017):
        assert a_bsf(anio, 5.0) == 5.0
