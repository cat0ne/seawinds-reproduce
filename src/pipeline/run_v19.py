"""V19: Station direction (from v18) + station speed model trained on observations.

Combines two station improvements:
1. Station direction: v7 grid model at nearest grid point + per-station conformal offset (from v18)
2. Station speed: per-region per-horizon quantile LightGBM trained on station observations,
   with per-station CQR calibration on TUNE split

Grid: same as v16 (v8 pressure speed + baseline surface + cherry-pick direction).

Station speed approach:
- Pool all station observations per region
- Features: HRES forecast speed/dir + reanalysis ws10/ws100 + station metadata
- Target: observed station speed
- Train per (region, horizon) quantile LightGBM
- CQR calibration per station on TUNE split
- For d14: use d10 HRES as proxy (no d14 HRES available)

Usage: python src/pipeline/run_v19.py
"""
from __future__ import annotations

import pickle
import time

import lightgbm as lgb
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
    VAL_END,
    VAL_START,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    align_columns,
    apply_height_correction,
    fix_crossing,
    load_baseline,
    save_submission,
    split_by_time,
)
from src.pipeline.run_v16 import predict_direction_v7_cherry, predict_pressure_speed
from src.pipeline.run_v18 import compute_station_offsets, predict_station_direction_v18

STATION_SPEED_DIR = LOGS_DIR / "station_speed_models_v19"
PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"

HORIZON_MAP = {1: "d1", 7: "d7", 14: "d10"}

_STATION_MAP = {
    "NS_01": 0, "NS_02": 1, "NS_03": 2, "NS_04": 3, "NS_05": 4,
    "NS_06": 5, "NS_07": 6, "NS_08": 7,
    "ECS_01": 10, "ECS_02": 11, "ECS_03": 12, "ECS_04": 13,
    "ECS_05": 14, "ECS_06": 15, "ECS_07": 16,
}


