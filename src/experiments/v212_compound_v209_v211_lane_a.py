"""v212: compound v207 + v209 (ECS press d7 dir Lane A) + v211 (NS press d7 dir Lane A).

Both Lane A wins in one submission:
  - v209: dir_pressure_d7_ecs 233.82 → 229.77 (-4.05 cWS, rank 3→2)
  - v211: dir_pressure_d7_ns  263.20 → 255.26 (-7.94 cWS, rank 3→1)

Disjoint cells. Should net both rank flips. Estimated mean rank improvement:
  v207 base: 3.500
  + v209 flip (-1 rank): 3.472
  + v211 flip (-2 ranks): 3.417
"""
from __future__ import annotations

import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import LOGS_DIR, PROJECT_ROOT  # noqa: E402
from src.pipeline.pipeline_utils import save_submission  # noqa: E402

VERSION = "v212"
PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
OUT_DIR = LOGS_DIR / f"{VERSION}_compound_v209_v211_lane_a"
Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]


def load_zip(version: str) -> pd.DataFrame:
    csv = PHASE1 / f"predictions_{version}.csv"
    if csv.exists():
        return pd.read_csv(csv, low_memory=False)
    z = PHASE1 / f"submission_{version}.zip"
    with zipfile.ZipFile(z) as zf:
        for n in zf.namelist():
            if n.endswith(".csv"):
                with zf.open(n) as f:
                    return pd.read_csv(BytesIO(f.read()), low_memory=False)
    raise FileNotFoundError(version)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading bases...")
    base = load_zip("v207")
    v209 = load_zip("v209")
    v211 = load_zip("v211")

    out = base.copy()

    # Overlay 1: v209 ECS press d7 dir
    m_ecs = (out["type"].eq("grid") & out["region"].eq("east_china_sea")
             & out["horizon"].astype(int).eq(7)
             & ~out["level"].astype(str).isin(["10m", "100m"]))
    out.loc[m_ecs, DIR_COLS] = v209.loc[m_ecs, DIR_COLS].to_numpy()

    # Overlay 2: v211 NS press d7 dir (OVERWRITES v207's v202 width-shrink)
    m_ns = (out["type"].eq("grid") & out["region"].eq("north_sea")
            & out["horizon"].astype(int).eq(7)
            & ~out["level"].astype(str).isin(["10m", "100m"]))
    out.loc[m_ns, DIR_COLS] = v211.loc[m_ns, DIR_COLS].to_numpy()

    # Validate scope
    total_target = m_ecs | m_ns
    q_changed = out[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = out[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int(q_changed.sum())
    non_target_dir = int((dir_changed & ~total_target).sum())
    if non_target_q or non_target_dir:
        raise RuntimeError(f"Scope violation: q={non_target_q} dir={non_target_dir}")
    q = out[Q_COLS].to_numpy(float)
    crossings = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if crossings:
        raise RuntimeError(f"Quantile crossings: {crossings}")
    # Confirm dir_50 frozen on target rows
    dir50_ecs = int(out.loc[m_ecs, "dir_50"].round(9).ne(base.loc[m_ecs, "dir_50"].round(9)).sum())
    dir50_ns = int(out.loc[m_ns, "dir_50"].round(9).ne(base.loc[m_ns, "dir_50"].round(9)).sum())

    metrics = {
        "version": VERSION,
        "base": "v207 (preserves v191 + v202 + v203 + v204)",
        "overlays": {
            "v209_ecs_press_d7_dir": int((dir_changed & m_ecs).sum()),
            "v211_ns_press_d7_dir":  int((dir_changed & m_ns).sum()),
        },
        "scope_checks": {
            "speed_changed_rows": non_target_q,
            "non_target_dir_rows": non_target_dir,
            "quantile_crossing_rows": crossings,
            "dir50_changed_ecs": dir50_ecs,
            "dir50_changed_ns": dir50_ns,
        },
        "expected_per_cell": {
            "dir_pressure_d7_ecs": "229.77 from v209 (rank 3->2)",
            "dir_pressure_d7_ns":  "255.26 from v211 (rank 3->1)",
            "other_cells": "preserved from v207",
        },
        "estimated_mean_rank": "~3.417 (v207 was 3.500, two rank flips * 1/36 = -0.083)",
    }

    zip_path = save_submission(out, VERSION)
    metrics["zip_path"] = str(zip_path)
    (OUT_DIR / "manifest.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved: {zip_path}")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
