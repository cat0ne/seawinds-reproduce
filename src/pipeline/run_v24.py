"""V24: Selective ensemble — average v16 with baseline using weighted blending.

Grid speed: weighted mean of q05/q50/q95 (v16 weight=0.7, baseline weight=0.3).
Grid direction: circular weighted average of centres + weighted average of half-widths.
Stations: keep v16 as-is (height correction already applied).

Usage: python src/pipeline/run_v24.py [--weight 0.7]
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from src.pipeline.pipeline_utils import (
    apply_height_correction,
    fix_crossing,
    load_baseline,
    save_submission,
)
from src.pipeline.run_v16 import generate_v16


def circular_weighted_avg(angles1: np.ndarray, angles2: np.ndarray, w1: float = 0.7) -> np.ndarray:
    rad1 = np.deg2rad(angles1)
    rad2 = np.deg2rad(angles2)
    sin_avg = w1 * np.sin(rad1) + (1 - w1) * np.sin(rad2)
    cos_avg = w1 * np.cos(rad1) + (1 - w1) * np.cos(rad2)
    return np.rad2deg(np.arctan2(sin_avg, cos_avg)) % 360.0


def circular_half_width(lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
    return ((hi - lo) % 360) / 2.0


def ensemble_speed(v16: pd.DataFrame, bl: pd.DataFrame, w1: float) -> pd.DataFrame:
    out = v16.copy()
    for q in ["q05", "q50", "q95"]:
        out[q] = w1 * v16[q].values + (1 - w1) * bl[q].values
    return out


def ensemble_direction(v16: pd.DataFrame, bl: pd.DataFrame, w1: float) -> pd.DataFrame:
    out = v16.copy()
    centre_v16 = ((v16["dir_95"].values - v16["dir_05"].values) % 360) / 2.0 + v16["dir_05"].values
    centre_bl = ((bl["dir_95"].values - bl["dir_05"].values) % 360) / 2.0 + bl["dir_05"].values
    centre_v16 = centre_v16 % 360
    centre_bl = centre_bl % 360
    centre = circular_weighted_avg(centre_v16, centre_bl, w1)
    hw_v16 = circular_half_width(v16["dir_05"].values, v16["dir_95"].values)
    hw_bl = circular_half_width(bl["dir_05"].values, bl["dir_95"].values)
    hw = w1 * hw_v16 + (1 - w1) * hw_bl
    out["dir_05"] = (centre - hw) % 360
    out["dir_95"] = (centre + hw) % 360
    out["dir_50"] = circular_weighted_avg(v16["dir_50"].values, bl["dir_50"].values, w1)
    return out


def load_v16_predictions() -> pd.DataFrame:
    v16_csv = save_submission.__wrapped__ if hasattr(save_submission, "__wrapped__") else None
    from src.data.paths import PROJECT_ROOT
    csv_path = PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_v16.csv"
    if csv_path.exists():
        print("  Loading existing v16 predictions...")
        return pd.read_csv(csv_path, low_memory=False)
    print("  Generating v16 predictions...")
    generate_v16()
    return pd.read_csv(csv_path, low_memory=False)


def generate_v24(w1: float = 0.7):
    print(f"\n{'=' * 60}")
    print(f"Generating V24 submission (ensemble v16×{w1:.0%} + baseline×{1 - w1:.0%})")
    print(f"{'=' * 60}")
    t0 = time.time()

    v16 = load_v16_predictions()
    baseline = load_baseline()

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    for df in [v16, baseline]:
        for c in ["latitude", "longitude"]:
            df[c] = df[c].astype(float).round(2)
        df["horizon"] = df["horizon"].astype(int)
        df["hour"] = df["hour"].astype(int)

    v16_grid = v16[v16["type"] == "grid"].copy()
    v16_stations = v16[v16["type"] == "station"].copy()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    bl_stations = baseline[baseline["type"] == "station"].copy()

    v16_grid = v16_grid.merge(
        bl_grid[merge_keys + ["q05", "q50", "q95", "dir_05", "dir_50", "dir_95"]],
        on=merge_keys, how="inner", suffixes=("", "_bl"),
    )

    grid_speed = ensemble_speed(
        v16_grid[["q05", "q50", "q95"]].reset_index(drop=True),
        v16_grid[["q05_bl", "q50_bl", "q95_bl"]].rename(columns={
            "q05_bl": "q05", "q50_bl": "q50", "q95_bl": "q95",
        }).reset_index(drop=True),
        w1,
    )
    v16_grid["q05"] = grid_speed["q05"].values
    v16_grid["q50"] = grid_speed["q50"].values
    v16_grid["q95"] = grid_speed["q95"].values

    grid_dir = ensemble_direction(
        v16_grid[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True),
        v16_grid[["dir_05_bl", "dir_50_bl", "dir_95_bl"]].rename(columns={
            "dir_05_bl": "dir_05", "dir_50_bl": "dir_50", "dir_95_bl": "dir_95",
        }).reset_index(drop=True),
        w1,
    )
    v16_grid["dir_05"] = grid_dir["dir_05"].values
    v16_grid["dir_50"] = grid_dir["dir_50"].values
    v16_grid["dir_95"] = grid_dir["dir_95"].values

    v16_grid = v16_grid.drop(columns=[c for c in v16_grid.columns if c.endswith("_bl")])
    v16_grid = fix_crossing(v16_grid)

    stations_final = apply_height_correction(bl_stations)
    has_v16_station = not v16_stations.empty
    if has_v16_station:
        print("  Keeping v16 station predictions (height-corrected)")
        stations_final = v16_stations

    submission = pd.concat([v16_grid, stations_final], ignore_index=True)
    print(f"  Grid rows: {len(v16_grid):,}, Station rows: {len(stations_final):,}")
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time() - t0:.0f}s")

    tag = f"v24_w{w1:.1f}"
    save_submission(submission, tag)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weight", type=float, default=0.7, help="Weight for v16 (default 0.7)")
    args = parser.parse_args()
    generate_v24(args.weight)
