"""V15: Station direction calibration.

Trains per-station direction models using station observations as ground truth
and nearest-grid features as inputs. Uses the same sin/cos + half-width + conformal
approach as the grid direction models.

NS_01 has no direction data — keeps baseline nearest-grid direction.

V14 base: v8 pressure d1/d7 + baseline d14 pressure + baseline surface + cherry-pick direction + CQR.
V15 adds: per-station direction models replacing baseline nearest-grid direction.

Usage: python src/pipeline/run_v15.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import (
    ALPHA,
    FEATURES_DIR,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SCORING_DIR,
    TRAIN_DIR,
)
from src.io.dataset import load_features, load_inference_features
from src.models.direction import DirectionModel
from src.pipeline.pipeline_utils import (
    apply_height_correction,
    fix_crossing,
    get_base_feature_cols,
    load_baseline,
    save_submission,
    split_by_time,
)
from src.scoring.winkler import _circ_dist, circular_winkler_score

SAVE_DIR = LOGS_DIR / "station_direction_v15"

LGBM_PARAMS = {
    "n_estimators": 500,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": -1,
}


def load_station_obs(region):
    path = TRAIN_DIR / f"stations_{region}_6h.parquet"
    return pd.read_parquet(path)


def load_station_meta():
    return pd.read_csv(SCORING_DIR / "station_metadata.csv")


def build_station_training(station_id, region, meta, features, station_obs):
    row = meta[meta["station"] == station_id].iloc[0]
    nlat = round(float(row["nearest_grid_lat"]), 2)
    nlon = round(float(row["nearest_grid_lon"]), 2)

    stat = station_obs[station_obs["station"] == station_id].copy()
    stat["time"] = pd.to_datetime(stat["time"])
    stat = stat.dropna(subset=["direction"])
    if len(stat) == 0:
        return None

    grid = features[
        (features["latitude"].astype(float).round(2) == nlat)
        & (features["longitude"].astype(float).round(2) == nlon)
    ].copy()
    grid["time"] = pd.to_datetime(grid["time"])

    feat_cols = get_base_feature_cols(grid.columns)
    merged = stat[["time", "direction"]].merge(
        grid[["time"] + feat_cols], on="time", how="inner"
    ).dropna(subset=["direction"])

    if len(merged) < 50:
        return None

    return merged, feat_cols


def prepare_station_X(df, feat_cols):
    X = df[feat_cols].copy()
    dt = pd.to_datetime(df["time"])
    X["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
    X["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
    X["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
    X["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)
    return X


def train_station_models():
    print("=" * 60)
    print("V15: Training per-station direction models")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    meta = load_station_meta()
    results = []

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        station_obs = load_station_obs(region)
        station_obs["time"] = pd.to_datetime(station_obs["time"])

        region_meta = meta[meta["region"] == region]
        for _, row in region_meta.iterrows():
            sid = row["station"]
            print(f"  {sid}...", end=" ", flush=True)

            result = build_station_training(sid, region, meta, features, station_obs)
            if result is None:
                print("NO DATA")
                continue

            df, feat_cols = result
            y = df["direction"].values

            tr, vl, tu, ho = split_by_time(df)
            print(f"train={len(tr)} val={len(vl)} tune={len(tu)}", end=" ")

            if len(tr) < 30:
                print("SKIP")
                continue

            X_tr = prepare_station_X(tr, feat_cols)
            y_tr = tr["direction"].values
            X_vl = prepare_station_X(vl, feat_cols) if len(vl) > 0 else None
            y_vl = vl["direction"].values if len(vl) > 0 else None
            X_tu = prepare_station_X(tu, feat_cols) if len(tu) > 0 else None
            y_tu = tu["direction"].values if len(tu) > 0 else None

            from src.pipeline.pipeline_utils import align_columns
            all_cols = sorted(set(X_tr.columns) | (set(X_vl.columns) if X_vl is not None else set()) | (set(X_tu.columns) if X_tu is not None else set()))
            X_tr = align_columns(X_tr, all_cols)
            if X_vl is not None:
                X_vl = align_columns(X_vl, all_cols)
            if X_tu is not None:
                X_tu = align_columns(X_tu, all_cols)

            model = DirectionModel(centre_backend="lightgbm", halfwidth_backend="lightgbm")
            model.fit_centre(X_tr, y_tr, X_vl, y_vl)
            model.fit_halfwidth(X_tr, y_tr, X_vl, y_vl)
            if X_tu is not None and len(tu) > 0:
                model.conformal_calibrate(X_tu, y_tu)

            scores = {}
            for name, X_s, y_s in [("val", X_vl, y_vl), ("tune", X_tu, y_tu)]:
                if X_s is None or len(X_s) == 0:
                    continue
                lo, mid, hi = model.predict(X_s)
                cws = circular_winkler_score(y_s, lo, hi, alpha=0.1)
                mae = float(np.nanmean(_circ_dist(y_s, mid)))
                scores[name] = {"cws": round(cws, 1), "mae": round(mae, 1)}
                print(f"{name}: cWS={cws:.1f} MAE={mae:.1f}deg", end=" ")

            save_path = SAVE_DIR / region / sid
            save_path.mkdir(parents=True, exist_ok=True)
            with open(save_path / "model.pkl", "wb") as f:
                pickle.dump({
                    "model": model,
                    "feature_cols": all_cols,
                    "station": sid,
                    "region": region,
                    "scores": scores,
                }, f)

            results.append({"station": sid, "region": region, **scores})
            print()

    summary = pd.DataFrame(results)
    summary.to_csv(SAVE_DIR / "summary.csv", index=False)
    print(f"\nTraining done in {time.time()-t0:.0f}s")
    print(summary.to_string(index=False))


def predict_station_direction():
    print("\nPredicting station direction...")
    meta = load_station_meta()
    station_preds = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]
        for _, row in region_meta.iterrows():
            sid = row["station"]
            model_path = SAVE_DIR / region / sid / "model.pkl"
            if not model_path.exists():
                continue

            with open(model_path, "rb") as f:
                art = pickle.load(f)
            dir_model = art["model"]
            feat_cols = art["feature_cols"]
            nlat = round(float(row["nearest_grid_lat"]), 2)
            nlon = round(float(row["nearest_grid_lon"]), 2)

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
                    c for c in feat_cols if c.startswith(("month_", "doy_"))
                }
                if missing:
                    continue

                for horizon in HORIZONS:
                    for hour in HOURS:
                        df_pred = grid[available].copy()
                        dt = pd.to_datetime(grid["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
                        df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

                        from src.pipeline.pipeline_utils import align_columns
                        X = align_columns(df_pred, feat_cols)
                        d05, d50, d95 = dir_model.predict(X)

                        for i in range(len(X)):
                            key = (wid, region, sid, horizon, hour)
                            station_preds[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(station_preds)} station dir entries")

    return station_preds


def generate_v15():
    print("\n" + "=" * 60)
    print("Generating V15 submission")
    print("=" * 60)
    t0 = time.time()

    baseline = load_baseline()
    bl_stations = baseline[baseline["type"] == "station"].copy()
    bl_stations = apply_height_correction(bl_stations)

    station_dir = predict_station_direction()
    print(f"  Station direction entries: {len(station_dir)}")

    dir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "station": k[2], "horizon": k[3], "hour": k[4],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in station_dir.items()
    ])

    if len(dir_df) > 0:
        dir_df["horizon"] = dir_df["horizon"].astype(int)
        dir_df["hour"] = dir_df["hour"].astype(int)

        merge_keys = ["window", "region", "station", "horizon", "hour"]
        bl_stations = bl_stations.merge(
            dir_df, on=merge_keys, how="left", suffixes=("_old", "_new"),
        )
        for dcol in ["dir_05", "dir_50", "dir_95"]:
            nc = f"{dcol}_new"
            oc = f"{dcol}_old"
            if nc in bl_stations.columns:
                bl_stations[dcol] = bl_stations[nc].fillna(bl_stations[oc])
                bl_stations = bl_stations.drop(columns=[nc, oc])

    from src.pipeline.run_v12 import predict_direction_cherry
    baseline2 = load_baseline()
    bl_grid = baseline2[baseline2["type"] == "grid"].copy()
    for c in ["latitude", "longitude"]:
        bl_grid[c] = bl_grid[c].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)

    all_dir = predict_direction_cherry()
    dir_grid = pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])
    for c in ["latitude", "longitude"]:
        dir_grid[c] = dir_grid[c].astype(float).round(2)
    dir_grid["horizon"] = dir_grid["horizon"].astype(int)
    dir_grid["hour"] = dir_grid["hour"].astype(int)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    grid = bl_grid.merge(dir_grid, on=merge_keys, how="left", suffixes=("_old", ""))
    for dcol in ["dir_05", "dir_50", "dir_95"]:
        old_col = f"{dcol}_old"
        if old_col in grid.columns:
            grid[dcol] = grid[dcol].fillna(grid[old_col])
            grid = grid.drop(columns=[old_col])

    grid = fix_crossing(grid)

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time()-t0:.0f}s")
    save_submission(submission, "v15")


if __name__ == "__main__":
    train_station_models()
    generate_v15()
