"""v163: continue the ECS pressure d14 speed level-gated push.

v162 confirmed hidden transfer after raising the v57 850/925 blend from 0.35
to 0.50. This follow-up keeps the same levels and raises only those rows to a
0.65 blend toward the v55 shear/ws3 donor family, using v162 as the base.
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

VERSION = "v163"
BASE_VERSION = "v162"
ANCHOR_VERSION = "v53"
DONOR_VERSION = "v55"
PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
OUT_DIR = LOGS_DIR / "v163_pressure_d14_ecs_push65"

REGION = "east_china_sea"
TARGET_HORIZON = 14
UPGRADE_LEVELS = ["850", "925"]
STRONG_BLEND_LAMBDA = 0.65
Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
SURFACE_LEVELS = {"10m", "100m"}


def load_predictions(version: str) -> pd.DataFrame:
    path = PHASE1 / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, engine="python")


def pressure_d14_mask(frame: pd.DataFrame) -> pd.Series:
    level = frame["level"].astype(str)
    return (
        frame["type"].eq("grid")
        & frame["region"].eq(REGION)
        & frame["horizon"].astype(int).eq(TARGET_HORIZON)
        & ~level.isin(SURFACE_LEVELS)
    )


def upgrade_mask(frame: pd.DataFrame) -> pd.Series:
    return pressure_d14_mask(frame) & frame["level"].astype(str).isin(UPGRADE_LEVELS)


def repair_quantiles(frame: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    out = frame.copy()
    q = np.sort(out.loc[mask, Q_COLS].to_numpy(float), axis=1)
    q[:, 0] = np.maximum(q[:, 0], 0.0)
    out.loc[mask, Q_COLS] = q
    return out


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
    return {
        "speed_changed_rows_vs_base": int(q_changed.sum()),
        "direction_changed_rows": direction_changed,
        "non_target_speed_rows": non_target_q,
        "quantile_crossing_rows": crossing,
    }


def build_candidate() -> tuple[pd.DataFrame, dict]:
    base = load_predictions(BASE_VERSION)
    anchor = load_predictions(ANCHOR_VERSION)
    donor = load_predictions(DONOR_VERSION)
    if len(base) != len(anchor) or len(base) != len(donor):
        raise RuntimeError(f"Row mismatch: base={len(base)}, anchor={len(anchor)}, donor={len(donor)}")

    allowed = upgrade_mask(base)
    out = base.copy()
    for col in Q_COLS:
        out.loc[allowed, col] = (
            anchor.loc[allowed, col].astype(float)
            + STRONG_BLEND_LAMBDA * (donor.loc[allowed, col].astype(float) - anchor.loc[allowed, col].astype(float))
        )
    out = repair_quantiles(out, allowed)
    metrics = assert_scope(base, out, allowed)

    target = pressure_d14_mask(base)
    diagnostics = []
    for level, group_idx in base.loc[target].groupby(base.loc[target, "level"].astype(str)).groups.items():
        idx = list(group_idx)
        base_w = base.loc[idx, "q95"].astype(float) - base.loc[idx, "q05"].astype(float)
        cand_w = out.loc[idx, "q95"].astype(float) - out.loc[idx, "q05"].astype(float)
        row = {
            "level": str(level),
            "rows": int(len(idx)),
            "changed": bool(str(level) in UPGRADE_LEVELS),
            "base_width": float(base_w.mean()),
            "candidate_width": float(cand_w.mean()),
            "width_delta_vs_base": float((cand_w - base_w).mean()),
        }
        for col in Q_COLS:
            row[f"mean_delta_{col}_vs_base"] = float((out.loc[idx, col].astype(float) - base.loc[idx, col].astype(float)).mean())
        diagnostics.append(row)

    metrics.update(
        {
            "version": VERSION,
            "base_version": BASE_VERSION,
            "anchor_version": ANCHOR_VERSION,
            "donor_version": DONOR_VERSION,
            "blend_lambda": STRONG_BLEND_LAMBDA,
            "upgrade_levels": UPGRADE_LEVELS,
            "level_diagnostics": diagnostics,
        }
    )
    return out, metrics


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidate, metrics = build_candidate()
    zip_path = save_submission(candidate, VERSION)
    metrics["zip_path"] = str(zip_path)
    (OUT_DIR / "manifest.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    pd.DataFrame(metrics["level_diagnostics"]).to_csv(OUT_DIR / "level_diagnostics.csv", index=False)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
