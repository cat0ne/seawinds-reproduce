"""V35: Cherry-pick v32's winning NS d1 station-direction cell.

V32 was rejected overall, but its station direction bias correction won one
visible rank-moving cell: ``dir_stations_d1_ns``. This variant starts from
v31 and copies only v32 station direction columns for North Sea horizon d1.
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


def cherry_pick_v32_ns_d1_station_direction(base: pd.DataFrame, v32: pd.DataFrame) -> pd.DataFrame:
    """Return base with only v32's NS d1 station direction copied in."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    v32_station = v32[v32["type"].eq("station")].copy()
    v32_station["horizon"] = v32_station["horizon"].astype(int)
    v32_station["hour"] = v32_station["hour"].astype(int)

    donor = v32_station[STATION_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_v32" for col in DIR_COLS}
    )
    merged = out.merge(donor, on=STATION_KEYS, how="left")
    target = (
        merged["type"].eq("station")
        & merged["region"].eq("north_sea")
        & merged["horizon"].eq(1)
    )
    missing = merged.loc[target, [f"{col}_v32" for col in DIR_COLS]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"V32 station direction missing for {int(missing.sum())} NS d1 rows")

    for col in DIR_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_v32"]
    return merged.drop(columns=[f"{col}_v32" for col in DIR_COLS])


def assert_v35_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)
    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    allowed = (
        cand_aligned["type"].eq("station")
        & cand_aligned["region"].eq("north_sea")
        & cand_aligned["horizon"].astype(int).eq(1)
    )
    unexpected = dir_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected direction changes outside NS d1 station scope: {int(unexpected.sum())}")

    changed = int((dir_changed & allowed).sum())
    if changed == 0:
        raise ValueError("Expected at least one NS d1 station direction row to change")


def generate_v35() -> None:
    print("\n" + "=" * 60)
    print("Generating V35 submission (v32 NS d1 station-direction cherry-pick)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v31.csv"))
    v32 = _load_predictions_csv(_phase1_path("predictions_v32.csv"))
    submission = cherry_pick_v32_ns_d1_station_direction(base, v32)
    assert_v35_scope(base, submission)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    print(f"  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  NS d1 station rows changed: {int((dir_changed & submission['type'].eq('station')).sum()):,}")
    save_submission(submission, "v35")


if __name__ == "__main__":
    generate_v35()
