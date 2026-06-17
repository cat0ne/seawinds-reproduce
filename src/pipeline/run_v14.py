"""V14: V13 + CQR calibration on all pressure speed intervals.

Computes CQR offsets for d1/d7 (v8 models) and d14 (v13 cross-horizon models),
then applies them to widen/narrow intervals toward 90% coverage.

V13 base: v8 pressure d1/d7 + v13 pressure d14 + baseline surface + cherry-pick direction.
V14 adds: CQR calibration offsets on ALL pressure speed intervals.

Usage: python src/pipeline/run_v14.py
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
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    add_time_encodings,
    align_columns,
    apply_height_correction,
    fix_crossing,
    get_base_feature_cols,
    load_baseline,
    load_reanalysis_level,
    save_submission,
    split_by_time,
    speed_from_uv,
)
from src.pipeline.run_v12 import predict_direction_cherry
from src.pipeline.run_v13 import (
    D14_MODEL_DIR,
    build_speed_features_d14,
    compute_d10_hres_speed,
)
from src.pipeline.run_v8 import SAVE_DIR as V8_MODEL_DIR, build_speed_features, compute_hres_speed

CQR_DIR = LOGS_DIR / "cqr_v14"


def compute_hres_for_horizon(df, level, horizon, hour):
    if horizon == 14:
        return compute_d10_hres_speed(df, level, hour)
    return compute_hres_speed(df, level, horizon, hour)


def build_cqr_data(region, level, horizon, features, feat_cols_base, rean):
    frames = []
    for hour in HOURS:
        sub = features[["time", "latitude", "longitude"] + feat_cols_base].copy()
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        sub["latitude"] = sub["latitude"].astype(float).round(2)
        sub["longitude"] = sub["longitude"].astype(float).round(2)

        merged = sub.merge(
            rean.rename(columns={"time": "target_time", "speed": "target_speed"}),
            on=["target_time", "latitude", "longitude"],
            how="inner",
        ).dropna(subset=["target_speed"])
        if len(merged) == 0:
            continue

        hres_spd = compute_hres_for_horizon(merged, level, horizon, hour)
        if hres_spd is None:
            continue
        valid = np.isfinite(hres_spd)
        merged = merged[valid].copy()
        if len(merged) == 0:
            continue

        merged["hres_speed"] = hres_spd[valid]
        merged["residual"] = merged["target_speed"].values - merged["hres_speed"].values
        frames.append(merged)

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def build_features_for_model(df, feat_cols, horizon, level):
    df = add_time_encodings(df)
    base_cols = [c for c in feat_cols if c in df.columns and not c.startswith(("horizon_", "hour_", "hres_speed", "month_", "doy_"))]
    X = df[base_cols].copy()
    for h in HORIZONS:
        X[f"horizon_{h}"] = int(h == horizon)
    for hr in HOURS:
        X[f"hour_{hr}"] = int(hr == 0)
    for c in ["month_sin", "month_cos", "doy_sin", "doy_cos"]:
        if c in df.columns:
            X[c] = df[c].values
        elif c in feat_cols:
            X[c] = 0
    hres_spd = compute_hres_for_horizon(df, level, horizon, 0)
    if hres_spd is not None and "hres_speed" in feat_cols:
        X["hres_speed"] = hres_spd
    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0
    return X[feat_cols]


def train_cqr():
    print("=" * 60)
    print("V14: Computing CQR calibration offsets (d1/d7/d14 pressure)")
    print("=" * 60)
    t0 = time.time()
    CQR_DIR.mkdir(parents=True, exist_ok=True)
    offsets = {}

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        feat_cols_base = get_base_feature_cols(features.columns)

        if len(features) > 200_000:
            features = features.sample(n=200_000, random_state=42).reset_index(drop=True)

        for level in PRESSURE_LEVELS:
            level_str = str(level)
            rean = load_reanalysis_level(region, level_str)

            for horizon in HORIZONS:
                if horizon == 14:
                    model_path = D14_MODEL_DIR / region / level_str / "d14" / "model.pkl"
                else:
                    model_path = V8_MODEL_DIR / region / level_str / f"d{horizon}" / "model.pkl"

                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                model_feat = art["feature_cols"]

                df = build_cqr_data(region, level_str, horizon, features, feat_cols_base, rean)
                if df is None or len(df) < 50:
                    offsets[(region, level_str, horizon)] = 0.0
                    continue

                if len(df) > 15_000:
                    df = df.sample(n=15_000, random_state=42)

                tr, vl, tu, ho = split_by_time(df)
                cal = tu if len(tu) > 50 else vl
                if len(cal) < 30:
                    offsets[(region, level_str, horizon)] = 0.0
                    continue

                X_cal = build_features_for_model(cal, model_feat, horizon, level_str)
                X_cal = align_columns(X_cal, model_feat)

                pred_05 = models[0.05].predict(X_cal)
                pred_95 = models[0.95].predict(X_cal)
                actual = cal["target_speed"].values
                hres_cal = cal["hres_speed"].values

                q05f = np.maximum(hres_cal + pred_05, 0)
                q95f = hres_cal + pred_95
                E = np.maximum(q05f - actual, actual - q95f)

                n = len(E)
                q_idx = min(int(np.ceil((1 - ALPHA) * (n + 1))) - 1, n - 1)
                offset = float(np.sort(E)[q_idx])

                offsets[(region, level_str, horizon)] = offset
                print(f"  {level_str}/d{horizon}: offset={offset:.3f} ({len(cal):,} cal)", flush=True)

    with open(CQR_DIR / "offsets.pkl", "wb") as f:
        pickle.dump(offsets, f)

    print(f"\nCQR done in {time.time()-t0:.0f}s")
    print(f"  Total: {len(offsets)}, non-zero: {sum(1 for v in offsets.values() if v > 0)}")
    return offsets


def predict_cqr_pressure_speed(offsets):
    print("\nPredicting CQR-calibrated pressure speed...")
    all_rows = []

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            level_str = str(level)
            for horizon in HORIZONS:
                if horizon == 14:
                    model_path = D14_MODEL_DIR / region / level_str / "d14" / "model.pkl"
                else:
                    model_path = V8_MODEL_DIR / region / level_str / f"d{horizon}" / "model.pkl"

                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                feat_cols = art["feature_cols"]
                offset = offsets.get((region, level_str, horizon), 0.0)

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    for hour in HOURS:
                        X = build_features_for_model(inf, feat_cols, horizon, level_str)
                        missing = set(feat_cols) - set(X.columns)
                        if missing:
                            for c in missing:
                                X[c] = 0
                        X = X[feat_cols]

                        r05 = models[0.05].predict(X)
                        r50 = models[0.50].predict(X)
                        r95 = models[0.95].predict(X)

                        hres_spd = compute_hres_for_horizon(inf, level_str, horizon, hour)
                        if hres_spd is None:
                            continue

                        valid = np.isfinite(hres_spd)
                        q05 = np.full(len(inf), np.nan)
                        q50 = np.full(len(inf), np.nan)
                        q95 = np.full(len(inf), np.nan)
                        q05[valid] = np.maximum(hres_spd[valid] + r05[valid] - offset, 0)
                        q50[valid] = hres_spd[valid] + r50[valid]
                        q95[valid] = hres_spd[valid] + r95[valid] + offset

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            if np.isnan(q05[i]):
                                continue
                            all_rows.append({
                                "type": "grid", "window": wid, "region": region,
                                "latitude": float(lats[i]), "longitude": float(lons[i]),
                                "station": "", "horizon": int(horizon), "hour": int(hour),
                                "level": level_str,
                                "q05": q05[i], "q50": q50[i], "q95": q95[i],
                            })

    return pd.DataFrame(all_rows)


def generate_v14(offsets):
    print("\n" + "=" * 60)
    print("Generating V14 submission")
    print("=" * 60)
    t0 = time.time()

    speed_df = predict_cqr_pressure_speed(offsets)
    print(f"  CQR pressure speed rows: {len(speed_df):,}")

    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    for c in ["latitude", "longitude"]:
        bl_grid[c] = bl_grid[c].astype(float).round(2)
        speed_df[c] = speed_df[c].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)
    speed_df["horizon"] = speed_df["horizon"].astype(int)
    speed_df["hour"] = speed_df["hour"].astype(int)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    bl_with_new = bl_grid.merge(
        speed_df[merge_keys + ["q05", "q50", "q95"]],
        on=merge_keys, how="left", suffixes=("_bl", "_new"),
    )
    for q in ["q05", "q50", "q95"]:
        nc, bc = f"{q}_new", f"{q}_bl"
        if nc in bl_with_new.columns:
            bl_with_new[q] = bl_with_new[nc].fillna(bl_with_new[bc])
            bl_with_new = bl_with_new.drop(columns=[nc, bc])

    all_dir = predict_direction_cherry()
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

    grid = bl_with_new.merge(dir_df, on=merge_keys, how="left", suffixes=("_old", ""))
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
    save_submission(submission, "v14")


if __name__ == "__main__":
    offsets = train_cqr()
    generate_v14(offsets)
