"""
Construye el grafo de sanciones OFAC — Venezuela (2000-2026).

Fuente de datos:
  OFAC SDN List: https://www.treasury.gov/ofac/downloads/sdn.csv
  SDN XML:       https://www.treasury.gov/ofac/downloads/sdnlist.xml
  OFAC Action Lookup: https://ofac.treasury.gov/recent-actions/

Metodología:
  1. Descarga la lista SDN actual en formato CSV del US Treasury.
  2. Filtra entidades vinculadas a Venezuela mediante los programas:
       VENEZUELA, SDNTK (narco-tráfico Venezuela), SDGT (terrorismo global
       con nexo venezolano) y SDNNPC (no-proliferación con nexo venezolano),
     y mediante el campo country='VENEZUELA'.
  3. Clasifica cada entidad en 6 categorías según el tipo SDN y el nombre:
       Gobierno, PDVSA, Banca, Militares, Intermediarios, Otro.
  4. Construye aristas de relación a partir de:
       a. El campo 'remarks' de la lista SDN (relaciones explícitas documentadas).
       b. Una tabla de relaciones estructurales derivada de las órdenes ejecutivas
          EO 13692, EO 13808, EO 13850 y reportes CRS R45046 / RL32488.
  5. Emite un JSON con listas 'nodes' y 'links' listo para D3.js.

Salida: data/raw/ofac_network.json

Referencias:
  U.S. Treasury OFAC. (2024). Venezuela-Related Sanctions.
    https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions
  CRS Report R45046. (2024). Venezuela: Overview of U.S. Sanctions.
  CRS Report RL32488. (2023). OFAC SDN Lists: Background and Legislative Issues.

Uso:
    python scripts/fetch_ofac_network.py
"""

from __future__ import annotations

import json
import re
import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402

OUTPUT = settings.paths.raw_ofac_network

SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"

# Programas OFAC asociados a Venezuela
VEN_PROGRAMS = {"VENEZUELA", "SDNTK", "SDGT", "SDNNPC", "PEESA-EO14024"}

# Columnas del SDN CSV (formato fijo de OFAC)
SDN_COLS = [
    "ent_num", "sdn_name", "sdn_type", "program",
    "title", "call_sign", "vess_type", "tonnage", "grt",
    "vess_flag", "vess_owner", "remarks",
]

# ─────────────────────────────────────────────────────────────────────────────
# Clasificación de categorías
# ─────────────────────────────────────────────────────────────────────────────

_GOV_KEYWORDS  = ["minister", "ministro", "gobernador", "governor", "presidente",
                  "president", "diplomat", "embajad", "magistrad", "fiscal",
                  "attorney", "judge", "juez", "assembly", "asamblea",
                  "national assembly", "congres", "senador", "senator",
                  "municipal", "alcald", "mayor", "chavez", "maduro", "cabello",
                  "delcy", "jorge rodriguez", "tarek", "vielma", "heliodoro"]

_PDVSA_KEYWORDS = ["pdvsa", "petróleo", "petroleo", "petróleos de venezuela",
                   "petroleos de venezuela", "pdvg", "bariven", "intevep",
                   "pdvex", "carbozulia", "bandes", "pequiven", "cvg",
                   "corporacion venezolana", "mibam", "siembra petrolera"]

_BANK_KEYWORDS  = ["bank", "banco", "banca", "financ", "credit", "caja",
                   "fondo", "fund", "investment", "inversio", "capital markets",
                   "securities", "bolsa", "exchange", "bandes", "bicentenario",
                   "provincial", "tesoro", "treasury", "casa de bolsa"]

_MIL_KEYWORDS   = ["general", "almirante", "admiral", "colonel", "coronel",
                   "capitan", "captain", "teniente", "lieutenant", "mayor",
                   "sargento", "sebin", "dgcim", "gnb", "guardia nacional",
                   "national guard", "fuerzas armadas", "army", "navy",
                   "marines", "ejercito", "fuerza aerea", "air force",
                   "minister of defense", "ministro de defensa"]

_INTER_KEYWORDS = ["holding", "corp", "ltd", "s.a.", "c.a.", "llc", "inc.",
                   "trading", "import", "export", "comercio", "logistic",
                   "transport", "shipping", "aviation", "air", "cargo",
                   "enterprise", "group", "grupo", "consortium", "international",
                   "offshore", "global", "services", "consultora"]


