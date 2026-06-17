"""V20: Retrain direction half-width models with custom circular Winkler objective.

Replaces the quantile loss (90th percentile of circular error) with a smooth
surrogate that directly minimises the circular Winkler score. The centre model
stays the same (MSE on sin/cos decomposition). Conformal calibration is applied
on the tune split to guarantee coverage.

Cherry-pick logic from v16 is preserved:
- NS d14 direction → keep baseline (v7 was worse)
- NS d7 surface (10m, 100m) direction → keep baseline
- All other combos → use v20 custom-loss models

Speed: v8 residual for pressure, baseline for surface.
Stations: baseline + height correction.

Usage: python src/pipeline/run_v20.py
"""
from __future__ import annotations

import pickle
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.data.paths import HORIZONS, HOURS, LOGS_DIR, PRESSURE_LEVELS, REGIONS, SURFACE_LEVELS
from src.io.dataset import load_features, load_inference_features
from src.models.circular_winkler_loss import circular_winkler_eval, circular_winkler_objective
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

SAVE_DIR = LOGS_DIR / "direction_models_v20"
SPEED_MODEL_DIR = LOGS_DIR / "speed_models_v8"

CENTRE_PARAMS = {
    "n_estimators": 500,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 100,
    "verbose": -1,
    "n_jobs": -1,
}

HW_PARAMS = {
    "n_estimators": 500,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 100,
    "verbose": -1,
    "n_jobs": -1,
}


def _circ_dist_local(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b)
    return np.minimum(d, 360.0 - d)


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


def train_centre_model(X_train, y_train, X_val=None, y_val=None):
    rad = np.deg2rad(y_train)
    sin_y = np.sin(rad)
    cos_y = np.cos(rad)

    sin_model = lgb.LGBMRegressor(**CENTRE_PARAMS)
    cos_model = lgb.LGBMRegressor(**CENTRE_PARAMS)

    if X_val is not None and y_val is not None:
        rad_val = np.deg2rad(y_val)
        sin_val = np.sin(rad_val)
        cos_val = np.cos(rad_val)
        sin_model.fit(X_train, sin_y, eval_set=[(X_val, sin_val)],
                      callbacks=[lgb.early_stopping(50, verbose=False)])
        cos_model.fit(X_train, cos_y, eval_set=[(X_val, cos_val)],
                      callbacks=[lgb.early_stopping(50, verbose=False)])
    else:
        sin_model.fit(X_train, sin_y)
        cos_model.fit(X_train, cos_y)

    return sin_model, cos_model


def predict_centre(sin_model, cos_model, X):
    sin_pred = sin_model.predict(X)
    cos_pred = cos_model.predict(X)
    ang_rad = np.arctan2(sin_pred, cos_pred)
    return np.rad2deg(ang_rad) % 360.0


