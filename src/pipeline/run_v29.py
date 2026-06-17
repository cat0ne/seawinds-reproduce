"""V29: Baseline ECS surface d14 direction revert on top of v28.

The visible leaderboard still shows ECS surface d14 direction as a moderate
rank drag. The original light baseline scored slightly better on that exact
dimension than the current direction model, while the current model is better
elsewhere. This variant copies only ECS d14 surface-grid direction intervals
from `predictions_light.csv` and keeps every speed, station, pressure, and
other direction cell from v28.

Usage:
    python -m src.pipeline.run_v29
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission


DIR_COLS = ["dir_05", "dir_50", "dir_95"]
GRID_KEYS = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
SURFACE_LEVELS = {"10m", "100m"}


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def baseline_ecs_surface_d14_direction_revert(base: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """Return `base` with only ECS surface d14 direction from baseline."""
    out = base.copy()

    for df in (out, baseline):
        grid = df["type"].eq("grid")
        df.loc[grid, "latitude"] = df.loc[grid, "latitude"].astype(float).round(2)
        df.loc[grid, "longitude"] = df.loc[grid, "longitude"].astype(float).round(2)
        df.loc[grid, "horizon"] = df.loc[grid, "horizon"].astype(int)
        df.loc[grid, "hour"] = df.loc[grid, "hour"].astype(int)
        df.loc[grid, "level"] = df.loc[grid, "level"].astype(str)

    base_grid = out[out["type"].eq("grid")].copy()
    baseline_grid = baseline[baseline["type"].eq("grid")][GRID_KEYS + DIR_COLS].copy()
    baseline_grid = baseline_grid.rename(columns={col: f"{col}_baseline" for col in DIR_COLS})

    merged_grid = base_grid.merge(baseline_grid, on=GRID_KEYS, how="left", validate="one_to_one")
    target_mask = (
        merged_grid["region"].eq("east_china_sea")
        & merged_grid["horizon"].astype(int).eq(14)
        & merged_grid["level"].astype(str).isin(SURFACE_LEVELS)
    )
    missing = merged_grid.loc[target_mask, [f"{col}_baseline" for col in DIR_COLS]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"Baseline ECS surface d14 directions missing for {int(missing.sum())} rows")

    for col in DIR_COLS:
        merged_grid.loc[target_mask, col] = merged_grid.loc[target_mask, f"{col}_baseline"]
    out.loc[out["type"].eq("grid"), DIR_COLS] = merged_grid[DIR_COLS].values
    return out


def generate_v29() -> None:
    print("\n" + "=" * 60)
    print("Generating V29 submission (v28 + baseline ECS surface d14 direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v28.csv"))
    baseline = _load_predictions_csv(_phase1_path("predictions_light.csv"))
    submission = baseline_ecs_surface_d14_direction_revert(base, baseline)

    dir_changed = (
        base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)
    ).any(axis=1)
    speed_changed = (
        base[["q05", "q50", "q95"]].reset_index(drop=True)
        != submission[["q05", "q50", "q95"]].reset_index(drop=True)
    ).any(axis=1)
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  Grid direction rows changed: {int((dir_changed & submission['type'].eq('grid')).sum()):,}")
    print(f"  Station direction rows changed: {int((dir_changed & submission['type'].eq('station')).sum()):,}")
    print(f"  Speed rows changed: {int(speed_changed.sum()):,}")
    save_submission(submission, "v29")


if __name__ == "__main__":
    generate_v29()
