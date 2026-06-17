"""V21: Retrain overfitting direction models with stronger regularization.

Overfitting models identified from v7 scores:
- ECS 500hPa d1: val=45.3, tune=88.4 (ratio 1.95) SEVERE
- ECS 500hPa d7: val=120.0, tune=222.7 (ratio 1.86) SEVERE
- ECS 1000hPa d1: val=96.4, tune=138.4 (ratio 1.44) MODERATE
- ECS 100m d1: val=97.2, tune=138.5 (ratio 1.42) MODERATE

All d14 direction models also retrained with stronger regularization.

Speed: v8 residual for pressure, baseline for surface (same as v16).
Direction: v21 retrained where overfitting, v7 elsewhere, baseline for NS d14.

Usage: python src/pipeline/run_v21.py
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
from src.io.dataset import load_features, load_inference_features
from src.models.direction import DirectionModel
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
)
from src.scoring.winkler import _circ_dist, circular_winkler_score

SAVE_DIR_V21 = LOGS_DIR / "direction_models_v21"
DIR_MODEL_DIR_V7 = LOGS_DIR / "direction_models_v7"
SPEED_MODEL_DIR_V8 = LOGS_DIR / "speed_models_v8"

OVERFIT_PARAMS = {
    "n_estimators": 500,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "min_child_samples": 200,
    "num_leaves": 31,
    "reg_lambda": 1.0,
    "reg_alpha": 0.1,
    "verbose": -1,
    "n_jobs": -1,
}

D14_PARAMS = {
    "n_estimators": 400,
    "max_depth": 3,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.6,
    "min_child_samples": 300,
    "num_leaves": 15,
    "reg_lambda": 2.0,
    "reg_alpha": 0.5,
    "verbose": -1,
    "n_jobs": -1,
}

RETRAIN_OVERFIT = [
    ("east_china_sea", "500", 1),
    ("east_china_sea", "500", 7),
    ("east_china_sea", "1000", 1),
    ("east_china_sea", "100m", 1),
]

RETRAIN_D14 = [
    (region, level, 14) for region in REGIONS for level in ALL_LEVELS
]


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


def train_direction_model(region, level, horizon, params):
    label = f"{region}/{level}/d{horizon}"
    print(f"\n--- {label} ---")
    try:
        df, feat_cols = build_training_frame(region, level, horizon)
    except ValueError as e:
        print(f"  SKIP: {e}")
        return None

    tr, vl, tu, ho = split_by_time(df)
    print(f"  train={len(tr):,} val={len(vl):,} tune={len(tu):,}")

    if len(tr) < 300 or len(tu) < 50:
        print("  SKIP: insufficient data")
        return None

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

    model = DirectionModel(
        centre_backend="lightgbm",
        halfwidth_backend="lightgbm",
        params=params,
    )
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

    save_path = SAVE_DIR_V21 / region / level / f"d{horizon}"
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

    return {"model": model, "feature_cols": all_cols, "scores": scores}


def train_regularized_directions():
    print("=" * 60)
    print("V21: Training regularized direction models")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR_V21.mkdir(parents=True, exist_ok=True)

    retrain_set = set(RETRAIN_OVERFIT) | set(RETRAIN_D14)

    results = []
    for region, level, horizon in sorted(retrain_set):
        label = f"{region}/{level}/d{horizon}"
        is_d14 = horizon == 14
        is_overfit = (region, level, horizon) in set(RETRAIN_OVERFIT)
        params = D14_PARAMS if is_d14 else OVERFIT_PARAMS
        tag = "d14-strong" if is_d14 else ("overfit" if is_overfit else "default")
        print(f"\n[{tag}] {label}")
        result = train_direction_model(region, level, horizon, params)
        if result is not None:
            scores = result["scores"]
            results.append({
                "region": region,
                "level": level,
                "horizon": horizon,
                "tag": tag,
                **{f"{k}_cws": v["cws"] for k, v in scores.items()},
                **{f"{k}_mae": v["mae"] for k, v in scores.items()},
            })

    summary = pd.DataFrame(results)
    summary.to_csv(SAVE_DIR_V21 / "summary.csv", index=False)
    print(f"\nTraining done in {time.time()-t0:.0f}s")
    if not summary.empty:
        print(summary.to_string(index=False))
    return summary


def _skip_direction(region: str, level: str, horizon: int) -> bool:
    if region == "north_sea" and horizon == 14:
        return True
    if region == "north_sea" and horizon == 7 and level in ("10m", "100m"):
        return True
    return False


def _use_v21(region: str, level: str, horizon: int) -> bool:
    v21_set = set(RETRAIN_OVERFIT) | set(RETRAIN_D14)
    return (region, level, horizon) in v21_set


def predict_direction_v21():
    print("Predicting direction (v21 regularized + v7 + baseline cherry-pick)...")
    all_dir = {}

    v21_cache = {}
    for region, level, horizon in set(RETRAIN_OVERFIT) | set(RETRAIN_D14):
        p = SAVE_DIR_V21 / region / level / f"d{horizon}" / "model.pkl"
        if p.exists():
            with open(p, "rb") as f:
                v21_cache[(region, level, horizon)] = pickle.load(f)

    v7_cache = {}
    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                p = DIR_MODEL_DIR_V7 / region / level / f"d{horizon}" / "model.pkl"
                if p.exists():
                    with open(p, "rb") as f:
                        v7_cache[(region, level, horizon)] = pickle.load(f)

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                if _skip_direction(region, level, horizon):
                    continue

                if _use_v21(region, level, horizon):
                    art = v21_cache.get((region, level, horizon))
                else:
                    art = v7_cache.get((region, level, horizon))

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


def predict_pressure_speed():
    print("Predicting pressure speed from v8 residual models...")
    from src.pipeline.run_v8 import build_speed_features, compute_hres_speed

    all_rows = []
    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            for horizon in HORIZONS:
                model_path = SPEED_MODEL_DIR_V8 / region / str(level) / f"d{horizon}" / "model.pkl"
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


def generate_v21():
    print("\n" + "=" * 60)
    print("Generating V21 submission")
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

    n_surface = bl_with_pspeed[bl_with_pspeed["level"].isin(SURFACE_LEVELS)].shape[0]
    print(f"  Grid: pressure speed replaced, {n_surface:,} surface rows kept baseline")

    all_dir = predict_direction_v21()
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
    save_submission(submission, "v21")


if __name__ == "__main__":
    train_regularized_directions()
    generate_v21()
