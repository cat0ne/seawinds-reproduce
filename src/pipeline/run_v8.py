"""V8: Residual speed framing + v7 direction + height correction.

Key change: predict residual = (reanalysis_speed - HRES_forecast_speed) instead of
raw reanalysis speed. Then reconstruct: prediction = HRES_forecast + model.predict(features).

This is Model Output Statistics (MOS) — the model only needs to learn the bias
correction and uncertainty adjustment, not the full wind speed distribution.

Requires: run_v7.py must have been run first (per-horizon direction models in logs/direction_models_v7/).

Usage: python src/pipeline/run_v8.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import (
    FEATURES_DIR,
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

SAVE_DIR = LOGS_DIR / "speed_models_v8"
DIR_MODEL_DIR = LOGS_DIR / "direction_models_v7"

LGBM_PARAMS = {
    "n_estimators": 800,
    "max_depth": 7,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 50,
    "verbose": -1,
    "n_jobs": -1,
}


def get_hres_speed_col(level, horizon, hour):
    if level in ("10m", "100m"):
        return f"speed_d{horizon}_h{hour}"
    return None


def get_hres_uv_cols(level, horizon, hour):
    if level in ("10m", "100m"):
        return None, None
    return f"fcst_u_{level}_d{horizon}_h{hour}", f"fcst_v_{level}_d{horizon}_h{hour}"


def compute_hres_speed(df, level, horizon, hour):
    if level in ("10m", "100m"):
        col = f"speed_d{horizon}_h{hour}"
        if col in df.columns:
            return df[col].values
        return None
    u_col = f"fcst_u_{level}_d{horizon}_h{hour}"
    v_col = f"fcst_v_{level}_d{horizon}_h{hour}"
    if u_col in df.columns and v_col in df.columns:
        return speed_from_uv(df[u_col].values, df[v_col].values)
    return None


def build_speed_features(df, feat_cols, horizon, hour, level):
    df = add_time_encodings(df)
    base_cols = [c for c in feat_cols if c in df.columns and not c.startswith(("horizon_", "hour_", "hres_speed", "month_", "doy_"))]
    X = df[base_cols].copy()

    for h in HORIZONS:
        X[f"horizon_{h}"] = int(h == horizon)
    for hr in HOURS:
        X[f"hour_{hr}"] = int(hr == hour)
    for c in ["month_sin", "month_cos", "doy_sin", "doy_cos"]:
        if c in df.columns:
            X[c] = df[c].values
        elif c in feat_cols:
            X[c] = 0

    hres_spd = compute_hres_speed(df, level, horizon, hour)
    if hres_spd is not None and "hres_speed" in feat_cols:
        X["hres_speed"] = hres_spd

    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0
    return X[feat_cols]


def build_training_data(region, level, horizon, hour, max_samples=100_000):
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    feat_cols = get_base_feature_cols(features.columns)

    rean = load_reanalysis_level(region, level)
    target_time = features["time"] + pd.Timedelta(days=horizon, hours=hour)
    feat_merged = features.copy()
    feat_merged["target_time"] = target_time

    merged = feat_merged.merge(
        rean.rename(columns={"time": "target_time", "speed": "target_speed"}),
        on=["target_time", "latitude", "longitude"],
        how="inner",
    ).dropna(subset=["target_speed"])

    if len(merged) == 0:
        return None, None

    hres_spd = compute_hres_speed(merged, level, horizon, hour)
    if hres_spd is None:
        return None, None

    merged["residual"] = merged["target_speed"].values - hres_spd
    merged["horizon"] = horizon
    merged["hour"] = hour

    if max_samples and len(merged) > max_samples:
        merged = merged.sample(n=max_samples, random_state=42)

    return merged, feat_cols


def train_speed_models():
    print("=" * 60)
    print("V8: Training residual speed models")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    for region in REGIONS:
        print(f"\n=== {region} ===")
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                level_hor_frames = []
                feat_cols_ref = None
                for hour in HOURS:
                    merged, feat_cols = build_training_data(region, level, horizon, hour)
                    if merged is None:
                        continue
                    level_hor_frames.append(merged)
                    if feat_cols_ref is None:
                        feat_cols_ref = feat_cols

                if not level_hor_frames or feat_cols_ref is None:
                    continue

                df = pd.concat(level_hor_frames, ignore_index=True)
                tr, vl, tu, ho = split_by_time(df)
                print(f"  {level}/d{horizon}: train={len(tr):,} val={len(vl):,} tune={len(tu):,}")

                if len(tr) < 200:
                    continue

                X_tr = build_speed_features(tr, feat_cols_ref, horizon, 0, level)
                y_tr = tr["residual"].values.astype(np.float32)
                X_vl = build_speed_features(vl, feat_cols_ref, horizon, 0, level) if len(vl) > 0 else None
                y_vl = vl["residual"].values.astype(np.float32) if len(vl) > 0 else None
                X_tu = build_speed_features(tu, feat_cols_ref, horizon, 0, level) if len(tu) > 0 else None
                y_tu = tu["residual"].values.astype(np.float32) if len(tu) > 0 else None

                all_cols = sorted(X_tr.columns)
                if X_vl is not None:
                    all_cols = sorted(set(all_cols) | set(X_vl.columns))
                if X_tu is not None:
                    all_cols = sorted(set(all_cols) | set(X_tu.columns))
                X_tr = align_columns(X_tr, all_cols)
                if X_vl is not None:
                    X_vl = align_columns(X_vl, all_cols)
                if X_tu is not None:
                    X_tu = align_columns(X_tu, all_cols)

                models = {}
                for q in [0.05, 0.50, 0.95]:
                    m = LGBMRegressor(
                        objective="quantile", alpha=q,
                        **LGBM_PARAMS,
                    )
                    if X_vl is not None and len(X_vl) > 50:
                        m.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)],
                              callbacks=[__import__("lightgbm").early_stopping(50, verbose=False)])
                    else:
                        m.fit(X_tr, y_tr)
                    models[q] = m

                val_score = None
                if X_vl is not None and len(X_vl) > 0:
                    pred_05 = models[0.05].predict(X_vl)
                    pred_95 = models[0.95].predict(X_vl)
                    hres_vl = compute_hres_speed(vl, level, horizon, 0)
                    if hres_vl is not None:
                        q05_full = np.maximum(hres_vl + pred_05, 0)
                        q95_full = hres_vl + pred_95
                        coverage = ((y_vl + hres_vl >= q05_full) & (y_vl + hres_vl <= q95_full)).mean()
                        width = np.mean(q95_full - q05_full)
                        val_score = {"coverage": round(coverage, 3), "width": round(width, 2)}
                        print(f"    val: coverage={coverage:.3f} width={width:.2f}")

                save_path = SAVE_DIR / region / level / f"d{horizon}"
                save_path.mkdir(parents=True, exist_ok=True)
                with open(save_path / "model.pkl", "wb") as f:
                    pickle.dump({
                        "models": models,
                        "feature_cols": all_cols,
                        "region": region,
                        "level": level,
                        "horizon": horizon,
                        "val_score": val_score,
                    }, f)

    print(f"\nSpeed training done in {time.time()-t0:.0f}s")


def predict_speed_inference():
    print("\nPredicting speed for all inference windows...")
    all_rows = []

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                model_path = SAVE_DIR / region / level / f"d{horizon}" / "model.pkl"
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
                        X = build_speed_features(inf, feat_cols, horizon, hour, level)
                        available = [c for c in feat_cols if c in X.columns]
                        missing = set(feat_cols) - set(available)
                        if missing:
                            for c in missing:
                                X[c] = 0
                        X = X[feat_cols]

                        r05 = models[0.05].predict(X)
                        r50 = models[0.50].predict(X)
                        r95 = models[0.95].predict(X)

                        hres_spd = compute_hres_speed(inf, level, horizon, hour)
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


def predict_direction_from_v7():
    from src.pipeline.run_v7 import predict_direction_all_windows
    return predict_direction_all_windows()


def generate_v8():
    print("\n" + "=" * 60)
    print("Generating V8 submission")
    print("=" * 60)

    speed_df = predict_speed_inference()
    print(f"  Residual speed rows: {len(speed_df):,}")

    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    bl_grid["latitude"] = bl_grid["latitude"].astype(float).round(2)
    bl_grid["longitude"] = bl_grid["longitude"].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    for c in ["latitude", "longitude"]:
        speed_df[c] = speed_df[c].astype(float).round(2)
    speed_df["horizon"] = speed_df["horizon"].astype(int)
    speed_df["hour"] = speed_df["hour"].astype(int)

    bl_with_new = bl_grid.merge(
        speed_df[merge_keys + ["q05", "q50", "q95"]],
        on=merge_keys, how="left", suffixes=("_bl", "_new"),
    )
    for q in ["q05", "q50", "q95"]:
        new_col = f"{q}_new"
        bl_col = f"{q}_bl"
        if new_col in bl_with_new.columns:
            bl_with_new[q] = bl_with_new[new_col].fillna(bl_with_new[bl_col])
            bl_with_new = bl_with_new.drop(columns=[new_col, bl_col])
    print(f"  Grid rows (with baseline fallback): {len(bl_with_new):,}")

    all_dir = predict_direction_from_v7()
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

    baseline = load_baseline()
    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    save_submission(submission, "v8")


if __name__ == "__main__":
    if not any(SAVE_DIR.rglob("model.pkl")):  # repro: skip retrain if frozen models present
        train_speed_models()
    else:
        print(f"[cache] reusing frozen speed models in {SAVE_DIR}")
    generate_v8()
