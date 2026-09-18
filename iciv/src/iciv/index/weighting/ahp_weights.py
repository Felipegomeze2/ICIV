"""
AHP (Analytic Hierarchy Process) — Ponderación de Saaty (1980).

Calcula los pesos de las dimensiones e indicadores del ICIV mediante el
método de vectores propios (eigenvector method) de Saaty, con validación
de consistencia (CR < 0.10).

Referencia metodológica:
  Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill, New York.
  OCDE (2008). Handbook on Constructing Composite Indicators, Cap. 7.

Flujo:
  1. El usuario (o experto) completa una matriz de comparación por pares
     usando la escala de Saaty (1–9).
  2. Se calcula el vector propio principal → pesos normalizados.
  3. Se calcula el Índice de Consistencia (CI) y la Razón de Consistencia
     (CR = CI / RI). Si CR < 0.10 el juicio es aceptable.
  4. Los pesos se pasan al ICIVAggregator como override de dimensiones.

Escala de Saaty:
  1 = Igual importancia
  3 = Moderadamente más importante
  5 = Fuertemente más importante
  7 = Muy fuertemente más importante
  9 = Extremadamente más importante
  2, 4, 6, 8 = Valores intermedios
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .base import WeightingStrategy
from iciv.index.dimensions import DIMENSIONS

logger = logging.getLogger(__name__)

# ── Índice de Consistencia Aleatoria (Saaty, 1980) ───────────────────────────
# RI[n] es el promedio del CR de 500 matrices aleatorias de tamaño n.
# CR = CI / RI; CR < 0.10 comprueba consistencia interna, no validez económica.
_RI: dict[int, float] = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
}

# ── Matriz AHP pre-definida para las 6 DIMENSIONES del ICIV ──────────────────
#
# Orden de filas/columnas:
#   [D1_macro, D2_energia, D3_institucional, D4_comercial, D5_capital, D6_percepcion]
#
# Justificación de cada juicio:
#   D1 > D2 = D3 (igualmente): sin estabilidad macro todo falla (Saaty 1)
#   D1 > D4:  la apertura es secundaria a la estabilidad         (Saaty 2)
#   D1 > D5, D6: menor peso por diseño                           (Saaty 3)
#   D2 = D3:  energía e institucional con mismo peso objetivo     (Saaty 1)
#   D2 > D4:  petróleo = principal divisa de Venezuela            (Saaty 1)
#   D2 > D5, D6                                                   (Saaty 2)
#   D3 > D4                                                       (Saaty 1)
#   D3 > D5, D6                                                   (Saaty 2)
#   D4 > D5, D6                                                   (Saaty 2)
#   D5 = D6:  igual peso por diseño                               (Saaty 1)
#
# Pesos objetivo: D1=25%, D2=20%, D3=20%, D4=15%, D5=10%, D6=10%

_DIMENSION_LABELS = [
    "D1_macro",
    "D2_energia",
    "D3_institucional",
    "D4_comercial",
    "D5_capital_humano",
    "D6_percepcion",
]

_DEFAULT_DIMENSION_MATRIX = np.array([
    #   D1    D2    D3    D4    D5    D6
    [  1.0,  1.0,  1.0,  2.0,  3.0,  3.0],  # D1
    [  1.0,  1.0,  1.0,  1.0,  2.0,  2.0],  # D2
    [  1.0,  1.0,  1.0,  1.0,  2.0,  2.0],  # D3
    [  1/2,  1.0,  1.0,  1.0,  2.0,  2.0],  # D4
    [  1/3,  1/2,  1/2,  1/2,  1.0,  1.0],  # D5
    [  1/3,  1/2,  1/2,  1/2,  1.0,  1.0],  # D6
], dtype=float)

# ── Matrices AHP para variables dentro de cada dimensión ─────────────────────

def _consistent_ratio_matrix(weights: list[float]) -> np.ndarray:
    """Construye la matriz de razones a[i][j] = w_i / w_j a partir de pesos dados.

    IMPORTANTE — leer antes de citar cualquier CR de estas matrices.

    Esto NO es una matriz de comparación por pares en el sentido de Saaty. Una
    matriz AHP legítima recoge juicios independientes (¿cuánto más importante es
    i que j?) y el CR mide si esos juicios son mutuamente coherentes. Aquí la
    matriz se DERIVA de los pesos ya elegidos, así que es perfectamente
    consistente por construcción: su CR vale 0 exacto siempre, para cualquier
    vector de pesos, incluido uno absurdo.

    Dicho de otro modo: el CR de estas matrices no valida nada. Solo confirma
    que la división funciona.

    Por qué se conserva: el agregador necesita un vector de pesos por variable y
    esta función lo devuelve de forma equivalente a declararlo directamente. Lo
    que NO se debe hacer es presentar el CR resultante como evidencia de rigor.

    La matriz de DIMENSIONES (`_DEFAULT_DIMENSION_MATRIX`) sí está construida a
    mano con valores Saaty y su CR = 0,0081 sí es un resultado informativo.

    Ver docs/METODOLOGIA.md §2.3.
    """
    arr = np.array(weights, dtype=float)
    return arr[:, None] / arr[None, :]


def _eigenvector_weights(matrix: np.ndarray) -> np.ndarray:
    """
    Calcula el vector propio principal de una matriz cuadrada positiva.

    Método: potencia iterativa (power method) — más estable que eigh()
    para matrices AHP con entradas fraccionarias.

    Returns:
        Vector normalizado (suma = 1.0) con los pesos AHP.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        raise ValueError("La matriz AHP debe ser cuadrada y no vacía")
    if not np.isfinite(matrix).all() or (matrix <= 0).any():
        raise ValueError("La matriz AHP debe tener entradas positivas y finitas")
    if not np.allclose(np.diag(matrix), 1.0) or not np.allclose(matrix * matrix.T, 1.0):
        raise ValueError("La matriz AHP debe ser recíproca y tener diagonal unitaria")
    n = matrix.shape[0]
    w = np.ones(n) / n

    for _ in range(1000):
        w_new = matrix @ w
        w_new /= w_new.sum()
        if np.allclose(w_new, w, atol=1e-10):
            break
        w = w_new

    return w_new


