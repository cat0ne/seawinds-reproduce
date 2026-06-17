"""V7: Per-horizon direction models + baseline speed + height correction.

Key change: train 3 SEPARATE direction models per (region, level) — one per horizon.
The d14 model will naturally learn wider intervals since it only sees d14 data.
No more blind post-hoc scaling (which failed in v5).

Usage: python src/pipeline/run_v7.py
"""
from __future__ import annotations

import pickle
import sys
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import HORIZONS, HOURS, LOGS_DIR, PRESSURE_LEVELS, REGIONS, SURFACE_LEVELS
from src.io.dataset import load_features, load_inference_features
from src.models.direction import DirectionModel
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
)
from src.scoring.winkler import _circ_dist, circular_winkler_score

SAVE_DIR = LOGS_DIR / "direction_models_v7"


def build_training_frame(region, level, horizon, max_samples=150_000):
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    feat_cols = get_base_feature_cols(features.columns)

    rean = load_reanalysis_level(region, level)
    rean = rean.rename(columns={"time": "target_time", "direction": "target_direction"})

    per_hour = max_samples // len(HOURS) if max_samples else None
    frames = []
    for hour in HOURS:
        sub = features[["time", "latitude", "longitude"] + feat_cols].copy()
        if per_hour and len(sub) > per_hour:
            sub = sub.sample(n=per_hour, random_state=42)
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        sub["latitude"] = sub["latitude"].astype(float).round(2)
        sub["longitude"] = sub["longitude"].astype(float).round(2)
        sub["hour"] = hour

        merged = sub.merge(
            rean[["target_time", "latitude", "longitude", "target_direction"]],
            on=["target_time", "latitude", "longitude"],
            how="inner",
        ).dropna(subset=["target_direction"])
        if len(merged) > 0:
            frames.append(merged)

    if not frames:
        raise ValueError(f"No data for {region}/{level}/d{horizon}")

    df = pd.concat(frames, ignore_index=True)
    df["horizon"] = horizon
    return df, feat_cols


def prepare_X_direction(df, feat_cols):
    df = add_time_encodings(df)
    X = df[feat_cols].copy()
    for hr in HOURS:
        X[f"hour_{hr}"] = (df["hour"] == hr).astype(int)
    for c in ["month_sin", "month_cos", "doy_sin", "doy_cos"]:
        if c in df.columns:
            X[c] = df[c].values
    return X


def train_per_horizon_direction():
    print("=" * 60)
    print("V7: Training per-horizon direction models")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                label = f"{region}/{level}/d{horizon}"
                print(f"\n--- {label} ---")
                try:
                    df, feat_cols = build_training_frame(region, level, horizon)
                except ValueError as e:
                    print(f"  SKIP: {e}")
                    continue

                tr, vl, tu, ho = split_by_time(df)
                print(f"  train={len(tr):,} val={len(vl):,} tune={len(tu):,}")

                if len(tr) < 300 or len(tu) < 50:
                    print("  SKIP: insufficient data")
                    continue

                X_tr = prepare_X_direction(tr, feat_cols)
                y_tr = tr["target_direction"].values
                X_vl = prepare_X_direction(vl, feat_cols) if len(vl) > 0 else None
                y_vl = vl["target_direction"].values if len(vl) > 0 else None
                X_tu = prepare_X_direction(tu, feat_cols)
                y_tu = tu["target_direction"].values

                all_cols = set(X_tr.columns) | set(X_tu.columns)
                if X_vl is not None:
                    all_cols |= set(X_vl.columns)
                all_cols = sorted(all_cols)
                X_tr = align_columns(X_tr, all_cols)
                X_vl = align_columns(X_vl, all_cols) if X_vl is not None else None
                X_tu = align_columns(X_tu, all_cols)

                model = DirectionModel(centre_backend="lightgbm", halfwidth_backend="lightgbm")
                model.fit_centre(X_tr, y_tr, X_vl, y_vl)
                model.fit_halfwidth(X_tr, y_tr, X_vl, y_vl)
                if len(tu) > 0:
                    model.conformal_calibrate(X_tu, y_tu)

                scores = {}
                for name, X_s, y_s in [("val", X_vl, y_vl), ("tune", X_tu, y_tu)]:
                    if X_s is None or len(X_s) == 0:
                        continue
                    lo, mid, hi = model.predict(X_s)
                    cws = circular_winkler_score(y_s, lo, hi, alpha=0.1)
                    mae = float(np.nanmean(_circ_dist(y_s, mid)))
                    scores[name] = {"cws": round(cws, 1), "mae": round(mae, 1)}
                    print(f"  {name}: cWS={cws:.1f}  MAE={mae:.1f}deg")

                save_path = SAVE_DIR / region / level / f"d{horizon}"
                save_path.mkdir(parents=True, exist_ok=True)
                with open(save_path / "model.pkl", "wb") as f:
                    pickle.dump({
                        "model": model,
                        "feature_cols": all_cols,
                        "region": region,
                        "level": level,
                        "horizon": horizon,
                        "scores": scores,
                    }, f)

                results.append({
                    "region": region, "level": level, "horizon": horizon,
                    **{f"{k}_cws": v["cws"] for k, v in scores.items()},
                    **{f"{k}_mae": v["mae"] for k, v in scores.items()},
                })

    summary = pd.DataFrame(results)
    summary.to_csv(SAVE_DIR / "summary.csv", index=False)
    print(f"\nTraining done in {time.time()-t0:.0f}s")
    print(summary.to_string(index=False))
    return summary


def predict_direction_all_windows():
    print("\nPredicting direction for all windows...")
    all_dir = {}

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                model_path = SAVE_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                dir_model = art["model"]
                feat_cols = art["feature_cols"]

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    available = [c for c in feat_cols if c in inf.columns]
                    missing = set(feat_cols) - set(available) - {
                        c for c in feat_cols if c.startswith(("hour_", "month_", "doy_"))
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

                        X = align_columns(df_pred, feat_cols)
                        d05, d50, d95 = dir_model.predict(X)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, float(lats[i]), float(lons[i]), int(horizon), int(hour), str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(all_dir):,} entries")

    return all_dir


def generate_v7():
    print("\n" + "=" * 60)
    print("Generating V7 submission")
    print("=" * 60)

    baseline = load_baseline()
    bl_surface = baseline[(baseline["type"] == "grid") & (baseline["level"].isin(SURFACE_LEVELS))].copy()
    bl_pressure = baseline[(baseline["type"] == "grid") & (baseline["level"].isin(PRESSURE_LEVELS))].copy()
    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    all_dir = predict_direction_all_windows()

    dir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])
    print(f"  Direction entries: {len(dir_df):,}")

    for df in [bl_surface, bl_pressure]:
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

    grid = pd.concat([bl_surface, bl_pressure], ignore_index=True)
    grid = fix_crossing(grid)

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    submission["latitude"] = submission["latitude"].round(2)
    submission["longitude"] = submission["longitude"].round(2)

    print(f"  Total rows: {len(submission):,}")
    save_submission(submission, "v7")


if __name__ == "__main__":
    train_per_horizon_direction()
    generate_v7()
