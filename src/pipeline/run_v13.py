"""V13: Pressure d14 speed via cross-horizon transfer.

Uses d10 HRES pressure forecasts as pseudo-forecast for d14.
Residual = reanalysis_d14_speed - speed_from_uv(fcst_u_{level}_d10, fcst_v_{level}_d10).
The model only needs to learn the 4-day degradation d10->d14.

V12 base: pressure speed from v8 residual (d1/d7), baseline surface, cherry-pick direction.
V13 adds: d14 pressure speed from cross-horizon transfer.

Usage: python src/pipeline/run_v13.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import (
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
from src.pipeline.run_v12 import predict_direction_cherry
from src.pipeline.run_v8 import SAVE_DIR as SPEED_MODEL_DIR, build_speed_features, compute_hres_speed

D14_MODEL_DIR = LOGS_DIR / "speed_models_v13"

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


def compute_d10_hres_speed(df, level, hour):
    u_col = f"fcst_u_{level}_d10_h{hour}"
    v_col = f"fcst_v_{level}_d10_h{hour}"
    if u_col in df.columns and v_col in df.columns:
        u = df[u_col].values.astype(float)
        v = df[v_col].values.astype(float)
        valid = np.isfinite(u) & np.isfinite(v)
        spd = np.full(len(df), np.nan)
        spd[valid] = speed_from_uv(u[valid], v[valid])
        return spd
    return None


def build_d14_training_data(region, level, max_samples=100_000):
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    feat_cols = get_base_feature_cols(features.columns)

    rean = load_reanalysis_level(region, level)
    horizon = 14
    frames = []

    for hour in HOURS:
        sub = features[["time", "latitude", "longitude"] + feat_cols].copy()
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        sub["latitude"] = sub["latitude"].astype(float).round(2)
        sub["longitude"] = sub["longitude"].astype(float).round(2)

        d10_spd = compute_d10_hres_speed(sub, level, hour)
        if d10_spd is None:
            continue

        merged = sub.merge(
            rean.rename(columns={"time": "target_time", "speed": "target_speed"}),
            on=["target_time", "latitude", "longitude"],
            how="inner",
        ).dropna(subset=["target_speed"])

        if len(merged) == 0:
            continue

        # Reindex d10_spd to match merged
        d10_spd_merged = compute_d10_hres_speed(merged, level, hour)
        if d10_spd_merged is None:
            continue

        valid_mask = np.isfinite(d10_spd_merged)
        merged = merged[valid_mask].copy()
        if len(merged) == 0:
            continue

        d10_spd_valid = d10_spd_merged[valid_mask]
        merged["residual"] = merged["target_speed"].values - d10_spd_valid
        merged["hres_speed"] = d10_spd_valid
        frames.append(merged)

    if not frames:
        return None, None

    df = pd.concat(frames, ignore_index=True)
    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42)
    return df, feat_cols


def build_speed_features_d14(df, feat_cols, level):
    df = add_time_encodings(df)
    base_cols = [c for c in feat_cols if c in df.columns and not c.startswith(("horizon_", "hour_", "hres_speed", "month_", "doy_"))]
    X = df[base_cols].copy()
    for h in HORIZONS:
        X[f"horizon_{h}"] = int(h == 14)
    for hr in HOURS:
        X[f"hour_{hr}"] = int(hr == 0)
    for c in ["month_sin", "month_cos", "doy_sin", "doy_cos"]:
        if c in df.columns:
            X[c] = df[c].values
        elif c in feat_cols:
            X[c] = 0
    hres_spd = compute_d10_hres_speed(df, level, 0)
    if hres_spd is not None and "hres_speed" in feat_cols:
        X["hres_speed"] = hres_spd
    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0
    return X[feat_cols]


def train_d14_models():
    print("=" * 60)
    print("V13: Training d14 pressure speed models (d10 cross-horizon)")
    print("=" * 60)
    t0 = time.time()
    D14_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    for region in REGIONS:
        print(f"\n=== {region} ===")
        for level in PRESSURE_LEVELS:
            print(f"  {level}...", end=" ", flush=True)
            df, feat_cols = build_d14_training_data(region, str(level))
            if df is None:
                print("NO DATA")
                continue

            tr, vl, tu, ho = split_by_time(df)
            print(f"train={len(tr):,} val={len(vl):,} tune={len(tu):,}", end=" ")

            if len(tr) < 200:
                print("SKIP (too few)")
                continue

            X_tr = build_speed_features_d14(tr, feat_cols, str(level))
            y_tr = tr["residual"].values.astype(np.float32)
            X_vl = build_speed_features_d14(vl, feat_cols, str(level)) if len(vl) > 0 else None
            y_vl = vl["residual"].values.astype(np.float32) if len(vl) > 0 else None

            all_cols = sorted(set(X_tr.columns) | (set(X_vl.columns) if X_vl is not None else set()))
            X_tr = align_columns(X_tr, all_cols)
            if X_vl is not None:
                X_vl = align_columns(X_vl, all_cols)

            models = {}
            for q in [0.05, 0.50, 0.95]:
                m = LGBMRegressor(objective="quantile", alpha=q, **LGBM_PARAMS)
                if X_vl is not None and len(X_vl) > 50:
                    import lightgbm
                    m.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)],
                          callbacks=[lightgbm.early_stopping(50, verbose=False)])
                else:
                    m.fit(X_tr, y_tr)
                models[q] = m

            val_score = None
            if X_vl is not None and len(X_vl) > 0:
                pred_05 = models[0.05].predict(X_vl)
                pred_95 = models[0.95].predict(X_vl)
                hres_vl = vl["hres_speed"].values
                actual = vl["target_speed"].values
                q05_full = np.maximum(hres_vl + pred_05, 0)
                q95_full = hres_vl + pred_95
                coverage = ((actual >= q05_full) & (actual <= q95_full)).mean()
                width = np.mean(q95_full - q05_full)
                val_score = {"coverage": round(coverage, 3), "width": round(width, 2)}
                print(f"val: cov={coverage:.3f} width={width:.2f}")
            else:
                print("no val")

            save_path = D14_MODEL_DIR / region / str(level) / "d14"
            save_path.mkdir(parents=True, exist_ok=True)
            with open(save_path / "model.pkl", "wb") as f:
                pickle.dump({
                    "models": models,
                    "feature_cols": all_cols,
                    "region": region,
                    "level": str(level),
                    "horizon": 14,
                    "base_horizon": 10,
                    "val_score": val_score,
                }, f)

    print(f"\nD14 training done in {time.time()-t0:.0f}s")


def predict_d14_pressure_speed():
    print("\nPredicting d14 pressure speed...")
    all_rows = []

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            model_path = D14_MODEL_DIR / region / str(level) / "d14" / "model.pkl"
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
                    X = build_speed_features_d14(inf, feat_cols, str(level))
                    available = [c for c in feat_cols if c in X.columns]
                    missing = set(feat_cols) - set(available)
                    if missing:
                        for c in missing:
                            X[c] = 0
                    X = X[feat_cols]

                    r05 = models[0.05].predict(X)
                    r50 = models[0.50].predict(X)
                    r95 = models[0.95].predict(X)

                    d10_spd = compute_d10_hres_speed(inf, str(level), hour)
                    if d10_spd is None:
                        continue

                    valid = np.isfinite(d10_spd)
                    q05 = np.full(len(inf), np.nan)
                    q50 = np.full(len(inf), np.nan)
                    q95 = np.full(len(inf), np.nan)
                    q05[valid] = np.maximum(d10_spd[valid] + r05[valid], 0)
                    q50[valid] = d10_spd[valid] + r50[valid]
                    q95[valid] = d10_spd[valid] + r95[valid]

                    lats = inf["latitude"].astype(float).round(2).values
                    lons = inf["longitude"].astype(float).round(2).values
                    for i in range(len(inf)):
                        if np.isnan(q05[i]):
                            continue
                        all_rows.append({
                            "type": "grid",
                            "window": wid,
                            "region": region,
                            "latitude": lats[i],
                            "longitude": lons[i],
                            "station": "",
                            "horizon": 14,
                            "hour": hour,
                            "level": str(level),
                            "q05": q05[i],
                            "q50": q50[i],
                            "q95": q95[i],
                        })

    return pd.DataFrame(all_rows)


def predict_v8_pressure_speed():
    print("Predicting v8 pressure speed (d1/d7)...")
    all_rows = []

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


def generate_v13():
    print("\n" + "=" * 60)
    print("Generating V13 submission")
    print("=" * 60)
    t0 = time.time()

    v8_speed = predict_v8_pressure_speed()
    d14_speed = predict_d14_pressure_speed()
    new_speed = pd.concat([v8_speed, d14_speed], ignore_index=True)
    print(f"  Pressure speed rows: {len(new_speed):,} (v8 d1/d7: {len(v8_speed):,}, d14: {len(d14_speed):,})")

    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    for c in ["latitude", "longitude"]:
        bl_grid[c] = bl_grid[c].astype(float).round(2)
        new_speed[c] = new_speed[c].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)
    new_speed["horizon"] = new_speed["horizon"].astype(int)
    new_speed["hour"] = new_speed["hour"].astype(int)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    bl_with_new = bl_grid.merge(
        new_speed[merge_keys + ["q05", "q50", "q95"]],
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
    save_submission(submission, "v13")


if __name__ == "__main__":
    train_d14_models()
    generate_v13()
