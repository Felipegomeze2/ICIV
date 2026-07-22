"""
Backfill paralelo de Black Marble — completa las 5 agregaciones + subnacional.

Driver de un solo uso: reprocesa en paralelo (varios meses a la vez) usando la
logica ya validada de fetch_blackmarble_monthly._process_month. Guardado
incremental con lock tras cada mes; reanudable (salta meses ya completos).

Uso:
    python scripts/backfill_blackmarble_parallel.py --workers 6 --start 2014-01
"""

from __future__ import annotations

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS.parent / "src"))

import fetch_blackmarble_monthly as bm  # noqa: E402

_LOCK = threading.Lock()


def _upsert(path: Path, new_rows: list[dict], keys: list[str]) -> None:
    df_new = pd.DataFrame(new_rows)
    if path.exists():
        old = pd.read_csv(path)
        proc = {(int(r["año"]), int(r["mes"])) for _, r in df_new.iterrows()}
        old = old[~old.apply(lambda r: (int(r["año"]), int(r["mes"])) in proc, axis=1)]
        df = pd.concat([old, df_new], ignore_index=True)
    else:
        df = df_new
    df = df.drop_duplicates(subset=keys, keep="last").sort_values(
        [k for k in keys if k in df.columns]).reset_index(drop=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _complete_months() -> set[str]:
    if not bm.OUTPUT.exists():
        return set()
    cur = pd.read_csv(bm.OUTPUT)
    cnt = cur.groupby(["año", "mes"])["variable"].nunique()
    return {f"{int(y)}-{int(m):02d}" for (y, m), n in cnt.items() if n >= len(bm._NAT_STATS)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--start", default=bm.DEFAULT_START)
    ap.add_argument("--limit", type=int, default=0, help="max meses por corrida (0 = todos)")
    ap.add_argument("--targets", default="", help="lista explicita YYYY-MM,YYYY-MM,... (ignora --start/--limit)")
    args = ap.parse_args()

    token = bm._load_token()
    if token is None:
        print("  [WARN] EARTHDATA_TOKEN no configurado. Nada que hacer.")
        return
    try:
        import h5py  # noqa: F401
    except ImportError:
        print("  [WARN] h5py no instalado.")
        return

    states = bm._state_names()
    done = _complete_months()
    if args.targets:
        want = [(int(t[:4]), int(t[5:7])) for t in args.targets.split(",") if t.strip()]
        pending = [(y, m) for (y, m) in want if f"{y}-{m:02d}" not in done]
    else:
        pending = [(y, m) for (y, m) in bm._candidate_months(args.start)
                   if f"{y}-{m:02d}" not in done]
    total_pend = len(pending)
    if args.limit > 0:
        pending = pending[:args.limit]
    print(f"  Pendientes totales: {total_pend} | esta corrida: {len(pending)} | workers: {args.workers}",
          flush=True)
    if not pending:
        print("  Todo completo.")
        return

    ok = 0
    fail = 0

    def _work(ym):
        y, m = ym
        return ym, bm._process_month(y, m, token, states)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_work, ym): ym for ym in pending}
        for fut in as_completed(futs):
            ym = futs[fut]
            try:
                _ym, res = fut.result()
            except Exception as exc:
                fail += 1
                print(f"  [ERROR] {ym[0]}-{ym[1]:02d}: {exc}")
                continue
            if not res:
                fail += 1
                continue
            with _LOCK:
                _upsert(bm.OUTPUT, res[0], ["año", "mes", "variable"])
                _upsert(bm.OUTPUT_STATES, res[1], ["año", "mes", "estado"])
                ok += 1
                print(f"  [{ok}/{len(pending)}] guardado {ym[0]}-{ym[1]:02d}")

    print(f"\n  Listo. OK={ok} fallidos={fail}")
    if bm.OUTPUT.exists():
        n = pd.read_csv(bm.OUTPUT)[["año", "mes"]].drop_duplicates().shape[0]
        print(f"  Nacional: {n} meses. Subnacional: "
              f"{pd.read_csv(bm.OUTPUT_STATES).shape[0]} filas.")


if __name__ == "__main__":
    main()
