"""V18: Station direction calibration using v7 grid model + per-station conformal offset.

Station direction currently is just nearest-grid baseline copy, scoring 185-333 cWS.
Capgemini gets 237 on ECS stations d7, showing significant room for improvement.

Approach:
- Use v7 per-horizon direction model (10m level) at nearest grid point for each station
- Compute per-station conformal offset on TUNE split: compare v7 predictions to actual
  station observations, compute the additional interval inflation needed for 90% coverage
- During inference: v7 model prediction at nearest grid point + station-specific offset

Grid: same as v16 (cherry-pick direction, v8 residual pressure speed).
Station speed: baseline + height correction (same as v8).
Station direction: v7 model at nearest grid point + per-station conformal offset.

NS_01 has no direction data — keeps baseline nearest-grid direction.

Usage: python src/pipeline/run_v18.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SCORING_DIR,
    SURFACE_LEVELS,
    TRAIN_DIR,
    TUNE_END,
    TUNE_START,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import (
    align_columns,
    apply_height_correction,
    fix_crossing,
    load_baseline,
    save_submission,
)
from src.pipeline.run_v16 import predict_direction_v7_cherry, predict_pressure_speed
from src.scoring.winkler import _circ_dist

PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"
OFFSET_DIR = LOGS_DIR / "station_dir_offsets_v18"
STATION_LEVEL = "10m"


def _load_station_meta():
    return pd.read_csv(SCORING_DIR / "station_metadata.csv")


def _load_station_obs(region):
    path = TRAIN_DIR / f"stations_{region}_6h.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _calibrate_station_direction(y, dir_05, dir_50, dir_95, alpha=0.1):
    if len(y) < 20:
        return 0.0
    centre = dir_50
    hw = ((dir_95 - dir_05) % 360.0) / 2.0
    scores = _circ_dist(y, centre) - hw
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(q_level, 1.0)
    return float(np.quantile(scores, q_level))


def _build_direction_features(merged, feat_cols, hour):
    base_cols = [
        c for c in feat_cols
        if c in merged.columns
        and not c.startswith(("hour_", "month_", "doy_"))
    ]
    df_pred = merged[base_cols].copy()
    for hr in HOURS:
        df_pred[f"hour_{hr}"] = int(hr == hour)
    dt = pd.to_datetime(merged["time"])
    df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
    df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values
    return align_columns(df_pred, feat_cols)


def compute_station_offsets():
    print("Computing station direction conformal offsets...")
    OFFSET_DIR.mkdir(parents=True, exist_ok=True)
    offsets_path = OFFSET_DIR / "offsets.pkl"
    if offsets_path.exists():
        with open(offsets_path, "rb") as f:
            offsets = pickle.load(f)
        print(f"  Loaded cached offsets for {len(offsets)} (station, horizon) combos")
        return offsets

    meta = _load_station_meta()
    offsets = {}

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)

        station_obs = _load_station_obs(region)
        station_obs = station_obs.dropna(subset=["direction"])

        region_meta = meta[meta["region"] == region]

        for horizon in HORIZONS:
            model_path = PERHORIZ_DIR_DIR / region / STATION_LEVEL / f"d{horizon}" / "model.pkl"
            if not model_path.exists():
                print(f"  d{horizon}: no v7 model, skipping")
                continue

            with open(model_path, "rb") as f:
                art = pickle.load(f)
            dir_model = art["model"]
            feat_cols = art["feature_cols"]

            for _, row in region_meta.iterrows():
                sid = row["station"]
                nlat = round(float(row["nearest_grid_lat"]), 2)
                nlon = round(float(row["nearest_grid_lon"]), 2)

                stat_obs = station_obs[
                    (station_obs["station"] == sid) & station_obs["direction"].notna()
                ]
                if len(stat_obs) == 0:
                    offsets[(sid, horizon)] = 0.0
                    print(f"  {sid}/d{horizon}: no direction data, offset=0.0")
                    continue

                grid_feats = features[
                    (features["latitude"] == nlat) & (features["longitude"] == nlon)
                ].copy()
                if len(grid_feats) == 0:
                    offsets[(sid, horizon)] = 0.0
                    continue

                all_y = []
                all_d05 = []
                all_d50 = []
                all_d95 = []

                for hour in HOURS:
                    gf = grid_feats.copy()
                    gf["target_time"] = gf["time"] + pd.Timedelta(days=horizon, hours=hour)

                    tune_mask = (gf["time"] >= TUNE_START) & (gf["time"] <= TUNE_END)
                    gf = gf[tune_mask]
                    if len(gf) == 0:
                        continue

                    merged = gf.merge(
                        stat_obs[["time", "direction"]].rename(
                            columns={"time": "target_time", "direction": "obs_dir"}
                        ),
                        on="target_time",
                        how="inner",
                    )
                    if len(merged) < 5:
                        continue

                    X = _build_direction_features(merged, feat_cols, hour)
                    d05, d50, d95 = dir_model.predict(X)

                    all_y.extend(merged["obs_dir"].values.tolist())
                    all_d05.extend(d05.tolist())
                    all_d50.extend(d50.tolist())
                    all_d95.extend(d95.tolist())

                y = np.array(all_y)
                d05 = np.array(all_d05)
                d50 = np.array(all_d50)
                d95 = np.array(all_d95)
                offset = _calibrate_station_direction(y, d05, d50, d95)
                offsets[(sid, horizon)] = offset
                print(f"  {sid}/d{horizon}: offset={offset:.1f} (n={len(y)})")

    with open(offsets_path, "wb") as f:
        pickle.dump(offsets, f)
    print(f"\n  Saved offsets for {len(offsets)} combos to {offsets_path}")
    return offsets


def predict_station_direction_v18(offsets):
    print("\nPredicting station direction (v7 model + conformal offset)...")
    meta = _load_station_meta()
    station_preds = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]

        for horizon in HORIZONS:
            model_path = PERHORIZ_DIR_DIR / region / STATION_LEVEL / f"d{horizon}" / "model.pkl"
            if not model_path.exists():
                continue

            with open(model_path, "rb") as f:
                art = pickle.load(f)
            dir_model = art["model"]
            feat_cols = art["feature_cols"]

            for _, row in region_meta.iterrows():
                sid = row["station"]
                nlat = round(float(row["nearest_grid_lat"]), 2)
                nlon = round(float(row["nearest_grid_lon"]), 2)
                offset = offsets.get((sid, horizon), 0.0)

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    grid = inf[
                        (inf["latitude"].astype(float).round(2) == nlat)
                        & (inf["longitude"].astype(float).round(2) == nlon)
                    ].copy()
                    if len(grid) == 0:
                        continue

                    available = [c for c in feat_cols if c in grid.columns]
                    missing = set(feat_cols) - set(available) - {
                        c for c in feat_cols if c.startswith(("hour_", "month_", "doy_"))
                    }
                    if missing:
                        continue

                    for hour in HOURS:
                        X = _build_direction_features(grid, feat_cols, hour)
                        d05, d50, d95 = dir_model.predict(X)

                        for i in range(len(X)):
                            d05_i = float(d05[i])
                            d50_i = float(d50[i])
                            d95_i = float(d95[i])

                            if offset != 0.0:
                                hw = ((d95_i - d05_i) % 360.0) / 2.0
                                new_hw = max(hw + offset, 0.0)
                                d05_i = (d50_i - new_hw) % 360.0
                                d95_i = (d50_i + new_hw) % 360.0

                            station_preds[(wid, region, sid, horizon, hour)] = (
                                d05_i, d50_i, d95_i
                            )

        print(f"  {region}: {len(station_preds)} station dir entries")

    return station_preds


def generate_v18():
    print("\n" + "=" * 60)
    print("Generating V18 submission (station direction conformal)")
    print("=" * 60)
    t0 = time.time()

    offsets = compute_station_offsets()

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

    n_surface = bl_with_pspeed[bl_with_pspeed["level"].isin(SURFACE_LEVELS)].shape[0]
    print(f"  Grid: pressure speed replaced, {n_surface:,} surface rows kept baseline")

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

    bl_stations = baseline[baseline["type"] == "station"].copy()
    bl_stations = apply_height_correction(bl_stations)

    station_dir = predict_station_direction_v18(offsets)
    print(f"  Station direction entries: {len(station_dir)}")

    sdir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "station": k[2], "horizon": k[3], "hour": k[4],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in station_dir.items()
    ])

    if len(sdir_df) > 0:
        sdir_df["horizon"] = sdir_df["horizon"].astype(int)
        sdir_df["hour"] = sdir_df["hour"].astype(int)

        merge_keys_st = ["window", "region", "station", "horizon", "hour"]
        bl_stations = bl_stations.merge(
            sdir_df, on=merge_keys_st, how="left", suffixes=("_old", "_new"),
        )
        for dcol in ["dir_05", "dir_50", "dir_95"]:
            nc = f"{dcol}_new"
            oc = f"{dcol}_old"
            if nc in bl_stations.columns:
                bl_stations[dcol] = bl_stations[nc].fillna(bl_stations[oc])
                bl_stations = bl_stations.drop(columns=[nc, oc])

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time()-t0:.0f}s")
    save_submission(submission, "v18")


if __name__ == "__main__":
    generate_v18()