def train_halfwidth_custom(X_train, circ_err_train, X_val=None, circ_err_val=None):
    hw_model = lgb.LGBMRegressor(objective=circular_winkler_objective, **HW_PARAMS)

    if X_val is not None and circ_err_val is not None:
        hw_model.fit(
            X_train, circ_err_train,
            eval_set=[(X_val, circ_err_val)],
            eval_metric=circular_winkler_eval,
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
    else:
        hw_model.fit(X_train, circ_err_train)

    return hw_model


def conformal_calibrate(sin_model, cos_model, hw_model, X_tune, y_tune, alpha=0.1):
    centre_pred = predict_centre(sin_model, cos_model, X_tune)
    hw_pred = np.abs(hw_model.predict(X_tune))
    hw_pred = np.clip(hw_pred, 1.0, 180.0)
    scores = _circ_dist_local(y_tune, centre_pred) - hw_pred
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(q_level, 1.0)
    return float(np.quantile(scores, q_level))


def predict_direction(sin_model, cos_model, hw_model, conformal_offset, X):
    centre = predict_centre(sin_model, cos_model, X)
    hw = np.abs(hw_model.predict(X))
    hw = np.clip(hw, 1.0, 180.0)
    hw = hw + conformal_offset
    hw = np.clip(hw, 0.0, 180.0)
    dir_05 = (centre - hw) % 360.0
    dir_50 = centre % 360.0
    dir_95 = (centre + hw) % 360.0
    return dir_05, dir_50, dir_95


def train_per_horizon_direction():
    print("=" * 60)
    print("V20: Training per-horizon direction models (custom CW loss)")
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

                print("  Training centre model (sin/cos MSE)...")
                sin_model, cos_model = train_centre_model(X_tr, y_tr, X_vl, y_vl)

                centre_pred_tr = predict_centre(sin_model, cos_model, X_tr)
                circ_err_tr = _circ_dist_local(y_tr, centre_pred_tr)

                circ_err_vl = None
                if X_vl is not None and y_vl is not None:
                    centre_pred_vl = predict_centre(sin_model, cos_model, X_vl)
                    circ_err_vl = _circ_dist_local(y_vl, centre_pred_vl)

                print("  Training half-width model (custom circular Winkler)...")
                hw_model = train_halfwidth_custom(X_tr, circ_err_tr, X_vl, circ_err_vl)

                print("  Conformal calibration on tune split...")
                conf_offset = conformal_calibrate(sin_model, cos_model, hw_model, X_tu, y_tune=y_tu)

                scores = {}
                for name, X_s, y_s in [("val", X_vl, y_vl), ("tune", X_tu, y_tu)]:
                    if X_s is None or len(X_s) == 0:
                        continue
                    lo, mid, hi = predict_direction(sin_model, cos_model, hw_model, conf_offset, X_s)
                    cws = circular_winkler_score(y_s, lo, hi, alpha=0.1)
                    mae = float(np.nanmean(_circ_dist(y_s, mid)))
                    scores[name] = {"cws": round(cws, 1), "mae": round(mae, 1)}
                    print(f"  {name}: cWS={cws:.1f}  MAE={mae:.1f}deg  conf_offset={conf_offset:.1f}")

                save_path = SAVE_DIR / region / level / f"d{horizon}"
                save_path.mkdir(parents=True, exist_ok=True)
                with open(save_path / "model.pkl", "wb") as f:
                    pickle.dump({
                        "sin_model": sin_model,
                        "cos_model": cos_model,
                        "hw_model": hw_model,
                        "conformal_offset": conf_offset,
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


def _skip_direction(region: str, level: str, horizon: int) -> bool:
    if region == "north_sea" and horizon == 14:
        return True
    if region == "north_sea" and horizon == 7 and level in ("10m", "100m"):
        return True
    return False


def predict_direction_v20_cherry():
    print("Predicting direction (v20 custom CW loss, cherry-pick)...")
    all_dir = {}

    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                if _skip_direction(region, level, horizon):
                    continue

                model_path = SAVE_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)

                sin_model = art["sin_model"]
                cos_model = art["cos_model"]
                hw_model = art["hw_model"]
                conf_offset = art["conformal_offset"]
                feat_cols = art["feature_cols"]

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    available = [c for c in feat_cols if c in inf.columns]
                    missing = set(feat_cols) - set(available) - {
                        c for c in feat_cols if c.startswith(("hour_", "horizon_", "month_", "doy_"))
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
                        d05, d50, d95 = predict_direction(sin_model, cos_model, hw_model, conf_offset, X)

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
    all_rows = []
    from src.pipeline.run_v8 import build_speed_features, compute_hres_speed

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            for horizon in HORIZONS:
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


def generate_v20():
    print("\n" + "=" * 60)
    print("Generating V20 submission (custom CW loss direction)")
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

    all_dir = predict_direction_v20_cherry()
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
    save_submission(submission, "v20")


if __name__ == "__main__":
    train_per_horizon_direction()
    generate_v20()
