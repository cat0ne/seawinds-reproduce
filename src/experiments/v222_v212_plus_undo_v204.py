"""v222: v212 plus the v204 undo on North Sea station d14 direction.

The live 2026-06-04 board makes v212's likely weakness clearer: v212 is based
on v207, so it preserves the v204 station d14 NS widening that lost raw cWS and
now costs visible ranks. This compound keeps the two confirmed Lane A pressure
d7 overlays from v212 and restores only the station d14 NS direction endpoints
from the promoted v196 base.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS_DIR = ROOT / "submissions"
LOGS_DIR = ROOT / "logs"

VERSION = "v222"
BASE_VERSION = "v212"
OUT_DIR = LOGS_DIR / f"{VERSION}_v212_plus_undo_v204"

Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
PRED_COLS = Q_COLS + DIR_COLS
SUB_COLS = [
    "type",
    "window",
    "region",
    "latitude",
    "longitude",
    "station",
    "horizon",
    "hour",
    "level",
    "q05",
    "q50",
    "q95",
    "dir_05",
    "dir_50",
    "dir_95",
]


def load_predictions(version: str) -> pd.DataFrame:
    path = SUBMISSIONS_DIR / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, low_memory=False)


def diff_checks(
    base: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    allowed_dir: pd.Series,
) -> dict[str, int]:
    if len(base) != len(candidate):
        raise RuntimeError(f"Row count changed: {len(base)} -> {len(candidate)}")

    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int(q_changed.sum())
    non_target_dir = int((dir_changed & ~allowed_dir).sum())
    q50_changed = int(candidate["q50"].round(9).ne(base["q50"].round(9)).sum())
    dir50_changed = int(candidate["dir_50"].round(9).ne(base["dir_50"].round(9)).sum())
    if non_target_q or non_target_dir:
        raise RuntimeError(f"Non-target changes: q={non_target_q} dir={non_target_dir}")
    if q50_changed or dir50_changed:
        raise RuntimeError(f"Center changed: q50={q50_changed} dir50={dir50_changed}")

    q = candidate[Q_COLS].to_numpy(dtype=float)
    quantile_crossings = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if quantile_crossings:
        raise RuntimeError(f"Quantile crossing/negative rows: {quantile_crossings}")
    nans = int(candidate[PRED_COLS].isna().sum().sum())
    if nans:
        raise RuntimeError(f"NaN prediction values: {nans}")

    return {
        "quantile_crossing_rows": quantile_crossings,
        "nan_prediction_values": nans,
        "changed_rows": int((q_changed | dir_changed).sum()),
        "speed_changed_rows": int(q_changed.sum()),
        "direction_changed_rows": int(dir_changed.sum()),
        "non_target_q_rows": non_target_q,
        "non_target_dir_rows": non_target_dir,
        "q50_changed_rows": q50_changed,
        "dir50_changed_rows": dir50_changed,
    }


def save_submission(frame: pd.DataFrame, version: str) -> Path:
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = SUBMISSIONS_DIR / f"predictions_{version}.csv"
    zip_path = SUBMISSIONS_DIR / f"submission_{version}.zip"
    frame[SUB_COLS].to_csv(csv_path, index=False)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname="predictions.csv")
    return zip_path


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("station")
        & frame["region"].eq("north_sea")
        & frame["horizon"].astype(int).eq(14)
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_predictions(BASE_VERSION)
    source = load_predictions("v196")
    target = target_mask(base)
    print(f"Target rows: {int(target.sum())}")

    out = base.copy()
    out.loc[target, DIR_COLS] = source.loc[target, DIR_COLS].to_numpy()

    checks = diff_checks(base, out, allowed_dir=target)
    manifest = {
        "target_dimension": "dir_stations_d14_ns",
        "mechanism": "v212 plus v204 undo; restore v196 station d14 NS direction endpoints",
        "base_rationale": "v212 contains confirmed v209/v211 Lane A pressure d7 overlays but preserves v207/v204 station d14 NS regression.",
        "source_version": "v196",
        "target_rows": int(target.sum()),
        "expected_live_board_effect_2026_06_04": {
            "dir_pressure_d7_ecs": "preserve v212/v209 improvement, expected current-board rank 4 -> 3 versus v196",
            "dir_pressure_d7_ns": "preserve v212/v211 improvement, expected current-board rank 4 -> 2 versus v196",
            "dir_stations_d14_ns": "recover v204 loss, expected current-board rank 7 -> 5 versus v212/v221-style v204 state",
            "net_rank_delta_vs_v196_estimate": "-3 ranks across 36 cells if v212 pressure gains transfer and station d14 restore behaves as v196",
        },
        "checks": checks,
        "wrote_submission": True,
    }
    zip_path = save_submission(out, VERSION)
    payload = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        **manifest,
        "zip_path": str(zip_path),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**manifest, "zip_path": str(zip_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
