"""V23: Climatological quantiles for d14 pressure speed.

Replaces baseline d14 pressure speed (vertical ratios, no HRES d14 pressure data)
with per-(grid_point, month, hour) quantiles from 3 years of reanalysis training data.

Everything else same as v16:
- v8 residual speed for d1/d7 pressure
- baseline surface speed
- cherry-picked direction (v7 per-horizon, skip NS d14 and NS d7 surface)
- baseline stations + height correction

Usage: python src/pipeline/run_v23.py
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
    align_columns,
    apply_height_correction,
    fix_crossing,
    load_baseline,
    load_reanalysis_level,
    save_submission,
)

SPEED_MODEL_DIR = LOGS_DIR / "speed_models_v8"
PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"
CLIM_DIR = LOGS_DIR / "climatology_v23"


def compute_climatology(region: str, level: str) -> pd.DataFrame:
    rean = load_reanalysis_level(region, level)
    rean["month"] = rean["time"].dt.month
    rean["hour"] = rean["time"].dt.hour

    grouped = rean.groupby(["latitude", "longitude", "month", "hour"])["speed"]
    clim = grouped.quantile([0.05, 0.50, 0.95]).unstack(level=-1)
    clim.columns = ["q05", "q50", "q95"]
    clim = clim.reset_index()

    return clim


def compute_climatologies() -> None:
    CLIM_DIR.mkdir(parents=True, exist_ok=True)
    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            out_path = CLIM_DIR / f"{region}_{level}.parquet"
            if out_path.exists():
                print(f"  {region}/{level}: cached")
                continue
            print(f"  {region}/{level}: computing...")
            clim = compute_climatology(region, level)
            clim.to_parquet(out_path, index=False)
            print(f"    {len(clim):,} combos")


def load_climatology(region: str, level: str) -> pd.DataFrame:
    path = CLIM_DIR / f"{region}_{level}.parquet"
    return pd.read_parquet(path)


def predict_pressure_speed_d1d7() -> pd.DataFrame:
    print("Predicting pressure speed d1/d7 from v8 residual models...")
    all_rows = []
    from src.pipeline.run_v8 import build_speed_features, compute_hres_speed

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            for horizon in [1, 7]:
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

                        hres_spd = compute_hres_speed(inf, str(level), horizon, hour)
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


def predict_pressure_speed_d14_climatology() -> pd.DataFrame:
    print("Predicting pressure speed d14 from climatology...")
    all_rows = []

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            clim = load_climatology(region, level)

            overall = clim.groupby(["latitude", "longitude"])[["q05", "q50", "q95"]].mean().reset_index()

            for wid in range(1, 9):
                try:
                    inf = load_inference_features(wid, region)
                except FileNotFoundError:
                    continue

                lats = inf["latitude"].astype(float).round(2)
                lons = inf["longitude"].astype(float).round(2)
                issue_time = pd.to_datetime(inf["time"])

                for hour in HOURS:
                    target_time = issue_time + pd.Timedelta(days=14, hours=hour)
                    month = target_time.dt.month

                    tmp = pd.DataFrame({
                        "latitude": lats.values,
                        "longitude": lons.values,
                        "month": month.values,
                        "hour": hour,
                    })

                    merged = tmp.merge(
                        clim, on=["latitude", "longitude", "month", "hour"], how="left",
                    )

                    missing_mask = merged["q05"].isna()
                    if missing_mask.any():
                        fill = tmp[missing_mask].merge(
                            overall, on=["latitude", "longitude"], how="left",
                        )
                        for q in ["q05", "q50", "q95"]:
                            merged.loc[missing_mask, q] = fill[q].values

                    for i in range(len(merged)):
                        all_rows.append({
                            "type": "grid",
                            "window": wid,
                            "region": region,
                            "latitude": float(lats.iloc[i]),
                            "longitude": float(lons.iloc[i]),
                            "station": "",
                            "horizon": 14,
                            "hour": hour,
                            "level": str(level),
                            "q05": merged.iloc[i]["q05"],
                            "q50": merged.iloc[i]["q50"],
                            "q95": merged.iloc[i]["q95"],
                        })

            print(f"  {region}/{level}: {sum(1 for r in all_rows if r['region'] == region and r['level'] == str(level)):,} rows")

    return pd.DataFrame(all_rows)


def _skip_direction(region: str, level: str, horizon: int) -> bool:
    if region == "north_sea" and horizon == 14:
        return True
    if region == "north_sea" and horizon == 7 and level in ("10m", "100m"):
        return True
    return False


def predict_direction_v7_cherry() -> dict:
    print("Predicting direction (v7 per-horizon, cherry-pick)...")
    all_dir: dict[tuple, tuple] = {}

    perhoriz_cache: dict[tuple, object] = {}
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
                if _skip_direction(region, level, horizon):
                    continue

                art = perhoriz_cache.get((region, level, horizon))
                if art is None:
                    continue

                active_feat = art["feature_cols"]

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

                        dt = pd.to_datetime(inf["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
                        df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

                        X = align_columns(df_pred, active_feat)
                        d05, d50, d95 = art["model"].predict(X)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, float(lats[i]), float(lons[i]),
                                   int(horizon), int(hour), str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(all_dir):,} dir entries")

    return all_dir


def generate_v23() -> None:
    print("\n" + "=" * 60)
    print("Generating V23 submission (climatological d14 pressure speed)")
    print("=" * 60)
    t0 = time.time()

    print("\nStep 1: Computing climatologies...")
    compute_climatologies()

    print("\nStep 2: Loading baseline...")
    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    bl_grid["latitude"] = bl_grid["latitude"].astype(float).round(2)
    bl_grid["longitude"] = bl_grid["longitude"].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)

    print("\nStep 3: Predicting d1/d7 pressure speed (v8 residual)...")
    pressure_d1d7 = predict_pressure_speed_d1d7()
    print(f"  d1/d7 pressure speed rows: {len(pressure_d1d7):,}")

    print("\nStep 4: Predicting d14 pressure speed (climatology)...")
    pressure_d14 = predict_pressure_speed_d14_climatology()
    print(f"  d14 pressure speed rows: {len(pressure_d14):,}")

    pressure_speed = pd.concat([pressure_d1d7, pressure_d14], ignore_index=True)
    print(f"  Total pressure speed rows: {len(pressure_speed):,}")

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

    n_surface = bl_with_pspeed[bl_with_pspeed["level"].isin(SURFACE_LEVELS)].shape[0]
    print(f"  Grid: pressure speed replaced, {n_surface:,} surface rows kept baseline")

    print("\nStep 5: Predicting direction (cherry-pick v7)...")
    all_dir = predict_direction_v7_cherry()
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

    print("\nStep 6: Assembling stations...")
    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time()-t0:.0f}s")
    save_submission(submission, "v23")


if __name__ == "__main__":
    generate_v23()
