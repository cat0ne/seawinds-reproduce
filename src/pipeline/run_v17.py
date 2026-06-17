"""V17: CQR calibration on v16 base (v8 speed + cherry-pick direction).

V16 base: v8 pressure speed models + baseline surface fallback + cherry-pick direction.
V17 adds: CQR offsets computed on TUNE split for pressure levels where coverage < 0.90.
Surface levels (10m, 100m) are degenerate with coverage=1.0, so CQR is skipped there.

Direction cherry-pick (same as v16):
- NS d14: baseline direction
- NS d7 surface (10m, 100m): baseline direction
- Everything else: v7 per-horizon direction models

Usage: python src/pipeline/run_v17.py
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
    SURFACE_LEVELS,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
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
from src.pipeline.run_v8 import SAVE_DIR as V8_MODEL_DIR
from src.pipeline.run_v8 import build_speed_features, compute_hres_speed

PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"
CQR_DIR = LOGS_DIR / "cqr_v17"


def predict_direction_v16():
    print("Predicting direction (v16 cherry-pick: NS d14→baseline, NS d7 surf→baseline, rest→v7)...")
    all_dir = {}

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
                if region == "north_sea" and horizon == 14:
                    continue
                if region == "north_sea" and horizon == 7 and level in ("10m", "100m"):
                    continue

                art = perhoriz_cache.get((region, level, horizon))
                if art is None:
                    continue

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

                        dt = pd.to_datetime(inf["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
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

        hres_spd = compute_hres_speed(merged, level, horizon, hour)
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


def train_cqr_calibration():
    print("=" * 60)
    print("V17: Computing CQR calibration offsets (pressure only, TUNE split)")
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
                cal = tu
                if len(cal) < 30:
                    cal = vl
                if len(cal) < 30:
                    offsets[(region, level_str, horizon)] = 0.0
                    continue

                X_cal = build_speed_features(cal, model_feat, horizon, 0, level_str)
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


def predict_cqr_speed(offsets):
    print("\nPredicting CQR-calibrated pressure speed...")
    all_rows = []

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            level_str = str(level)
            for horizon in HORIZONS:
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
                        X = build_speed_features(inf, feat_cols, horizon, hour, level_str)
                        missing = set(feat_cols) - set(X.columns)
                        if missing:
                            for c in missing:
                                X[c] = 0
                        X = X[feat_cols]

                        r05 = models[0.05].predict(X)
                        r50 = models[0.50].predict(X)
                        r95 = models[0.95].predict(X)

                        hres_spd = compute_hres_speed(inf, level_str, horizon, hour)
                        if hres_spd is None:
                            continue

                        q05 = np.maximum(hres_spd + r05 - offset, 0)
                        q50 = hres_spd + r50
                        q95 = hres_spd + r95 + offset

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            all_rows.append({
                                "type": "grid", "window": wid, "region": region,
                                "latitude": float(lats[i]), "longitude": float(lons[i]),
                                "station": "", "horizon": int(horizon), "hour": int(hour),
                                "level": level_str,
                                "q05": q05[i], "q50": q50[i], "q95": q95[i],
                            })

    return pd.DataFrame(all_rows)


def generate_v17():
    print("\n" + "=" * 60)
    print("Generating V17 submission (v16 base + CQR calibration)")
    print("=" * 60)
    t0 = time.time()

    offsets_path = CQR_DIR / "offsets.pkl"
    if offsets_path.exists():
        with open(offsets_path, "rb") as f:
            offsets = pickle.load(f)
    else:
        offsets = train_cqr_calibration()

    speed_df = predict_cqr_speed(offsets)
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

    all_dir = predict_direction_v16()
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
    save_submission(submission, "v17")


if __name__ == "__main__":
    train_cqr_calibration()
    generate_v17()
