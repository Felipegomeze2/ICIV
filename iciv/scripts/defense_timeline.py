"""
Gráfico de defensa: timeline del ICIV 2000-2026 con eventos históricos anotados.

La pregunta que responde ante el jurado: "¿cómo sé que el índice mide algo real?"
Si el ICIV reacciona en el momento y la dirección que la historia conocida exige
(paro petrolero, expropiaciones, sanciones, apagón, COVID), el índice tiene
validez de constructo observable a simple vista.

Genera dos variantes en docs/figures/:
  - iciv_timeline_eventos.png       (fondo claro, para slides e impresión)
  - iciv_timeline_eventos_dark.png  (fondo oscuro, coherente con el dashboard)

Uso:
  cd iciv
  python scripts/defense_timeline.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

_ICIV_DIR = Path(__file__).resolve().parents[1]
SCORES_CSV = _ICIV_DIR / "data" / "processed" / "iciv_scores_ahp.csv"
FIG_DIR = _ICIV_DIR.parent / "docs" / "figures"

# (año, etiqueta, dirección esperada: -1 baja / +1 sube)
EVENTOS = [
    (2002, "Golpe de Estado +\nparo petrolero PDVSA", -1),
    (2007, "Cierre RCTV ·\nnacionalizaciones masivas", -1),
    (2014, "Caída del crudo ·\nprotestas masivas", -1),
    (2017, "ANC constituyente ·\nsanciones financieras EE.UU.", -1),
    (2019, "Sanciones petroleras ·\napagón nacional · Guaidó", -1),
    (2020, "COVID-19 ·\ncolapso de demanda", -1),
    (2021, "Dolarización informal ·\nrecuperación gradual", +1),
    (2024, "Elecciones presidenciales ·\nescalada represiva", -1),
]

# Umbral de cobertura para considerar un año como consolidado
COBERTURA_MIN = 70.0

# Bandas de riesgo (idénticas a RISK_CATEGORIES del aggregator)
BANDAS = [
    (0, 30, "Alto Riesgo"),
    (30, 50, "Riesgo Moderado-Alto"),
    (50, 65, "Riesgo Moderado"),
    (65, 80, "Bajo Riesgo"),
    (80, 100, "Muy Bajo Riesgo"),
]


def _plot(df: pd.DataFrame, dark: bool) -> plt.Figure:
    if dark:
        bg, fg, muted, grid = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
        line_col, event_col = "#00d4aa", "#f1c40f"
        band_cols = ["#e05c5c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"]
        band_alpha = 0.10
    else:
        bg, fg, muted, grid = "#ffffff", "#1a2b3c", "#5a6b7c", "#d8dde3"
        line_col, event_col = "#00795f", "#b07d00"
        band_cols = ["#c0392b", "#d35400", "#b7950b", "#1e8449", "#145a32"]
        band_alpha = 0.07

    fig, ax = plt.subplots(figsize=(13, 6.5))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    # Bandas de riesgo de fondo con etiqueta al margen derecho
    for (lo, hi, label), col in zip(BANDAS, band_cols):
        ax.axhspan(lo, hi, color=col, alpha=band_alpha, zorder=0)
        ax.text(2026.6, (lo + hi) / 2, label, fontsize=7.5, color=muted,
                va="center", ha="left", style="italic")

    # Años con cobertura suficiente (>=70% del peso del índice) en línea sólida;
    # años preliminares en punteado con marcador hueco. Evita que el lector
    # confunda un artefacto de cobertura (p. ej. 2026 con 19%) con una mejora real.
    solid = df[df["cobertura_pct"] >= COBERTURA_MIN]
    # Tramo preliminar: desde el último año sólido para que la línea conecte
    prelim = df[df["año"] >= solid["año"].max()]

    ax.plot(solid["año"], solid["iciv_score"], color=line_col, linewidth=2.6,
            zorder=3, marker="o", markersize=4.5, markerfacecolor=line_col)
    if len(prelim) > 1:
        ax.plot(prelim["año"], prelim["iciv_score"], color=line_col,
                linewidth=1.8, linestyle=(0, (4, 3)), zorder=3, marker="o",
                markersize=4.5, markerfacecolor=bg, markeredgecolor=line_col)
        x_mid = prelim["año"].mean()
        y_min = prelim["iciv_score"].min()
        ax.text(x_mid, max(y_min - 9, 2),
                f"cobertura < {COBERTURA_MIN:.0f}%\n(lectura preliminar)",
                fontsize=7.2, color=muted, ha="center", va="top",
                style="italic", linespacing=1.2)

    score_by_year = dict(zip(df["año"], df["iciv_score"]))

    # Eventos anotados, alternando alturas para evitar choques de texto
    offsets = [34, 18, 30, 14, 34, 18, -26, 30]
    for (yr, label, dir_), dy in zip(EVENTOS, offsets):
        y = score_by_year.get(yr)
        if y is None:
            continue
        ax.annotate(
            label, xy=(yr, y), xytext=(yr, y + dy),
            fontsize=7.6, color=fg, ha="center", va="center",
            linespacing=1.25,
            arrowprops=dict(arrowstyle="-", color=event_col, linewidth=1.0,
                            shrinkA=4, shrinkB=3),
            bbox=dict(boxstyle="round,pad=0.32", facecolor=bg,
                      edgecolor=event_col, linewidth=0.9, alpha=0.95),
            zorder=4,
        )
        flecha = "▼" if dir_ < 0 else "▲"
        col_dir = "#c0392b" if dir_ < 0 else "#1e8449"
        if dark:
            col_dir = "#e05c5c" if dir_ < 0 else "#2ecc71"
        ax.text(yr, y + (7 if dy > 0 else -7), flecha, fontsize=7,
                color=col_dir, ha="center", va="center", zorder=4)

    ax.set_xlim(1999.4, 2030.5)
    ax.set_ylim(0, 105)
    ax.set_xticks(range(2000, 2027, 2))
    ax.set_xlabel("Año", color=muted, fontsize=10)
    ax.set_ylabel("ICIV (0–100)", color=muted, fontsize=10)
    ax.set_title(
        "ICIV 2000–2026 — El índice reacciona a la historia conocida de Venezuela",
        color=fg, fontsize=13, fontweight="bold", pad=14,
    )
    ax.tick_params(colors=muted, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(grid)
    ax.grid(True, color=grid, linewidth=0.5, alpha=0.7, zorder=1)

    fig.text(0.01, 0.012,
             "Fuente: ICIV (pesos AHP, 26 variables core, fuentes 100% internacionales). "
             "Eventos: cronología documentada 2002–2024. Línea punteada: años con cobertura "
             "de datos inferior al 70% (lectura preliminar). Elaboración propia.",
             fontsize=7, color=muted)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def main() -> None:
    df = pd.read_csv(SCORES_CSV)[["año", "iciv_score", "cobertura_pct"]].dropna()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    for dark, fname in [(False, "iciv_timeline_eventos.png"),
                        (True, "iciv_timeline_eventos_dark.png")]:
        fig = _plot(df, dark=dark)
        out = FIG_DIR / fname
        fig.savefig(out, dpi=300, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"OK {out}")


if __name__ == "__main__":
    main()