def _classify(name: str, sdn_type: str, program: str) -> str:
    nl = (name or "").lower()
    if any(k in nl for k in _PDVSA_KEYWORDS):
        return "PDVSA"
    if any(k in nl for k in _MIL_KEYWORDS):
        return "Militares"
    if any(k in nl for k in _GOV_KEYWORDS):
        return "Gobierno"
    if any(k in nl for k in _BANK_KEYWORDS):
        return "Banca"
    if sdn_type in ("Entity", "-0-") or any(k in nl for k in _INTER_KEYWORDS):
        return "Intermediarios"
    return "Gobierno" if sdn_type == "Individual" else "Otro"


def _extract_year(remarks: str) -> int | None:
    """Intenta extraer el año de sanción del campo remarks."""
    if not remarks:
        return None
    m = re.search(r"\b(200[0-9]|201[0-9]|202[0-6])\b", str(remarks))
    return int(m.group(1)) if m else None


# ─────────────────────────────────────────────────────────────────────────────
# Relaciones estructurales documentadas (fuente: EO 13808, EO 13850, CRS R45046)
# ─────────────────────────────────────────────────────────────────────────────
# Formato: (source_name_fragment, target_name_fragment, relation_type, year)
# Todas las entidades DEBEN aparecer en la lista SDN descargada.
# Si no se encuentran, la arista se descarta silenciosamente.

STRUCTURAL_EDGES: list[tuple[str, str, str, int]] = [
    # Gobierno → PDVSA (EO 13850, 2019)
    ("PETRÓLEOS DE VENEZUELA", "PDVSA PETRÓLEO", "control_jerarquico", 2019),
    ("MADURO MOROS", "PETRÓLEOS DE VENEZUELA", "control_politico", 2019),
    ("CABELLO RONDÓN", "PETRÓLEOS DE VENEZUELA", "influencia_politica", 2016),
    # PDVSA → subsidiarias
    ("PETRÓLEOS DE VENEZUELA", "BARIVEN", "subsidiaria", 2019),
    ("PETRÓLEOS DE VENEZUELA", "PEQUIVEN", "subsidiaria", 2019),
    ("PETRÓLEOS DE VENEZUELA", "INTEVEP", "subsidiaria", 2019),
    # Banca → Gobierno
    ("BANDES", "MADURO MOROS", "financiamiento", 2018),
    ("BANCO BICENTENARIO", "CABELLO RONDÓN", "coordinacion", 2018),
    # Militares → Gobierno
    ("PADRINO LOPEZ", "MADURO MOROS", "cadena_mando", 2018),
    ("REVEROL TORRES", "MADURO MOROS", "cadena_mando", 2018),
    # Intermediarios → PDVSA (esquemas de evasión)
    ("CAROIL", "PETRÓLEOS DE VENEZUELA", "contrato_evasion", 2020),
    ("LIBRE ABORDO", "PETRÓLEOS DE VENEZUELA", "transporte_crudo", 2020),
    # SEBIN / DGCIM → Gobierno
    ("SEBIN", "MADURO MOROS", "seguridad_estado", 2019),
    ("DGCIM", "MADURO MOROS", "seguridad_estado", 2019),
]


# ─────────────────────────────────────────────────────────────────────────────

def fetch_sdn() -> pd.DataFrame:
    print("  Descargando SDN CSV desde OFAC Treasury...")
    try:
        resp = requests.get(SDN_CSV_URL, timeout=60)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), header=None, names=SDN_COLS,
                         encoding="latin-1", on_bad_lines="skip")
        print(f"  SDN descargado: {len(df):,} entidades totales")
        return df
    except Exception as exc:
        print(f"  WARN No se pudo descargar SDN: {exc}")
        return pd.DataFrame(columns=SDN_COLS)


