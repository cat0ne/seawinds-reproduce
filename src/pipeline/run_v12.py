"""V12: Cherry-pick best per-dimension from v6 + v8.

Strategy based on v8 leaderboard analysis:
- Pressure speed: v8 residual models (massive win, -18 to -23 on d1)
- Surface speed: baseline (v8 regressed +1-2 on d7/d14 surface)
- Station speed: baseline + height correction (unchanged)
- Direction d1: per-horizon v7 models (v8 proved these are excellent, 81-118 vs 144-190)
- Direction d7 NS: pooled model (v8 regressed +18-33 on NS d7)
- Direction d7 ECS: per-horizon v7 model (similar or slightly better than pooled)
- Direction d14: per-horizon v7 models (massive improvement)

Uses generate_hybrid_direction with per-region/horizon granularity.

Usage: python src/pipeline/run_v12.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd

from src.data.paths import (
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SURFACE_LEVELS,
)
from src.io.dataset import load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    add_time_encodings,
    align_columns,
    apply_height_correction,
    direction_from_uv,
    fix_crossing,
    get_base_feature_cols,
    load_baseline,
    load_reanalysis_level,
    save_submission,
    split_by_time,
    speed_from_uv,
)

SPEED_MODEL_DIR = LOGS_DIR / "speed_models_v8"
PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"
POOLED_DIR_DIR = LOGS_DIR / "direction_models"


def predict_pressure_speed():
    print("Predicting pressure speed from v8 residual models...")
    all_rows = []
    from src.pipeline.run_v8 import build_speed_features

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            for horizon in HORIZONS:
                model_path = SPEED_MODEL_DIR / region / str(level) / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                feat_cols = art["feature_cols"]

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    for hour in HOURS:
                        X = build_speed_features(inf, feat_cols, horizon, hour, str(level))
                        available = [c for c in feat_cols if c in X.columns]
                        missing = set(feat_cols) - set(available)
                        if missing:
                            for c in missing:
                                X[c] = 0
                        X = X[feat_cols]

                        r05 = models[0.05].predict(X)
                        r50 = models[0.50].predict(X)
                        r95 = models[0.95].predict(X)

                        from src.pipeline.run_v8 import compute_hres_speed as _compute_hres
                        hres_spd = _compute_hres(inf, str(level), horizon, hour)
                        if hres_spd is None:
                            continue

                        q05 = np.maximum(hres_spd + r05, 0)
                        q50 = hres_spd + r50
                        q95 = hres_spd + r95

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            all_rows.append({
                                "type": "grid",
                                "window": wid,
                                "region": region,
                                "latitude": lats[i],
                                "longitude": lons[i],
                                "station": "",
                                "horizon": horizon,
                                "hour": hour,
                                "level": str(level),
                                "q05": q05[i],
                                "q50": q50[i],
                                "q95": q95[i],
                            })

    return pd.DataFrame(all_rows)


def predict_direction_cherry():
    print("Predicting direction (cherry-pick per region/horizon)...")
    all_dir = {}

    pooled_cache = {}
    for region in REGIONS:
        for level in ALL_LEVELS:
            p = POOLED_DIR_DIR / region / level / "model.pkl"
            if p.exists():
                with open(p, "rb") as f:
                    pooled_cache[(region, level)] = pickle.load(f)

    perhoriz_cache = {}
    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                p = PERHORIZ_DIR_DIR / region / level / f"d{horizon}" / "model.pkl"
                if p.exists():
                    with open(p, "rb") as f:
                        perhoriz_cache[(region, level, horizon)] = pickle.load(f)

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                use_pooled = False
                if horizon == 7 and region == "north_sea":
                    use_pooled = True

                if use_pooled:
                    art = pooled_cache.get((region, level))
                else:
                    art = perhoriz_cache.get((region, level, horizon))

                if art is None:
                    art = pooled_cache.get((region, level))
                if art is None:
                    continue

                is_perhoriz = (region, level, horizon) in perhoriz_cache and not use_pooled
                active_feat = art["feature_cols"]
                dir_model = art["model"]

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
                        df_pred = inf[available].copy()
                        for hr in HOURS:
                            df_pred[f"hour_{hr}"] = int(hr == hour)

                        if not is_perhoriz:
                            for h in HORIZONS:
                                df_pred[f"horizon_{h}"] = int(h == horizon)

                        dt = pd.to_datetime(inf["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        if is_perhoriz:
                            df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
                            df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

                        X = align_columns(df_pred, active_feat)
                        d05, d50, d95 = dir_model.predict(X)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, float(lats[i]), float(lons[i]),
                                   int(horizon), int(hour), str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(all_dir):,} dir entries")

    return all_dir


def generate_v12():
    print("\n" + "=" * 60)
    print("Generating V12 submission (cherry-pick best of v6 + v8)")
    print("=" * 60)
    t0 = time.time()

    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    bl_grid["latitude"] = bl_grid["latitude"].astype(float).round(2)
    bl_grid["longitude"] = bl_grid["longitude"].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)

    pressure_speed = predict_pressure_speed()
    print(f"  Pressure speed rows: {len(pressure_speed):,}")

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    for c in ["latitude", "longitude"]:
        pressure_speed[c] = pressure_speed[c].astype(float).round(2)
    pressure_speed["horizon"] = pressure_speed["horizon"].astype(int)
    pressure_speed["hour"] = pressure_speed["hour"].astype(int)

    bl_with_pspeed = bl_grid.merge(
        pressure_speed[merge_keys + ["q05", "q50", "q95"]],
        on=merge_keys, how="left", suffixes=("_bl", "_new"),
    )
    for q in ["q05", "q50", "q95"]:
        new_col = f"{q}_new"
        bl_col = f"{q}_bl"
        if new_col in bl_with_pspeed.columns:
            bl_with_pspeed[q] = bl_with_pspeed[new_col].fillna(bl_with_pspeed[bl_col])
            bl_with_pspeed = bl_with_pspeed.drop(columns=[new_col, bl_col])

    n_pressure_replaced = bl_with_pspeed[
        bl_with_pspeed["level"].isin([str(l) for l in PRESSURE_LEVELS])
    ].shape[0] - pressure_speed.shape[0]
    n_surface_kept = bl_with_pspeed[
        bl_with_pspeed["level"].isin(SURFACE_LEVELS)
    ].shape[0]
    print(f"  Grid: pressure speed replaced, {n_surface_kept:,} surface rows kept baseline")

    all_dir = predict_direction_cherry()
    dir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])
    print(f"  Direction entries: {len(dir_df):,}")

    for c in ["latitude", "longitude"]:
        dir_df[c] = dir_df[c].astype(float).round(2)
    dir_df["horizon"] = dir_df["horizon"].astype(int)
    dir_df["hour"] = dir_df["hour"].astype(int)

    grid = bl_with_pspeed.merge(dir_df, on=merge_keys, how="left", suffixes=("_old", ""))
    for dcol in ["dir_05", "dir_50", "dir_95"]:
        old_col = f"{dcol}_old"
        if old_col in grid.columns:
            grid[dcol] = grid[dcol].fillna(grid[old_col])
            grid = grid.drop(columns=[old_col])

    grid = fix_crossing(grid)

    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time()-t0:.0f}s")
    save_submission(submission, "v12")


if __name__ == "__main__":
    generate_v12()
