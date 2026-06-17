"""V28: Narrow heavy-direction cherry-pick on top of v27.

After v27, the biggest visible drag is NS station direction d7. The official
heavy baseline is locally available and visibly better on NS d7 station
direction and NS d7 surface direction, while worse on several other direction
cells. This variant therefore copies only those two cells' direction intervals
from heavy and keeps every speed column plus all other directions from v27.

Usage:
    python -m src.pipeline.run_v28
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission


DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]
GRID_KEYS = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
SURFACE_LEVELS = {"10m", "100m"}


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def heavy_ns_d7_direction_cherry_pick(base: pd.DataFrame, heavy: pd.DataFrame) -> pd.DataFrame:
    """Return `base` with only NS d7 station/surface direction from heavy."""
    out = base.copy()

    station_mask = (
        out["type"].eq("station")
        & out["region"].eq("north_sea")
        & out["horizon"].astype(int).eq(7)
    )
    grid_mask = (
        out["type"].eq("grid")
        & out["region"].eq("north_sea")
        & out["horizon"].astype(int).eq(7)
        & out["level"].astype(str).isin(SURFACE_LEVELS)
    )

    station_heavy = heavy[heavy["type"].eq("station")].copy()
    station_heavy["horizon"] = station_heavy["horizon"].astype(int)
    station_fallback = station_heavy[STATION_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_heavy" for col in DIR_COLS}
    )
    out = out.merge(station_fallback, on=STATION_KEYS, how="left")
    missing_station = out.loc[station_mask, [f"{col}_heavy" for col in DIR_COLS]].isna().any(axis=1)
    if missing_station.any():
        raise ValueError(f"Heavy station directions missing for {int(missing_station.sum())} rows")
    for col in DIR_COLS:
        out.loc[station_mask, col] = out.loc[station_mask, f"{col}_heavy"]
    out = out.drop(columns=[f"{col}_heavy" for col in DIR_COLS])

    heavy_grid = heavy[heavy["type"].eq("grid")].copy()
    for df in (out, heavy_grid):
        grid = df["type"].eq("grid")
        df.loc[grid, "latitude"] = df.loc[grid, "latitude"].astype(float).round(2)
        df.loc[grid, "longitude"] = df.loc[grid, "longitude"].astype(float).round(2)
        df.loc[grid, "horizon"] = df.loc[grid, "horizon"].astype(int)
        df.loc[grid, "hour"] = df.loc[grid, "hour"].astype(int)
        df.loc[grid, "level"] = df.loc[grid, "level"].astype(str)

    base_grid = out[out["type"].eq("grid")].copy()
    grid_fallback = heavy_grid[GRID_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_heavy" for col in DIR_COLS}
    )
    merged_grid = base_grid.merge(grid_fallback, on=GRID_KEYS, how="left", validate="one_to_one")
    merged_grid_mask = (
        merged_grid["region"].eq("north_sea")
        & merged_grid["horizon"].astype(int).eq(7)
        & merged_grid["level"].astype(str).isin(SURFACE_LEVELS)
    )
    missing_grid = merged_grid.loc[merged_grid_mask, [f"{col}_heavy" for col in DIR_COLS]].isna().any(axis=1)
    if missing_grid.any():
        raise ValueError(f"Heavy grid directions missing for {int(missing_grid.sum())} rows")
    for col in DIR_COLS:
        merged_grid.loc[merged_grid_mask, col] = merged_grid.loc[merged_grid_mask, f"{col}_heavy"]

    out.loc[out["type"].eq("grid"), DIR_COLS] = merged_grid[DIR_COLS].values
    return out


def generate_v28() -> None:
    print("\n" + "=" * 60)
    print("Generating V28 submission (v27 + heavy NS d7 direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v27.csv"))
    heavy = _load_predictions_csv(_phase1_path("predictions_heavy.csv"))
    submission = heavy_ns_d7_direction_cherry_pick(base, heavy)

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
    save_submission(submission, "v28")


if __name__ == "__main__":
    generate_v28()
