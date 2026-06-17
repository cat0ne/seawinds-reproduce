"""V27: Heavy-baseline grid-speed graft on top of v26.

The visible leaderboard shows the heavy baseline beating v26 on all grid-speed
families while v26 dominates stations and direction. This variant keeps v26 as
the submission base, replaces only grid `q05/q50/q95` from the official heavy
baseline predictions, and leaves all direction and station rows untouched.

Usage:
    python -m src.pipeline.run_v27
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import fix_crossing, save_submission


GRID_KEYS = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
SPEED_COLS = ["q05", "q50", "q95"]


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def heavy_grid_speed_graft(base: pd.DataFrame, heavy: pd.DataFrame) -> pd.DataFrame:
    """Return `base` with grid speed quantiles replaced from `heavy`.

    Matching is exact on the official grid key. Station rows and direction
    columns remain from `base`.
    """
    out = base.copy()

    for df in (out, heavy):
        grid = df["type"].eq("grid")
        df.loc[grid, "latitude"] = df.loc[grid, "latitude"].astype(float).round(2)
        df.loc[grid, "longitude"] = df.loc[grid, "longitude"].astype(float).round(2)
        df.loc[grid, "horizon"] = df.loc[grid, "horizon"].astype(int)
        df.loc[grid, "hour"] = df.loc[grid, "hour"].astype(int)
        df.loc[grid, "level"] = df.loc[grid, "level"].astype(str)

    base_grid = out[out["type"].eq("grid")].copy()
    heavy_grid = heavy[heavy["type"].eq("grid")][GRID_KEYS + SPEED_COLS].copy()
    heavy_grid = heavy_grid.rename(columns={col: f"{col}_heavy" for col in SPEED_COLS})

    merged_grid = base_grid.merge(heavy_grid, on=GRID_KEYS, how="left", validate="one_to_one")
    missing = merged_grid[[f"{col}_heavy" for col in SPEED_COLS]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"Heavy predictions missing for {int(missing.sum())} grid rows")

    for col in SPEED_COLS:
        merged_grid[col] = merged_grid[f"{col}_heavy"]
    merged_grid = merged_grid.drop(columns=[f"{col}_heavy" for col in SPEED_COLS])
    merged_grid = fix_crossing(merged_grid)

    out.loc[out["type"].eq("grid"), SPEED_COLS] = merged_grid[SPEED_COLS].values
    return out


def generate_v27() -> None:
    print("\n" + "=" * 60)
    print("Generating V27 submission (v26 + heavy grid speed)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v26.csv"))
    heavy = _load_predictions_csv(_phase1_path("predictions_heavy.csv"))
    submission = heavy_grid_speed_graft(base, heavy)

    changed_rows = (
        base[SPEED_COLS].reset_index(drop=True) != submission[SPEED_COLS].reset_index(drop=True)
    ).any(axis=1)
    print(f"  Speed rows changed: {int(changed_rows.sum()):,}")
    print(f"  Grid speed rows changed: {int((changed_rows & submission['type'].eq('grid')).sum()):,}")
    print(f"  Station rows changed: {int((changed_rows & submission['type'].eq('station')).sum()):,}")
    save_submission(submission, "v27")


if __name__ == "__main__":
    generate_v27()
