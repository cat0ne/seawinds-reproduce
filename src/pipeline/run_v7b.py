"""V7b: Hybrid direction — pooled for d1/d7, per-horizon for d14.

V7 showed per-horizon direction models massively improve d14 direction
(dir_pressure_d14_ns: 402→300) but destroy d1/d7 (dir_pressure_d1_ecs: 157→375).
The d1/d7 per-horizon models have 1/3 the data and lost cross-horizon signal.

Fix: use pooled direction models (from v4/v6) for d1/d7, and per-horizon
d14 models only. This should give us the d14 gain without any d1/d7 regression.

Usage: python src/pipeline/run_v7b.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd

from src.data.paths import HORIZONS, HOURS, LOGS_DIR, PRESSURE_LEVELS, REGIONS, SURFACE_LEVELS
from src.io.dataset import load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    add_time_encodings,
    align_columns,
    apply_height_correction,
    fix_crossing,
    load_baseline,
    save_submission,
)

POOLED_DIR = LOGS_DIR / "direction_models"
PERHORIZ_DIR = LOGS_DIR / "direction_models_v7"


def predict_pooled_direction(model_art, inf, horizon, hour, feat_cols):
    df_pred = inf[[c for c in feat_cols if c in inf.columns]].copy()
    for h in HOURS:
        df_pred[f"hour_{h}"] = int(h == hour)
    for h in HORIZONS:
        df_pred[f"horizon_{h}"] = int(h == horizon)
    dt = pd.to_datetime(inf["time"])
    df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    X = align_columns(df_pred, feat_cols)
    return model_art["model"].predict(X)


def predict_perhoriz_direction(model_art, inf, hour, feat_cols):
    df_pred = inf[[c for c in feat_cols if c in inf.columns]].copy()
    for h in HOURS:
        df_pred[f"hour_{h}"] = int(h == hour)
    dt = pd.to_datetime(inf["time"])
    df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
    df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values
    X = align_columns(df_pred, feat_cols)
    return model_art["model"].predict(X)


def generate_v7b():
    print("=" * 60)
    print("V7b: Hybrid direction (pooled d1/d7 + per-horizon d14)")
    print("=" * 60)
    t0 = time.time()

    baseline = load_baseline()
    bl_surface = baseline[(baseline["type"] == "grid") & (baseline["level"].isin(SURFACE_LEVELS))].copy()
    bl_pressure = baseline[(baseline["type"] == "grid") & (baseline["level"].isin(PRESSURE_LEVELS))].copy()
    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    all_dir = {}

    pooled_cache = {}

    for region in REGIONS:
        for level in ALL_LEVELS:
            pooled_path = POOLED_DIR / region / level / "model.pkl"
            if pooled_path.exists():
                with open(pooled_path, "rb") as f:
                    pooled_cache[(region, level)] = pickle.load(f)

    for region in REGIONS:
        print(f"\n--- {region} ---")
        for level in ALL_LEVELS:
            pooled_art = pooled_cache.get((region, level))

            for horizon in HORIZONS:
                use_perhoriz = (horizon == 14)
                model_dir = PERHORIZ_DIR / region / level / f"d{horizon}"
                perhoriz_path = model_dir / "model.pkl"
                perhoriz_art = None

                if use_perhoriz and perhoriz_path.exists():
                    with open(perhoriz_path, "rb") as f:
                        perhoriz_art = pickle.load(f)

                if perhoriz_art is None and pooled_art is None:
                    continue

                active_art = perhoriz_art if perhoriz_art else pooled_art
                active_feat = active_art["feature_cols"]
                source = "per-horizon" if perhoriz_art else "pooled"

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    available = [c for c in active_feat if c in inf.columns]
                    missing = set(active_feat) - set(available) - {
                        c for c in active_feat if c.startswith(("hour_", "horizon_", "month_", "doy_"))
                    }
                    if missing:
                        continue

                    for hour in HOURS:
                        if perhoriz_art:
                            d05, d50, d95 = predict_perhoriz_direction(perhoriz_art, inf, hour, active_feat)
                        else:
                            d05, d50, d95 = predict_pooled_direction(pooled_art, inf, horizon, hour, active_feat)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, float(lats[i]), float(lons[i]), int(horizon), int(hour), str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

            print(f"  {level}: using per-horizon d14 + pooled d1/d7")

    dir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])
    print(f"\n  Direction entries: {len(dir_df):,}")

    for idx, df in enumerate([bl_surface, bl_pressure]):
        merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
        df["latitude"] = df["latitude"].astype(float).round(2)
        df["longitude"] = df["longitude"].astype(float).round(2)
        df["horizon"] = df["horizon"].astype(int)
        df["hour"] = df["hour"].astype(int)

        before = len(df)
        df = df.merge(dir_df, on=merge_keys, how="left", suffixes=("_old", ""))
        for dcol in ["dir_05", "dir_50", "dir_95"]:
            if f"{dcol}_old" in df.columns:
                df[dcol] = df[dcol].fillna(df[f"{dcol}_old"])
                df = df.drop(columns=[f"{dcol}_old"])
        assert len(df) == before, f"Row count changed: {before} -> {len(df)}"
        if idx == 0:
            bl_surface = df
        else:
            bl_pressure = df

    grid = pd.concat([bl_surface, bl_pressure], ignore_index=True)
    grid = fix_crossing(grid)

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    submission["latitude"] = submission["latitude"].round(2)
    submission["longitude"] = submission["longitude"].round(2)

    print(f"  Total rows: {len(submission):,}")
    save_submission(submission, "v7b")
    print(f"Done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    generate_v7b()