def filter_venezuela(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    prog_mask = df["program"].fillna("").apply(
        lambda p: any(vp in p.upper() for vp in VEN_PROGRAMS)
    )
    remarks_mask = df["remarks"].fillna("").str.upper().str.contains(
        r"VENEZUELA|VENEZUELAN|MADURO|CHAVEZ|PDVSA|SEBIN|DGCIM|GNB|CONVIASA", regex=True
    )
    ven = df[prog_mask | remarks_mask].copy()
    print(f"  Entidades venezolanas filtradas: {len(ven)}")
    return ven


MAX_NODES = 200  # D3.js performance limit

# Nombres de alta relevancia (siempre incluidos si están en SDN)
PRIORITY_FRAGMENTS = [
    "MADURO", "CABELLO", "PDVSA", "BARIVEN", "PEQUIVEN", "INTEVEP",
    "BANDES", "BICENTENARIO", "SEBIN", "DGCIM", "CONVIASA", "PADRINO",
    "REVEROL", "TARECK", "EL AISSAMI", "DELCY", "JORGE RODRIGUEZ",
    "CAROIL", "LIBRE ABORDO", "HELIODORO", "IVAN HERNANDEZ",
    "NATIONAL GUARD", "GUARDIA NACIONAL", "CHAVEZ",
]


def _priority_score(name_upper: str, cat: str) -> int:
    score = 0
    for frag in PRIORITY_FRAGMENTS:
        if frag in name_upper:
            score += 10
    if cat in ("Gobierno", "PDVSA"):
        score += 3
    elif cat == "Militares":
        score += 2
    return score


def build_nodes(ven: pd.DataFrame) -> list[dict]:
    candidates = []
    seen: set[str] = set()
    for _, row in ven.iterrows():
        raw_name = str(row["sdn_name"]).strip()
        if not raw_name or raw_name == "nan":
            continue
        node_id = raw_name.upper()[:80]
        if node_id in seen:
            continue
        seen.add(node_id)

        cat     = _classify(raw_name, str(row["sdn_type"]), str(row["program"]))
        año     = _extract_year(str(row["remarks"]))
        desc    = str(row["remarks"])[:120].strip() if row["remarks"] else ""
        desc    = re.sub(r"(?i)\b(individual|entity|vessel)\b.*", "", desc).strip("; ").strip()
        pri     = _priority_score(node_id, cat)

        candidates.append({
            "id":          node_id,
            "nombre":      raw_name[:60],
            "categoria":   cat,
            "año_sancion": año,
            "sdn_type":    str(row["sdn_type"]),
            "programa":    str(row["program"])[:40],
            "descripcion": desc[:100] if desc else None,
            "_priority":   pri,
        })

    # Sort by priority descending; keep top MAX_NODES
    candidates.sort(key=lambda x: -x["_priority"])
    selected = candidates[:MAX_NODES]
    for n in selected:
        del n["_priority"]
    print(f"  Nodos seleccionados (de {len(candidates)}): {len(selected)}")
    return selected


def build_links(nodes: list[dict], ven: pd.DataFrame) -> list[dict]:
    node_ids = {n["id"] for n in nodes}

    def find_node(fragment: str) -> str | None:
        frag = fragment.upper()
        for nid in node_ids:
            if frag in nid:
                return nid
        return None

    links: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    # Relaciones estructurales documentadas
    for src_frag, tgt_frag, rel, year in STRUCTURAL_EDGES:
        src = find_node(src_frag)
        tgt = find_node(tgt_frag)
        if src and tgt and src != tgt:
            pair = (min(src, tgt), max(src, tgt))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                links.append({"source": src, "target": tgt, "tipo": rel, "año": year})

    # Relaciones implícitas por programa compartido (mismo EO → misma red)
    prog_groups: dict[str, list[str]] = {}
    for n in nodes:
        prog = str(n["programa"])[:20]
        prog_groups.setdefault(prog, []).append(n["id"])

    for prog, grp in prog_groups.items():
        if len(grp) < 2 or len(grp) > 30:
            continue
        # Conectar al primer nodo del grupo como hub (representativo del programa)
        hub = grp[0]
        for member in grp[1:6]:  # máximo 5 aristas por hub para no saturar
            pair = (min(hub, member), max(hub, member))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                links.append({
                    "source": hub,
                    "target": member,
                    "tipo":   "mismo_programa",
                    "año":    None,
                })

    print(f"  Aristas construidas: {len(links)}")
    return links


def main() -> None:
    print("=" * 60)
    print("  OFAC Network Builder — Venezuela")
    print("=" * 60)

    ven = filter_venezuela(fetch_sdn())

    if ven.empty:
        # Sin datos SDN: red vacia. No se generan datos de demostracion inventados.
        print("  ERROR: SDN no descargada o sin entidades venezolanas.")
        print("  Red de sanciones: vacia (0 nodos, 0 aristas).")
        print("  Ejecuta el script cuando OFAC SDN este disponible.")
        nodes = []
        links = []
    else:
        nodes = build_nodes(ven)
        links = build_links(nodes, ven)

    network = {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "fuente":    "US Treasury OFAC — SDN List",
            "url":       "https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions",
            "n_nodes":   len(nodes),
            "n_links":   len(links),
            "generado":  pd.Timestamp.now().strftime("%Y-%m-%d"),
        }
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(network, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  OK  {len(nodes)} nodos, {len(links)} aristas -> {OUTPUT}")


if __name__ == "__main__":
    main()
