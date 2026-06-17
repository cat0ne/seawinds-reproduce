"""V31: Cleaned station-speed gains plus held ECS surface d14 direction gain.

V30 improved aggregate station speed but had two small station-speed
regressions. This variant starts from v28, keeps only the v30 station-speed
winners (NS d7 and ECS d1), then applies the held v29 ECS surface d14
direction donor from the light baseline. It is compound by design to save a
submission slot, but each component is independently scoped.

Usage:
    python -m src.pipeline.run_v31
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission
from src.pipeline.run_v29 import baseline_ecs_surface_d14_direction_revert


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]
WINNING_STATION_SPEED_CELLS = {
    ("north_sea", 7),
    ("east_china_sea", 1),
}


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def winning_station_speed_cherry_pick(base: pd.DataFrame, v30: pd.DataFrame) -> pd.DataFrame:
    """Return `base` with only v30's winning station-speed cells copied in."""
    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)

    v30_station = v30[v30["type"].eq("station")].copy()
    v30_station["horizon"] = v30_station["horizon"].astype(int)
    v30_station["hour"] = v30_station["hour"].astype(int)
    donor = v30_station[STATION_KEYS + Q_COLS].rename(
        columns={col: f"{col}_v30" for col in Q_COLS}
    )

    merged = out.merge(donor, on=STATION_KEYS, how="left")
    target = merged["type"].eq("station") & (
        ((merged["region"] == "north_sea") & (merged["horizon"].eq(7)))
        | ((merged["region"] == "east_china_sea") & (merged["horizon"].eq(1)))
    )
    missing = merged.loc[target, [f"{col}_v30" for col in Q_COLS]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"V30 station speed missing for {int(missing.sum())} target rows")

    for col in Q_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_v30"]
    return merged.drop(columns=[f"{col}_v30" for col in Q_COLS])


def generate_v31() -> None:
    print("\n" + "=" * 60)
    print("Generating V31 submission (clean v30 station winners + v29 ECS d14 direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v28.csv"))
    v30 = _load_predictions_csv(_phase1_path("predictions_v30.csv"))
    light = _load_predictions_csv(_phase1_path("predictions_light.csv"))

    station_clean = winning_station_speed_cherry_pick(base, v30)
    submission = baseline_ecs_surface_d14_direction_revert(station_clean, light)

    q_changed = (
        base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)
    ).any(axis=1)
    dir_changed = (
        base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)
    ).any(axis=1)
    allowed_q = submission["type"].eq("station") & (
        ((submission["region"] == "north_sea") & (submission["horizon"].astype(int).eq(7)))
        | ((submission["region"] == "east_china_sea") & (submission["horizon"].astype(int).eq(1)))
    )
    allowed_dir = submission["type"].eq("grid") & (
        submission["region"].eq("east_china_sea")
        & submission["horizon"].astype(int).eq(14)
        & submission["level"].astype(str).isin({"10m", "100m"})
    )
    unexpected_q = q_changed & ~allowed_q
    unexpected_dir = dir_changed & ~allowed_dir
    if unexpected_q.any():
        raise ValueError(f"Unexpected speed changes outside v31 scope: {int(unexpected_q.sum())}")
    if unexpected_dir.any():
        raise ValueError(f"Unexpected direction changes outside v31 scope: {int(unexpected_dir.sum())}")

    print(f"  Station speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  Grid direction rows changed: {int((dir_changed & submission['type'].eq('grid')).sum()):,}")
    save_submission(submission, "v31")


if __name__ == "__main__":
    generate_v31()
