"""Tests de regresion de la guarda contra sobrescritura destructiva.

Contexto: el 2026-08-03 el fetch anual de Guardian fallo contra la API, escribio
igualmente el CSV y borro 27 anios de datos con NaN. D6 Percepcion Internacional
(10% del indice) dejo de aportar durante ocho dias sin que nada avisara.

Estos tests fijan el comportamiento que impide que vuelva a pasar.
"""

import pandas as pd
import pytest

from iciv.utils import NoDataError, save_dataframe


@pytest.fixture
def csv_con_datos(tmp_path):
    """Un CSV existente con datos buenos, como guardian.csv antes del incidente."""
    destino = tmp_path / "guardian.csv"
    pd.DataFrame({
        "año": [2024, 2025, 2026],
        "guardian_articulos_venezuela": [308, 690, 958],
        "guardian_tono_titulares": [-0.1664, -0.2293, -0.1585],
    }).to_csv(destino, index=False)
    return destino


def _df_vacio():
    """Lo que devuelve un fetcher cuando todas las peticiones fallaron."""
    return pd.DataFrame({
        "año": [2024, 2025, 2026],
        "guardian_articulos_venezuela": [None, None, None],
        "guardian_tono_titulares": [None, None, None],
    })


def test_no_sobrescribe_cuando_todo_viene_nan(csv_con_datos):
    """El caso exacto del incidente: no debe tocar el archivo."""
    original = csv_con_datos.read_text(encoding="utf-8")

    with pytest.raises(NoDataError):
        save_dataframe(_df_vacio(), csv_con_datos)

    assert csv_con_datos.read_text(encoding="utf-8") == original


def test_no_sobrescribe_con_dataframe_vacio(csv_con_datos):
    original = csv_con_datos.read_text(encoding="utf-8")

    with pytest.raises(NoDataError):
        save_dataframe(pd.DataFrame(), csv_con_datos)

    assert csv_con_datos.read_text(encoding="utf-8") == original


def test_escribe_cuando_hay_datos_reales(csv_con_datos):
    nuevo = pd.DataFrame({
        "año": [2024, 2025, 2026],
        "guardian_articulos_venezuela": [308, 690, 1000],
        "guardian_tono_titulares": [-0.1664, -0.2293, -0.1700],
    })

    assert save_dataframe(nuevo, csv_con_datos) is True
    assert pd.read_csv(csv_con_datos)["guardian_articulos_venezuela"].iloc[-1] == 1000


def test_escribe_aunque_falte_algun_anio(csv_con_datos):
    """Cobertura parcial es valida: el indice ya maneja NaN sueltos."""
    parcial = pd.DataFrame({
        "año": [2024, 2025, 2026],
        "guardian_articulos_venezuela": [308, None, 958],
        "guardian_tono_titulares": [None, None, -0.1585],
    })

    assert save_dataframe(parcial, csv_con_datos) is True


def test_modo_no_estricto_no_lanza(csv_con_datos):
    original = csv_con_datos.read_text(encoding="utf-8")

    assert save_dataframe(_df_vacio(), csv_con_datos, strict=False) is False
    assert csv_con_datos.read_text(encoding="utf-8") == original


def test_columnas_de_indice_no_cuentan_como_datos(tmp_path):
    """Un CSV con solo la columna de anio no es 'tener datos'."""
    destino = tmp_path / "vacio.csv"
    solo_indice = pd.DataFrame({"año": [2024, 2025], "valor": [None, None]})

    with pytest.raises(NoDataError):
        save_dataframe(solo_indice, destino)

    assert not destino.exists()


def test_crea_el_archivo_si_no_existia(tmp_path):
    destino = tmp_path / "subdir" / "nuevo.csv"
    df = pd.DataFrame({"año": [2026], "valor": [42.0]})

    assert save_dataframe(df, destino) is True
    assert destino.exists()
