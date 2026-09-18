"""Reproducible source comparison; never overwrites raw observations.

Pinned official vintages, archived response bytes and per-cell comparisons.
Run --refresh to retrieve again; default reuses SHA-verified evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
EVIDENCE = ROOT / "data/sources/audit_20260917"
URLS = {
    "cpi2025.xlsx": "https://images.transparencycdn.org/images/CPI2025_Results.xlsx",
    "weo_apr2026.xlsx": "https://data.imf.org/-/media/iData/External-Storage/Documents/2F78EE59F79143A7921E5E203D3AAA80/en/WEOApr2026all.xlsx",
    "wjp2025.xlsx": "https://worldjusticeproject.org/rule-of-law-index/downloads/2025_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
    "fh2013_2024.xlsx": "https://freedomhouse.org/sites/default/files/2024-02/All_data_FIW_2013-2024.xlsx",
    "fh2025.html": "https://freedomhouse.org/country/venezuela/freedom-world/2025",
    "fh2026.html": "https://freedomhouse.org/country/venezuela/freedom-world/2026",
    "hdi_owid.csv": "https://ourworldindata.org/grapher/human-development-index.csv",
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def retrieve(name, refresh=False):
    path = EVIDENCE / name
    meta_path = EVIDENCE / (name + ".json")
    if path.exists() and meta_path.exists() and not refresh:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["sha256"] != digest(path) or meta["url"] != URLS[name]:
            raise ValueError(f"Evidence mismatch: {name}")
        return path
    response = requests.get(URLS[name], timeout=120,
                            headers={"User-Agent": "Mozilla/5.0 ICIV academic source audit"})
    response.raise_for_status()
    path.write_bytes(response.content)
    meta_path.write_text(json.dumps({"url": URLS[name], "retrieved_at": datetime.now(timezone.utc).isoformat(),
                                    "sha256": digest(path)}, indent=2), encoding="utf-8")
    return path

def cpi_values(path):
    """Read the official Strict OOXML workbook without modifying its bytes.

    openpyxl does not support its Strict namespaces. Resolve the named sheet
    through workbook relationships, then read published cached cell values.
    """
    with ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/workbook.xml"))
        ns = {"m": root.tag.split("}")[0][1:]}
        shared = ET.fromstring(z.read("xl/sharedStrings.xml"))
        strings = ["".join(t.text or "" for t in s.findall(".//m:t", ns)) for s in shared]
        sheet = next(s for s in root.findall(".//m:sheet", ns) if s.get("name") == "CPI Timeseries 2012 - 2025")
        rel_id = next(v for k, v in sheet.attrib.items() if k.endswith("}id"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == rel_id)
        rows = []
        for row in ET.fromstring(z.read("xl/" + target)).findall(".//m:row", ns):
            cells = {}
            for cell in row:
                value = cell.findtext("m:v", default="", namespaces=ns)
                if cell.get("t") == "s" and value:
                    value = strings[int(value)]
                cells[re.sub(r"\d", "", cell.get("r"))] = value
            rows.append(cells)
        header = next(r for r in rows if r.get("B") == "ISO3")
        ven = [r for r in rows if r.get("B") == "VEN"]
        if len(ven) != 1:
            raise ValueError("CPI requires one Venezuela row")
        values = {int(label.strip()[-4:]): float(ven[0][col]) for col, label in header.items()
                  if re.fullmatch(r"CPI score 20\d\d", label.strip(), flags=re.IGNORECASE)}
        if set(values) != set(range(2012, 2026)):
            raise ValueError("Incomplete CPI comparable history in official workbook")
        return values

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    records, checks, issues = [], [], []

    def compare(raw_name, variable, official, evidence_name, tolerance=1e-9, states=None, publication=None):
        raw_path = ROOT / "data/raw" / raw_name
        raw = pd.read_csv(raw_path)
        local = raw[raw.indicador.eq(variable)].set_index("año").valor if "indicador" in raw else raw.set_index("año")[variable]
        for year, value in official.items():
            stored = local.get(year, np.nan)
            match = pd.notna(stored) and np.isfinite(value) and abs(float(stored) - value) <= tolerance
            checks.append({"archivo": raw_name, "variable": variable, "año": year, "valor_local": stored,
                           "valor_oficial": value, "tolerancia_absoluta": tolerance,
                           "coincide": bool(match), "evidencia": evidence_name})
            if match:
                records.append({"archivo_origen": raw_name, "variable": variable, "año": year,
                                "valor_verificado": stored, "raw_sha256": digest(raw_path),
                                "raw_canonical_lf_sha256": hashlib.sha256(raw_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                                "estado_observacion": states.get(year) if states else "indice_publicado_verificado; no es medicion directa",
                                "fecha_publicacion": publication,
                                "evidencia": evidence_name, "evidence_sha256": digest(EVIDENCE / evidence_name),
                                "url": URLS[evidence_name]})

    for source in ("cpi", "weo", "wjp", "fh", "hdi"):
        try:
            if source == "cpi":
                compare("cpi.csv", "cpi_score", cpi_values(retrieve("cpi2025.xlsx", args.refresh)), "cpi2025.xlsx", publication="2026-02-10")
            elif source == "weo":
                data = pd.read_excel(retrieve("weo_apr2026.xlsx", args.refresh), sheet_name="Countries")
                ven = data[data["COUNTRY.ID"].eq("VEN")]
                mapping = {"PCPIPCH": "inflacion_ipc_imf_pct", "LUR": "desempleo_pct",
                           "BCA_NGDPD": "cuenta_corriente_pct_pib", "NGDP_RPCH": "pib_crecimiento_imf_pct"}
                selected = ven[ven["INDICATOR.ID"].isin(mapping)].copy()
                selected.to_csv(EVIDENCE / "weo_venezuela_metadata.csv", index=False)
                for code, var in mapping.items():
                    row = selected[selected["INDICATOR.ID"].eq(code)].iloc[0]
                    last = int(row["LATEST_ACTUAL_ANNUAL_DATA"])
                    vals = {y: float(row[y]) for y in range(2000, 2027) if pd.notna(row[y])}
                    states = {y: ("WEO_historico_segun_proveedor_revisable" if last > 0 and y <= last else "WEO_estimacion_o_proyeccion_del_FMI") for y in vals}
                    compare("imf.csv", var, vals, "weo_apr2026.xlsx", tolerance=0.0500001,
                            states=states, publication=row["PUBLICATION_DATE"])
            elif source == "wjp":
                from fetch_wjp import _expand_edition_years
                data = pd.read_excel(retrieve("wjp2025.xlsx", args.refresh), sheet_name="Historical Data")
                ven = data[data["Country Code"].eq("VEN")]
                score = next(c for c in data if "overall score" in str(c).lower())
                vals = {y: float(r[score]) for _, r in ven.iterrows() for y in _expand_edition_years(r["Year"])}
                compare("wjp.csv", "wjp_rule_of_law", vals, "wjp2025.xlsx", tolerance=0.00005001)
            elif source == "fh":
                path = retrieve("fh2013_2024.xlsx", args.refresh)
                x = pd.ExcelFile(path)
                sheet = next(s for s in x.sheet_names if "FIW" in s.upper())
                d = pd.read_excel(path, sheet_name=sheet, header=1)
                country = next(c for c in d if "Country" in str(c))
                d = d[d[country].eq("Venezuela")]
                compare("freedom_house.csv", "freedom_house_score", {int(r.Edition)-1: float(r.Total) for _,r in d.iterrows()}, "fh2013_2024.xlsx")
                for edition in (2025, 2026):
                    name = f"fh{edition}.html"
                    html = retrieve(name, args.refresh).read_text(encoding="utf-8")
                    match = re.search(r'<div class="country-score">\s*(\d+)\s*</div>', html)
                    if match is None:
                        raise ValueError(f"Missing aggregate score: {name}")
                    compare("freedom_house.csv", "freedom_house_score", {edition-1: float(match.group(1))}, name)
            else:
                d = pd.read_csv(retrieve("hdi_owid.csv", args.refresh))
                d = d[d.Code.eq("VEN")]
                val = next(c for c in d if c not in ("Entity", "Code", "Year"))
                compare("hdi.csv", "hdi", {int(r.Year): float(r[val]) for _,r in d.iterrows() if 2000 <= r.Year <= 2023}, "hdi_owid.csv", tolerance=0.00050001)
        except Exception as exc:
            issues.append({"source": source, "status": "verification_failed", "error": f"{type(exc).__name__}: {exc}"})
    pd.DataFrame(checks).to_csv(EVIDENCE / "comparisons.csv", index=False)
    pd.DataFrame(records).to_csv(EVIDENCE / "verified_observations.csv", index=False)
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "compared": len(checks),
               "matching": sum(c["coincide"] for c in checks), "issues": issues,
               "scope": "CPI>=2012; WJP; FH>=2012; HDI via OWID; IMF WEO. Other sources not certified by this audit.",
               "tolerance_policy": "IMF raw 1 decimal: half rounding unit; WJP 4 decimals; HDI 3 decimals. CPI/FH exact."}
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if issues or summary["matching"] != summary["compared"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