def _consistency_ratio(matrix: np.ndarray, weights: np.ndarray) -> dict:
    """
    Calcula el Índice de Consistencia (CI) y la Razón de Consistencia (CR).

    CR = CI / RI
    CI = (λmax - n) / (n - 1)
    λmax = promedio ponderado de (Aw / w) para cada elemento

    Returns:
        dict con lambda_max, CI, RI, CR y si pasa el umbral.
    """
    n = matrix.shape[0]
    aw = matrix @ weights
    lambda_max = float(np.mean(aw / weights))
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = _RI.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    return {
        "n": n,
        "lambda_max": round(lambda_max, 4),
        "CI": round(ci, 4),
        "RI": ri,
        "CR": round(cr, 4),
        "consistent": cr < 0.10,
    }


def compute_ahp(
    matrix: np.ndarray,
    labels: list[str] | None = None,
) -> dict:
    """
    Ejecuta el proceso AHP completo sobre una matriz de comparación.

    Args:
        matrix: matriz de comparación por pares (n × n), cuadrada y positiva.
                La entrada a[i][j] indica cuánto más importante es el elemento i
                respecto al elemento j (escala Saaty 1–9).
                La diagonal debe ser 1.0; a[j][i] = 1 / a[i][j].
        labels: nombres de los elementos (filas/columnas). Opcionales.

    Returns:
        dict con:
          - weights: dict {label: peso} o {i: peso} si no hay labels
          - weights_array: np.ndarray con los pesos ordenados
          - consistency: dict con lambda_max, CI, RI, CR, consistent
          - table: DataFrame con label, peso, peso_pct para reportes
    """
    n = matrix.shape[0]
    if matrix.shape != (n, n):
        raise ValueError(f"La matriz debe ser cuadrada. Forma recibida: {matrix.shape}")

    weights = _eigenvector_weights(matrix)
    consistency = _consistency_ratio(matrix, weights)

    keys = labels if labels is not None else [str(i) for i in range(n)]
    if len(keys) != n or len(set(keys)) != n:
        raise ValueError("Las etiquetas AHP deben ser únicas y coincidir con la matriz")

    weights_dict = {k: round(float(w), 6) for k, w in zip(keys, weights)}

    table = pd.DataFrame({
        "elemento": keys,
        "peso_ahp": [round(float(w), 4) for w in weights],
        "peso_pct": [f"{w*100:.1f}%" for w in weights],
    })

    # El CR solo es informativo cuando la matriz recoge juicios independientes.
    # Si se derivó de un vector de pesos (a[i][j] = w_i/w_j) su CR es 0 por
    # construcción y anunciarlo como "consistencia aceptable" seria engañoso.
    derivada = bool(np.isclose(consistency["CR"], 0.0, atol=1e-9))

    if not consistency["consistent"]:
        logger.warning(
            "AHP: CR = %.3f ≥ 0.10 — la matriz no es suficientemente consistente. "
            "Revisa los juicios de comparación (Saaty 1980).",
            consistency["CR"],
        )
    elif derivada:
        logger.info(
            "Pesos declarados: CR = 0 por construcción (matriz derivada de los "
            "pesos, no de juicios independientes). El CR no valida nada aquí."
        )
    else:
        logger.info(
            "AHP: CR = %.4f < 0.10 — juicios consistentes (λmax = %.3f, n = %d).",
            consistency["CR"],
            consistency["lambda_max"],
            n,
        )

    return {
        "weights": weights_dict,
        "weights_array": weights,
        "consistency": consistency,
        "table": table,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLASE WeightingStrategy — integración con el pipeline del ICIV
# ─────────────────────────────────────────────────────────────────────────────


class AHPWeights(WeightingStrategy):
    """
    Estrategia de ponderación basada en el Proceso de Jerarquía Analítica (AHP).

    Usa la matriz de comparación de dimensiones pre-definida (o la que
    proporcione el usuario) para calcular los pesos de cada variable.

    El peso final de cada variable es:
        peso_final = peso_dim_AHP × peso_variable_AHP_dentro_de_dim

    Args:
        dimension_matrix: matriz de comparación entre dimensiones (6×6).
                          Si None, usa la matriz pre-definida del ICIV.
        variable_matrices: dict {dim_label: (matrix, labels)} para pesos
                           internos de variables. Si None, usa las matrices
                           pre-definidas.
        require_consistency: si True (por defecto), lanza ValueError cuando
                             CR ≥ 0.10 en cualquier matriz.

    Atributos disponibles tras compute_weights():
        dimension_result_:  resultado AHP de las dimensiones
        variable_results_:  dict {dim_label: resultado AHP}
        cr_report_:         resumen de CR de todas las matrices
    """

    def __init__(
        self,
        dimension_matrix: np.ndarray | None = None,
        variable_matrices: dict[str, tuple[np.ndarray, list[str]]] | None = None,
        require_consistency: bool = True,
    ) -> None:
        self._dim_matrix = (
            dimension_matrix
            if dimension_matrix is not None
            else _DEFAULT_DIMENSION_MATRIX.copy()
        )
        self._var_matrices = self._default_variable_matrices()
        if variable_matrices is not None:
            self._var_matrices.update(variable_matrices)
        self.require_consistency = require_consistency

        self.dimension_result_: dict | None = None
        self.variable_results_: dict[str, dict] = {}
        self.cr_report_: pd.DataFrame | None = None

    # ── Interfaz WeightingStrategy ─────────────────────────────────────────────

    def compute_weights(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Calcula los pesos AHP para cada variable del DataFrame.

        Los pesos de dimensión derivan de la matriz de comparación entre
        dimensiones; los pesos internos, de las matrices por dimensión.

        Returns:
            dict {columna: peso_final} sobre el universo completo, normalizado a 1.0.
        """
        # 1. Pesos de dimensiones
        self.dimension_result_ = compute_ahp(self._dim_matrix, _DIMENSION_LABELS)
        dim_weights = self.dimension_result_["weights"]
        self._check_cr(self.dimension_result_["consistency"], "Dimensiones")

        # 2. Pesos de variables dentro de cada dimensión
        final_weights: dict[str, float] = {}

        for dim_label, (var_matrix, var_labels) in self._var_matrices.items():
            result = compute_ahp(var_matrix, var_labels)
            self.variable_results_[dim_label] = result
            self._check_cr(result["consistency"], dim_label)

            dim_w = dim_weights.get(dim_label, 0.0)
            for var_label, var_w in result["weights"].items():
                final_weights[var_label] = dim_w * var_w

        # 3. Universo fijo: una columna ausente conserva su peso esperado.
        total = sum(final_weights.values())
        if total > 0:
            final_weights = {k: v / total for k, v in final_weights.items()}

        # 4. Construir reporte de CR
        rows = [
            {
                "nivel": "Dimensiones (6×6)",
                "CR": self.dimension_result_["consistency"]["CR"],
                "CI": self.dimension_result_["consistency"]["CI"],
                "lambda_max": self.dimension_result_["consistency"]["lambda_max"],
                "consistente": self.dimension_result_["consistency"]["consistent"],
            }
        ]
        for dim_label, res in self.variable_results_.items():
            rows.append({
                "nivel": f"Variables {dim_label}",
                "CR": res["consistency"]["CR"],
                "CI": res["consistency"]["CI"],
                "lambda_max": res["consistency"]["lambda_max"],
                "consistente": res["consistency"]["consistent"],
            })
        self.cr_report_ = pd.DataFrame(rows)

        logger.info(
            "AHPWeights: %d pesos calculados. "
            "Dimensiones CR=%.3f. Todas consistentes: %s",
            len(final_weights),
            self.dimension_result_["consistency"]["CR"],
            all(self.cr_report_["consistente"]),
        )
        return final_weights

    def get_method_name(self) -> str:
        cr = (
            self.dimension_result_["consistency"]["CR"]
            if self.dimension_result_
            else "N/A"
        )
        cr_str = f"{cr:.3f}" if isinstance(cr, float) else cr
        return f"AHP — Saaty (1980) · CR dimensiones = {cr_str}"

    # ── Métodos de reporte (para la tesis) ────────────────────────────────────

    def get_dimension_weights_table(self) -> pd.DataFrame:
        """Tabla de pesos de dimensiones con nombre y CR."""
        if self.dimension_result_ is None:
            raise RuntimeError("Llama a compute_weights() primero.")
        return self.dimension_result_["table"]

    def get_variable_weights_table(self) -> pd.DataFrame:
        """
        Tabla consolidada de pesos de variables con su dimensión,
        peso en dimensión, peso de dimensión y peso final.
        """
        if not self.variable_results_:
            raise RuntimeError("Llama a compute_weights() primero.")

        dim_weights = self.dimension_result_["weights"]  # type: ignore[index]
        rows = []
        for dim_label, result in self.variable_results_.items():
            dim_w = dim_weights.get(dim_label, 0.0)
            for var_label, var_w in result["weights"].items():
                rows.append({
                    "dimensión": dim_label,
                    "peso_dimensión": round(dim_w, 4),
                    "variable": var_label,
                    "peso_en_dim": round(var_w, 4),
                    "peso_final": round(dim_w * var_w, 4),
                    "peso_final_pct": f"{dim_w * var_w * 100:.2f}%",
                })

        return pd.DataFrame(rows).sort_values("peso_final", ascending=False).reset_index(drop=True)

    def get_cr_report(self) -> pd.DataFrame:
        """Tabla de razones de consistencia de todas las matrices AHP."""
        if self.cr_report_ is None:
            raise RuntimeError("Llama a compute_weights() primero.")
        return self.cr_report_

    def print_ahp_report(self) -> None:
        """Imprime en consola el resumen completo del AHP para revisión."""
        if self.dimension_result_ is None:
            print("Llama a compute_weights() primero.")
            return

        print("\n" + "=" * 65)
        print("  INFORME AHP — ICIV Venezuela")
        print("=" * 65)

        print("\n── Pesos de Dimensiones ────────────────────────────────────")
        print(self.get_dimension_weights_table().to_string(index=False))
        cons = self.dimension_result_["consistency"]
        print(f"\n  λmax = {cons['lambda_max']}  ·  CI = {cons['CI']}  "
              f"·  RI = {cons['RI']}  ·  CR = {cons['CR']}  "
              f"({'✓ consistente' if cons['consistent'] else '✗ NO consistente'})")

        print("\n── Pesos de Variables (top 10 por peso final) ─────────────")
        tbl = self.get_variable_weights_table()
        print(tbl.head(10).to_string(index=False))

        print("\n── Razones de Consistencia ─────────────────────────────────")
        print(self.get_cr_report().to_string(index=False))

        all_ok = self.cr_report_["consistente"].all()  # type: ignore[union-attr]
        print(f"\n  Todas las matrices son consistentes (CR<0.10): "
              f"{'SÍ ✓' if all_ok else 'NO ✗'}")
        print("=" * 65 + "\n")

    # ── Privados ───────────────────────────────────────────────────────────────

    @staticmethod
    def _default_variable_matrices() -> dict[str, tuple[np.ndarray, list[str]]]:
        # Una sola configuración interna: no duplicar pesos del catálogo.
        return {dim_id.value: (
            _consistent_ratio_matrix([v.weight for v in dim.variables]),
            [v.column for v in dim.variables],
        ) for dim_id, dim in DIMENSIONS.items()}

    def _check_cr(self, consistency: dict, name: str) -> None:
        if self.require_consistency and not consistency["consistent"]:
            raise ValueError(
                f"AHP '{name}': CR = {consistency['CR']:.3f} ≥ 0.10. "
                "Revisa los juicios de la matriz de comparación."
            )
