"""V36: Cherry-pick v34's winning ECS d1 station-speed cell.

V34 failed as a broad Track E station-speed overlay, but it improved one
cell: ``speed_stations_d1_ecs``. This variant starts from v35 and copies only
v34 station speed columns for East China Sea horizon d1.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def cherry_pick_v34_ecs_d1_station_speed(base: pd.DataFrame, v34: pd.DataFrame) -> pd.DataFrame:
    """Return base with only v34's ECS d1 station speed copied in."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    v34_station = v34[v34["type"].eq("station")].copy()
    v34_station["horizon"] = v34_station["horizon"].astype(int)
    v34_station["hour"] = v34_station["hour"].astype(int)

    donor = v34_station[STATION_KEYS + Q_COLS].rename(
        columns={col: f"{col}_v34" for col in Q_COLS}
    )
    merged = out.merge(donor, on=STATION_KEYS, how="left")
    target = (
        merged["type"].eq("station")
        & merged["region"].eq("east_china_sea")
        & merged["horizon"].eq(1)
    )
    missing = merged.loc[target, [f"{col}_v34" for col in Q_COLS]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"V34 station speed missing for {int(missing.sum())} ECS d1 rows")

    for col in Q_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_v34"]
    return merged.drop(columns=[f"{col}_v34" for col in Q_COLS])


def assert_v36_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    if dir_changed.any():
        raise ValueError(f"Unexpected direction changes: {int(dir_changed.sum())}")

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    allowed = (
        cand_aligned["type"].eq("station")
        & cand_aligned["region"].eq("east_china_sea")
        & cand_aligned["horizon"].astype(int).eq(1)
    )
    unexpected = q_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected speed changes outside ECS d1 station scope: {int(unexpected.sum())}")

    changed = int((q_changed & allowed).sum())
    expected = int(allowed.sum())
    if changed != expected:
        raise ValueError(f"Expected all ECS d1 station rows to change, got {changed}/{expected}")


def generate_v36() -> None:
    print("\n" + "=" * 60)
    print("Generating V36 submission (v34 ECS d1 station-speed cherry-pick)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v35.csv"))
    v34 = _load_predictions_csv(_phase1_path("predictions_v34.csv"))
    submission = cherry_pick_v34_ecs_d1_station_speed(base, v34)
    assert_v36_scope(base, submission)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    print(f"  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  ECS d1 station rows changed: {int((q_changed & submission['type'].eq('station')).sum()):,}")
    save_submission(submission, "v36")


if __name__ == "__main__":
    generate_v36()