def _station_speed_features(df, feat_cols, horizon, hour):
    h_key = HORIZON_MAP[horizon]
    h_str = str(horizon)
    result = pd.DataFrame(index=df.index)

    fcst_speed = f"fcst_speed_{h_key}_h{hour}"
    fcst_dir = f"fcst_dir_{h_key}_h{hour}"
    if fcst_speed in df.columns:
        result["fcst_speed"] = df[fcst_speed].astype(float)
    else:
        result["fcst_speed"] = np.nan
    if fcst_dir in df.columns:
        result["fcst_dir"] = df[fcst_dir].astype(float)
    else:
        result["fcst_dir"] = np.nan

    for col in ["ws10", "wd10", "ws100", "wd100", "wind_shear",
                 "t2m", "msl", "sshf", "blh", "cape",
                 "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d", "ws10_rstd7d",
                 "msl_lag1d", "msl_lag3d", "t2m_lag1d", "t2m_lag3d",
                 "elevation"]:
        if col in df.columns:
            result[col] = df[col].astype(float)

    if "height_m" in df.columns:
        result["height_m"] = df["height_m"].astype(float)

    if "latitude" in df.columns:
        result["stat_lat"] = df["latitude"].astype(float)
    if "longitude" in df.columns:
        result["stat_lon"] = df["longitude"].astype(float)

    dt = pd.to_datetime(df["time"]) if "time" in df.columns else pd.to_datetime(df["issue_time"])
    result["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    result["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    result["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
    result["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

    for hr in HOURS:
        result[f"hour_{hr}"] = int(hr == hour)

    for col in feat_cols:
        if col not in result.columns:
            result[col] = 0.0

    return result[feat_cols]


def train_station_speed_models():
    print("=" * 60)
    print("V19: Training station speed models (per region x horizon)")
    print("=" * 60)
    t0 = time.time()
    STATION_SPEED_DIR.mkdir(parents=True, exist_ok=True)

    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)

        obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
        obs["time"] = pd.to_datetime(obs["time"])
        obs = obs.dropna(subset=["speed"])

        region_meta = meta[meta["region"] == region]

        for horizon in HORIZONS:
            print(f"\n  --- d{horizon} ---")
            all_rows = []

            for _, mrow in region_meta.iterrows():
                sid = mrow["station"]
                stat_height = float(mrow["height_m"])
                nlat = round(float(mrow["nearest_grid_lat"]), 2)
                nlon = round(float(mrow["nearest_grid_lon"]), 2)

                stat_obs = obs[obs["station"] == sid].copy()
                if len(stat_obs) == 0:
                    continue

                grid_feats = features[
                    (features["latitude"] == nlat) & (features["longitude"] == nlon)
                ].copy()
                if len(grid_feats) == 0:
                    continue

                for hour in HOURS:
                    gf = grid_feats.copy()
                    gf["target_time"] = gf["time"] + pd.Timedelta(days=horizon, hours=hour)

                    merged = gf.merge(
                        stat_obs[["time", "speed"]].rename(
                            columns={"time": "target_time", "speed": "obs_speed"}
                        ),
                        on="target_time",
                        how="inner",
                    ).dropna(subset=["obs_speed"])
                    if len(merged) < 5:
                        continue

                    merged["station"] = sid
                    merged["height_m"] = stat_height
                    merged["latitude"] = float(mrow["latitude"])
                    merged["longitude"] = float(mrow["longitude"])
                    merged["hour"] = hour
                    merged["horizon"] = horizon
                    all_rows.append(merged)

            if not all_rows:
                print(f"    No data, skipping")
                continue

            df = pd.concat(all_rows, ignore_index=True)
            print(f"    Total samples: {len(df):,}")

            feat_cols = _get_feat_cols()
            all_X, all_y, all_splits, all_stations = [], [], [], []

            for hour in HOURS:
                hour_rows = df[df["hour"] == hour]
                if len(hour_rows) == 0:
                    continue
                X_h = _station_speed_features(hour_rows, feat_cols, horizon, hour)
                for c in X_h.columns:
                    X_h[c] = X_h[c].fillna(0)
                X_h["station_id"] = hour_rows["station"].map(_STATION_MAP).fillna(-1).astype(int).values
                all_X.append(X_h)
                all_y.append(hour_rows["obs_speed"].values.astype(float))
                all_splits.append(hour_rows["time"])
                all_stations.append(hour_rows["station"].values)

            if not all_X:
                print(f"    No data, skipping")
                continue

            X = pd.concat(all_X, ignore_index=True)
            final_feat_cols = list(X.columns)
            y = np.concatenate(all_y)
            times = pd.concat(all_splits, ignore_index=True)
            stations_arr = np.concatenate(all_stations)

            tr_mask = times < VAL_START
            tu_mask = (times >= TUNE_START) & (times <= TUNE_END)

            X_tr = X[tr_mask].values.astype(np.float32)
            y_tr = y[tr_mask]
            X_tu = X[tu_mask].values.astype(np.float32)
            y_tu = y[tu_mask]

            print(f"    Train: {len(X_tr):,}, TUNE: {len(X_tu):,}")

            models = {}
            for q in [0.05, 0.50, 0.95]:
                dtrain = lgb.Dataset(X_tr, label=y_tr)
                params = {
                    "objective": "quantile",
                    "alpha": q,
                    "learning_rate": 0.05,
                    "num_leaves": 31,
                    "min_child_samples": 20,
                    "feature_fraction": 0.8,
                    "bagging_fraction": 0.8,
                    "bagging_freq": 1,
                    "verbose": -1,
                    "n_jobs": -1,
                }
                model = lgb.train(params, dtrain, num_boost_round=300)
                models[q] = model

            cqr_offsets = {}
            stations_tune = stations_arr[tu_mask.values] if tu_mask.sum() > 0 else []
            unique_stations = np.unique(stations_tune) if len(stations_tune) > 0 else []

            for sid in unique_stations:
                s_mask = stations_tune == sid
                X_s = X_tu[s_mask]
                y_s = y_tu[s_mask]
                if len(y_s) < 10:
                    cqr_offsets[sid] = 0.0
                    continue

                p05 = models[0.05].predict(X_s)
                p95 = models[0.95].predict(X_s)
                E = np.maximum(p05 - y_s, y_s - p95)
                n = len(E)
                q_idx = min(int(np.ceil((1 - ALPHA) * (n + 1))) - 1, n - 1)
                cqr_offsets[sid] = float(np.sort(E)[max(q_idx, 0)])

            all_stations = region_meta["station"].values
            for sid in all_stations:
                if sid not in cqr_offsets:
                    cqr_offsets[sid] = 0.0

            save_dir = STATION_SPEED_DIR / region / f"d{horizon}"
            save_dir.mkdir(parents=True, exist_ok=True)
            with open(save_dir / "model.pkl", "wb") as f:
                pickle.dump({
                    "models": models,
                    "feature_cols": final_feat_cols,
                    "cqr_offsets": cqr_offsets,
                }, f)

            p50_tr = models[0.50].predict(X_tr)
            bias_tr = np.mean(y_tr - p50_tr)
            p05_tu = models[0.05].predict(X_tu)
            p95_tu = models[0.95].predict(X_tu)
            cov = np.mean((y_tu >= p05_tu) & (y_tu <= p95_tu))
            print(f"    Train bias: {bias_tr:+.2f}, TUNE coverage (raw): {cov:.3f}")
            non_zero = sum(1 for v in cqr_offsets.values() if v > 0)
            print(f"    CQR offsets: {non_zero}/{len(cqr_offsets)} non-zero, "
                  f"max={max(cqr_offsets.values()):.2f}")

    print(f"\nStation speed models trained in {time.time()-t0:.0f}s")


def _get_feat_cols():
    return [
        "fcst_speed", "fcst_dir",
        "ws10", "wd10", "ws100", "wd100", "wind_shear",
        "t2m", "msl", "sshf", "blh", "cape",
        "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d", "ws10_rstd7d",
        "msl_lag1d", "msl_lag3d", "t2m_lag1d", "t2m_lag3d",
        "elevation", "height_m", "stat_lat", "stat_lon",
        "month_sin", "month_cos", "doy_sin", "doy_cos",
        "hour_0", "hour_6", "hour_12", "hour_18",
        "station_id",
    ]


def predict_station_speed_v19():
    print("\nPredicting station speed (v19 models + CQR)...")
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    all_preds = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]

        for horizon in HORIZONS:
            model_path = STATION_SPEED_DIR / region / f"d{horizon}" / "model.pkl"
            if not model_path.exists():
                print(f"  {region}/d{horizon}: no model, using baseline")
                continue

            with open(model_path, "rb") as f:
                art = pickle.load(f)
            models = art["models"]
            feat_cols = art["feature_cols"]
            cqr_offsets = art["cqr_offsets"]

            for _, mrow in region_meta.iterrows():
                sid = mrow["station"]
                stat_height = float(mrow["height_m"])
                nlat = round(float(mrow["nearest_grid_lat"]), 2)
                nlon = round(float(mrow["nearest_grid_lon"]), 2)
                offset = cqr_offsets.get(sid, 0.0)

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

                    for hour in HOURS:
                        grid["height_m"] = stat_height
                        grid["latitude"] = float(mrow["latitude"])
                        grid["longitude"] = float(mrow["longitude"])
                        grid["station"] = sid
                        grid["hour"] = hour
                        grid["horizon"] = horizon

                        X = _station_speed_features(grid, feat_cols, horizon, hour)
                        for c in X.columns:
                            X[c] = X[c].fillna(0)

                        X["station_id"] = _STATION_MAP.get(sid, -1)

                        X_arr = X[feat_cols].values.astype(np.float32)

                        q05 = models[0.05].predict(X_arr)
                        q50 = models[0.50].predict(X_arr)
                        q95 = models[0.95].predict(X_arr)

                        q05 = np.maximum(q05 - offset, 0)
                        q95 = q95 + offset

                        q05, q50, q95 = np.sort(np.column_stack([q05, q50, q95]), axis=1).T

                        for i in range(len(grid)):
                            key = (wid, region, sid, int(horizon), int(hour))
                            all_preds[key] = (float(q05[i]), float(q50[i]), float(q95[i]))

        print(f"  {region}: {len(all_preds)} station speed entries")

    return all_preds


def generate_v19():
    print("\n" + "=" * 60)
    print("V19: Station direction + station speed model")
    print("=" * 60)
    t0 = time.time()

    dir_offsets = compute_station_offsets()

    if not any(STATION_SPEED_DIR.rglob("model.pkl")):  # repro: skip retrain if frozen models present
        train_station_speed_models()
    else:
        print(f"[cache] reusing frozen station-speed models in {STATION_SPEED_DIR}")

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

    all_dir = predict_direction_v7_cherry()
    dir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])
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

    station_speed = predict_station_speed_v19()
    print(f"  Station speed entries: {len(station_speed)}")

    sspd_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "station": k[2], "horizon": k[3], "hour": k[4],
         "q05": v[0], "q50": v[1], "q95": v[2]}
        for k, v in station_speed.items()
    ])
    if len(sspd_df) > 0:
        sspd_df["horizon"] = sspd_df["horizon"].astype(int)
        sspd_df["hour"] = sspd_df["hour"].astype(int)
        merge_keys_st = ["window", "region", "station", "horizon", "hour"]
        bl_stations = bl_stations.merge(
            sspd_df, on=merge_keys_st, how="left", suffixes=("_old", "_new"),
        )
        for qcol in ["q05", "q50", "q95"]:
            nc = f"{qcol}_new"
            oc = f"{qcol}_old"
            if nc in bl_stations.columns:
                bl_stations[qcol] = bl_stations[nc].fillna(bl_stations[oc])
                bl_stations = bl_stations.drop(columns=[nc, oc])

    station_dir = predict_station_direction_v18(dir_offsets)
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
    save_submission(submission, "v19")


if __name__ == "__main__":
    generate_v19()
