"""V41: gated Track I ECS d7 station-direction candidate.

V39 proved Track I transfers for ECS d1 station direction. V40 showed that
ungated ECS d7/d14 expansion is unsafe, especially d14. V41 starts from v39
and applies Track I only to ECS d7 station rows whose candidate is a small,
sane correction relative to the v39 baseline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission
from src.scoring.winkler import _circ_dist


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]
TARGET_REGION = "east_china_sea"
TARGET_HORIZON = 7
MAX_CENTER_SHIFT = 20.0
MIN_WIDTH = 70.0
MAX_WIDTH = 170.0


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def _interval_width(frame: pd.DataFrame, suffix: str = "") -> np.ndarray:
    lo = frame[f"dir_05{suffix}"].to_numpy(dtype=float)
    hi = frame[f"dir_95{suffix}"].to_numpy(dtype=float)
    return (hi - lo) % 360.0


def apply_gated_track_i_ecs_d7(
    base: pd.DataFrame,
    candidate_source: pd.DataFrame,
    max_center_shift: float = MAX_CENTER_SHIFT,
    min_width: float = MIN_WIDTH,
    max_width: float = MAX_WIDTH,
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Copy Track I ECS d7 direction only for rows passing sanity gates."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)

    cand = candidate_source.copy()
    cand["horizon"] = cand["horizon"].astype(int)
    cand["hour"] = cand["hour"].astype(int)
    cand_station = cand[cand["type"].eq("station")].copy()
    if cand_station.duplicated(STATION_KEYS).any():
        raise ValueError(f"Candidate source has duplicate station keys: {int(cand_station.duplicated(STATION_KEYS).sum())}")
    donor = cand_station[STATION_KEYS + DIR_COLS].rename(columns={col: f"{col}_cand" for col in DIR_COLS})
    merged = out.merge(donor, on=STATION_KEYS, how="left")

    requested = (
        merged["type"].eq("station")
        & merged["region"].eq(TARGET_REGION)
        & merged["horizon"].eq(TARGET_HORIZON)
    )
    missing = requested & merged["dir_50_cand"].isna()
    if missing.any():
        raise ValueError(f"Candidate source missing for {int(missing.sum())} ECS d7 station rows")

    shift = np.full(len(merged), np.nan)
    width = np.full(len(merged), np.nan)
    req_idx = requested.to_numpy()
    shift[req_idx] = _circ_dist(
        merged.loc[requested, "dir_50"].to_numpy(dtype=float),
        merged.loc[requested, "dir_50_cand"].to_numpy(dtype=float),
    )
    width[req_idx] = (
        merged.loc[requested, "dir_95_cand"].to_numpy(dtype=float)
        - merged.loc[requested, "dir_05_cand"].to_numpy(dtype=float)
    ) % 360.0

    gate = (
        requested
        & (pd.Series(shift, index=merged.index) <= max_center_shift)
        & (pd.Series(width, index=merged.index) >= min_width)
        & (pd.Series(width, index=merged.index) <= max_width)
    )

    for col in DIR_COLS:
        merged.loc[gate, col] = merged.loc[gate, f"{col}_cand"]

    metrics = {
        "requested_rows": int(requested.sum()),
        "accepted_rows": int(gate.sum()),
        "rejected_rows": int(requested.sum() - gate.sum()),
        "max_center_shift": float(max_center_shift),
        "min_width": float(min_width),
        "max_width": float(max_width),
    }
    result = merged.drop(columns=[f"{col}_cand" for col in DIR_COLS])
    return result, metrics


def assert_v41_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    allowed = (
        cand_aligned["type"].eq("station")
        & cand_aligned["region"].eq(TARGET_REGION)
        & cand_aligned["horizon"].astype(int).eq(TARGET_HORIZON)
    )
    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    unexpected = dir_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected direction changes outside ECS d7 station scope: {int(unexpected.sum())}")

    changed = int((dir_changed & allowed).sum())
    if changed == 0:
        raise ValueError("Expected at least one gated ECS d7 station direction row to change")


def generate_v41() -> None:
    print("\n" + "=" * 60)
    print("Generating V41 submission (gated Track I ECS d7 station direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v39.csv"))
    v40 = _load_predictions_csv(_phase1_path("predictions_v40.csv"))
    submission, metrics = apply_gated_track_i_ecs_d7(base, v40)
    assert_v41_scope(base, submission)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"  Requested ECS d7 rows: {metrics['requested_rows']:,}")
    print(f"  Accepted gated rows: {metrics['accepted_rows']:,}")
    print(f"  Rejected gated rows: {metrics['rejected_rows']:,}")
    print(f"  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  NaNs in prediction columns: {int(nans)}")
    save_submission(submission, "v41")


if __name__ == "__main__":
    generate_v41()
