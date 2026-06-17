"""v207: Compound — v191 + v202 + v203 + v204.

Combines proven and unscored mechanisms across 3 non-overlapping direction cells:
- v191 base (already includes -1.18 cWS gain on dir_pressure_d7_ecs)
- + v202 dir_pressure_d7_ns (aggressive shrink, max_shrink=18 vs v198's 14)
- + v203 dir_surface_d7_ns (v191 mirror on surface levels)
- + v204 dir_stations_d14_ns (climatology widening)

All 4 cells are disjoint. 1 submission tests 3 new mechanisms with v191's gain preserved.
Per-cell leaderboard scores let us bisect any regression.

Scope-frozen: no speed columns change, no other direction cells change, dir_50 frozen on stations.
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

VERSION = "v207"
PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
OUT_DIR = LOGS_DIR / f"{VERSION}_compound_v191_v202_v203_v204"

Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]


def load_predictions_zip(version: str) -> pd.DataFrame:
    """Load predictions from either CSV or zip."""
    csv_path = PHASE1 / f"predictions_{version}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path, low_memory=False)
    zip_path = PHASE1 / f"submission_{version}.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                if n.endswith(".csv"):
                    with z.open(n) as f:
                        return pd.read_csv(BytesIO(f.read()), low_memory=False)
    raise FileNotFoundError(f"No predictions found for {version}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading base v191...")
    base = load_predictions_zip("v191")
    print(f"  v191 rows: {len(base):,}")

    print("\nLoading v202 (NS pressure d7 dir aggressive)...")
    v202 = load_predictions_zip("v202")
    print("Loading v203 (NS surface d7 dir)...")
    v203 = load_predictions_zip("v203")
    print("Loading v204 (stations d14 NS climatology widening)...")
    v204 = load_predictions_zip("v204")

    out = base.copy()

    # --- v202 overlay: grid NS pressure d7 direction ---
    m202 = (out["type"].eq("grid") & out["region"].eq("north_sea")
            & out["horizon"].astype(int).eq(7)
            & ~out["level"].astype(str).isin(["10m", "100m"]))
    print(f"\nv202 target rows: {int(m202.sum())}")
    out.loc[m202, DIR_COLS] = v202.loc[m202, DIR_COLS].to_numpy()

    # --- v203 overlay: grid NS surface d7 direction ---
    m203 = (out["type"].eq("grid") & out["region"].eq("north_sea")
            & out["horizon"].astype(int).eq(7)
            & out["level"].astype(str).isin(["10m", "100m"]))
    print(f"v203 target rows: {int(m203.sum())}")
    out.loc[m203, DIR_COLS] = v203.loc[m203, DIR_COLS].to_numpy()

    # --- v204 overlay: stations NS d14 direction ---
    m204 = (out["type"].eq("station") & out["region"].eq("north_sea")
            & out["horizon"].astype(int).eq(14))
    print(f"v204 target rows: {int(m204.sum())}")
    out.loc[m204, DIR_COLS] = v204.loc[m204, DIR_COLS].to_numpy()

    # --- Scope validation ---
    total_target_mask = m202 | m203 | m204
    q_changed = out[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = out[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int(q_changed.sum())
    non_target_dir = int((dir_changed & ~total_target_mask).sum())
    dir50_changed_stations = int((out.loc[m204, "dir_50"].round(9).ne(base.loc[m204, "dir_50"].round(9))).sum())

    if non_target_q:
        raise RuntimeError(f"Speed columns changed (should be 0): {non_target_q}")
    if non_target_dir:
        raise RuntimeError(f"Non-target direction rows changed: {non_target_dir}")
    if dir50_changed_stations:
        raise RuntimeError(f"Station dir_50 changed (frozen): {dir50_changed_stations}")
    q = out[Q_COLS].to_numpy(float)
    crossings = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if crossings:
        raise RuntimeError(f"Quantile crossings: {crossings}")

    # --- Per-cell change counts ---
    changes_v202 = int((dir_changed & m202).sum())
    changes_v203 = int((dir_changed & m203).sum())
    changes_v204 = int((dir_changed & m204).sum())
    # v191's own changes (preserved from base): dir_pressure_d7_ecs
    m191 = (out["type"].eq("grid") & out["region"].eq("east_china_sea")
            & out["horizon"].astype(int).eq(7)
            & ~out["level"].astype(str).isin(["10m", "100m"]))
    # v191 vs v173 — load v173 to verify v191's gain is preserved
    v173 = load_predictions_zip("v173")
    v191_kept_changes_vs_v173 = int(out.loc[m191, DIR_COLS].round(9).ne(v173.loc[m191, DIR_COLS].round(9)).any(axis=1).sum())

    metrics = {
        "version": VERSION,
        "base_version": "v191",
        "mechanism": "compound: v191 base + v202 (NS press d7 dir) + v203 (NS surf d7 dir) + v204 (stations d14 NS dir)",
        "non_overlap_assertion": "all 4 target masks are pairwise disjoint cells",
        "target_rows": {
            "v202_ns_press_d7": int(m202.sum()),
            "v203_ns_surf_d7":  int(m203.sum()),
            "v204_stations_d14_ns": int(m204.sum()),
        },
        "changed_rows": {
            "v202": changes_v202,
            "v203": changes_v203,
            "v204": changes_v204,
            "v191_preserved_vs_v173": v191_kept_changes_vs_v173,
        },
        "scope_checks": {
            "speed_changed_rows": non_target_q,
            "non_target_dir_rows": non_target_dir,
            "station_dir50_changed_rows": dir50_changed_stations,
            "quantile_crossing_rows": crossings,
        },
        "expected_cell_deltas": {
            "dir_pressure_d7_ns": "v202 may improve beyond v198's -2.61 cWS (max_shrink=18 instead of 14)",
            "dir_surface_d7_ns": "v203 first attempt on surface cell, gap +9 cWS to the leader",
            "dir_stations_d14_ns": "v204 climatology widening on flat-136deg base, gap +9.94 cWS to Breva",
            "dir_pressure_d7_ecs": "preserved from v191: 233.82 (v173 was 235.00)",
        },
    }

    zip_path = save_submission(out, VERSION)
    metrics["zip_path"] = str(zip_path)
    (OUT_DIR / "manifest.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved: {zip_path}")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
