"""Summarize strict-QA evidence without admitting it to the annual index."""
from pathlib import Path
import json
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def main():
    data = pd.read_csv(ROOT/"data/raw/blackmarble_qa_monthly.csv")
    data = data[data.variable.eq("luminosidad_nocturna_mensual_nwcm2sr")].sort_values(["año","mes"])
    for _,row in data.iterrows():
        evidence = ROOT/f"data/sources/blackmarble_qa/{int(row['año'])}-{int(row.mes):02d}.json"
        if not evidence.exists():
            raise ValueError(f"Missing granule evidence: {evidence.name}")
        e = json.loads(evidence.read_text(encoding="utf-8"))
        if len(e["granules"]) != 5 or abs(e["valid_pixel_pct"]-row.valid_pixel_pct)>0.000051:
            raise ValueError(f"Inconsistent spatial evidence: {evidence.name}")
    data[["año","mes","valor","n_valid_pixels","n_total_pixels","valid_pixel_pct"]].to_csv(ROOT/"data/processed/satellite_qa_coverage.csv", index=False)
    y = data[data["año"].eq(2025)]
    lines = ["# Revisión satelital · decisión de exclusión", "",
        "Se recuperaron granulos reales NASA VNP46A3 colección 002 usando las credenciales configuradas. El extractor excluye calidad distinta de 0, rellenos y píxeles con tres observaciones o menos. No se usaron datos simulados ni el histórico sin QA para completar faltantes.", "",
        f"La muestra recuperada contiene {len(data)} meses: todos los de 2025, meses de referencia de 2014/2019 y julio de 2026. No representa un reprocesamiento de todo el histórico 2014–2026.", "",
        f"En 2025 la cobertura válida va de **{y.valid_pixel_pct.min():.2f}% a {y.valid_pixel_pct.max():.2f}%** sobre la máscara de {int(y.n_total_pixels.iloc[0]):,} píxeles. Solo {(y.valid_pixel_pct>=50).sum()} de 12 meses alcanza 50%. Este umbral es diagnóstico, no un estándar NASA ni una calibración externa.", "",
        "| Año | Mes | Radiancia media válida | Píxeles válidos % |", "|---|---:|---:|---:|"]
    for _,r in data.iterrows():
        lines.append(f"| {int(r['año'])} | {int(r.mes)} | {r.valor:.4f} | {r.valid_pixel_pct:.4f} |")
    lines += ["", "## Decisión implementada", "",
        "Luminosidad permanece **fuera del score anual y de Pulse**, incluso si existe el CSV QA. La variable mantiene su lugar en el universo de cobertura v2 para no mejorar artificialmente la cobertura al excluirla. No se introduce Li et al. como sustituto. Los score anuales no cambian por estas nuevas descargas.", "",
        "La media mensual representa los píxeles válidos de ese mes, cuya distribución cambia con nubes, geometría de observación y disponibilidad. Una media de meses con territorios distintos no acredita un indicador nacional comparable. No se infiere caída de actividad a partir de una caída de radiancia en un mes de baja cobertura.", "",
        "Cada mes tiene URL e identificador de sus cinco granulos, hash de los bytes descargados, hash del GeoJSON y conteos en `iciv/data/sources/blackmarble_qa`. Los HDF5 se eliminan tras procesarlos; los hashes no sustituyen los archivos y reproducir la extracción requiere volver a descargarlos. La máscara está en una cuadrícula angular; las medias ponderan píxeles por igual, no por superficie geodésica.", "",
        "El mapa heredado conserva la advertencia de contexto sin QA acreditado. La muestra estricta queda como evidencia auxiliar separada. Una futura reincorporación necesita cobertura espacial/estacional suficiente, verificación de máscaras, ponderación de área, comparación de canastas espaciales comunes y validación económica, sin rellenar píxeles ausentes.", "",
        "Referencia QA: [NASA Black Marble Collection 2 User Guide](https://landweb.modaps.eosdis.nasa.gov/data/userguide/BlackMarbleUserGuide_Collection2.0_20241203.pdf). Los criterios de representatividad propuestos son del proyecto, no una certificación NASA.", ""]
    (ROOT.parent/"docs/REVISION_SATELITAL.md").write_text("\n".join(lines),encoding="utf-8")
    print(f"Satellite evidence: {len(data)} months, exclusion retained")

if __name__ == "__main__":
    main()
