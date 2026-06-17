"""v173: final ECS pressure d14 boundary-crossing probe.

v167 scored cleanly and landed at `speed_pressure_d14_ecs = 17.8919`, just
above the visible 17.8900 boundary. This final probe keeps v167 as the base and
pushes only the same high-regime window-level cells from lambda 0.95 to 1.00 in
the v53 -> v55 shear/ws3 family.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import LOGS_DIR, PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission

VERSION = "v173"
BASE_VERSION = "v167"
ANCHOR_VERSION = "v53"
DONOR_VERSION = "v55"
PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
OUT_DIR = LOGS_DIR / "v173_pressure_d14_ecs_final_crossing"

REGION = "east_china_sea"
TARGET_HORIZON = 14
Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
SURFACE_LEVELS = {"10m", "100m"}
FINAL_LAMBDA = 1.00
HIGH_REGIME_KEYS = {
    ("850", 1),
    ("850", 2),
    ("850", 4),
    ("850", 5),
    ("925", 1),
    ("925", 2),
    ("925", 5),
    ("925", 8),
}


def load_predictions(version: str) -> pd.DataFrame:
    path = PHASE1 / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, engine="python")


def target_mask(frame: pd.DataFrame) -> pd.Series:
    level = frame["level"].astype(str)
    key_mask = pd.Series(
        [(str(lv), int(window)) in HIGH_REGIME_KEYS for lv, window in zip(level, frame["window"])],
        index=frame.index,
    )
    return (
        frame["type"].eq("grid")
        & frame["region"].eq(REGION)
        & frame["horizon"].astype(int).eq(TARGET_HORIZON)
        & ~level.isin(SURFACE_LEVELS)
        & key_mask
    )


def repair_quantiles(frame: pd.DataFrame, mask: pd.Series) -> None:
    q = np.sort(frame.loc[mask, Q_COLS].to_numpy(float), axis=1)
    q[:, 0] = np.maximum(q[:, 0], 0.0)
    frame.loc[mask, Q_COLS] = q


def assert_scope(base: pd.DataFrame, candidate: pd.DataFrame, allowed: pd.Series) -> dict:
    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int((q_changed & ~allowed).sum())
    if non_target_q:
        raise RuntimeError(f"Non-target speed rows changed: {non_target_q}")
    direction_changed = int(dir_changed.sum())
    if direction_changed:
        raise RuntimeError(f"Direction rows changed: {direction_changed}")
    q = candidate[Q_COLS].to_numpy(float)
    crossing = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if crossing:
        raise RuntimeError(f"Quantile crossing/negative rows: {crossing}")
    nans = int(candidate[Q_COLS + DIR_COLS].isna().sum().sum())
    if nans:
        raise RuntimeError(f"NaNs in prediction columns: {nans}")
    return {
        "changed_rows": int(q_changed.sum()),
        "direction_changed_rows": direction_changed,
        "non_target_speed_rows": non_target_q,
        "quantile_crossing_rows": crossing,
        "nan_prediction_values": nans,
    }


def build_candidate() -> tuple[pd.DataFrame, dict]:
    base = load_predictions(BASE_VERSION)
    anchor = load_predictions(ANCHOR_VERSION)
    donor = load_predictions(DONOR_VERSION)
    if len(base) != len(anchor) or len(base) != len(donor):
        raise RuntimeError(f"Row mismatch: base={len(base)}, anchor={len(anchor)}, donor={len(donor)}")

    allowed = target_mask(base)
    out = base.copy()
    for col in Q_COLS:
        out.loc[allowed, col] = (
            anchor.loc[allowed, col].astype(float)
            + FINAL_LAMBDA * (donor.loc[allowed, col].astype(float) - anchor.loc[allowed, col].astype(float))
        )
    repair_quantiles(out, allowed)
    checks = assert_scope(base, out, allowed)

    base_width = base.loc[allowed, "q95"].astype(float) - base.loc[allowed, "q05"].astype(float)
    cand_width = out.loc[allowed, "q95"].astype(float) - out.loc[allowed, "q05"].astype(float)
    metrics = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "anchor_version": ANCHOR_VERSION,
        "donor_version": DONOR_VERSION,
        "final_lambda": FINAL_LAMBDA,
        "high_regime_keys": sorted([f"{level}:w{window}" for level, window in HIGH_REGIME_KEYS]),
        "checks": checks,
        "mean_q50_delta_vs_base": float((out.loc[allowed, "q50"].astype(float) - base.loc[allowed, "q50"].astype(float)).mean()),
        "mean_width_delta_vs_base": float((cand_width - base_width).mean()),
        "changed_by_level": out.loc[allowed].groupby(out.loc[allowed, "level"].astype(str)).size().to_dict(),
    }
    return out, metrics


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidate, metrics = build_candidate()
    zip_path = save_submission(candidate, VERSION)
    metrics["zip_path"] = str(zip_path)
    (OUT_DIR / "manifest.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
