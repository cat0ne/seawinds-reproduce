"""V22: Per-horizon hyperparameter tuning for pressure speed models.

Different horizons have different signal strengths:
- d1: strong HRES signal → less regularization needed
- d7: moderate signal → moderate regularization
- d14: weak/no signal → heavy regularization

Grid search over key hyperparameters per horizon, evaluate on VAL split,
retrain with best params, then assemble submission using v16 cherry-pick
direction and height-corrected station baselines.

Usage: python src/pipeline/run_v22.py
"""
from __future__ import annotations

import pickle
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import (
    ALPHA,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SURFACE_LEVELS,
)
from src.io.dataset import load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    align_columns,
    apply_height_correction,
    fix_crossing,
    load_baseline,
    save_submission,
    split_by_time,
)
from src.pipeline.run_v16 import predict_direction_v7_cherry
from src.pipeline.run_v8 import build_speed_features, build_training_data, compute_hres_speed
from src.scoring.winkler import winkler_score

SEARCH_DIR = LOGS_DIR / "hp_search_v22"
SAVE_DIR = LOGS_DIR / "speed_models_v22"

PARAM_GRID = {
    1: [
        {"n_estimators": 800, "max_depth": 7, "learning_rate": 0.05, "min_child_samples": 50, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 1000, "max_depth": 6, "learning_rate": 0.03, "min_child_samples": 80, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 600, "max_depth": 8, "learning_rate": 0.08, "min_child_samples": 40, "subsample": 0.9, "colsample_bytree": 0.9},
    ],
    7: [
        {"n_estimators": 800, "max_depth": 7, "learning_rate": 0.05, "min_child_samples": 50, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 1000, "max_depth": 5, "learning_rate": 0.03, "min_child_samples": 100, "subsample": 0.7, "colsample_bytree": 0.7},
        {"n_estimators": 600, "max_depth": 6, "learning_rate": 0.05, "min_child_samples": 80, "subsample": 0.8, "colsample_bytree": 0.8},
    ],
    14: [
        {"n_estimators": 800, "max_depth": 7, "learning_rate": 0.05, "min_child_samples": 50, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.03, "min_child_samples": 150, "subsample": 0.7, "colsample_bytree": 0.6},
    ],
}


def _full_params(base: dict) -> dict:
    p = dict(base)
    p["verbose"] = -1
    p["n_jobs"] = -1
    return p


def _train_quantile_models(X_tr, y_tr, X_vl, y_vl, params):
    models = {}
    for q in [0.05, 0.50, 0.95]:
        m = LGBMRegressor(objective="quantile", alpha=q, **params)
        if X_vl is not None and len(X_vl) > 50:
            m.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
        else:
            m.fit(X_tr, y_tr)
        models[q] = m
    return models


def _evaluate_on_split(models, X, y_actual, hres_speed):
    if X is None or len(X) == 0 or hres_speed is None:
        return None, None, None
    pred_05 = models[0.05].predict(X)
    pred_50 = models[0.50].predict(X)
    pred_95 = models[0.95].predict(X)
    q05 = np.maximum(hres_speed + pred_05, 0)
    q50 = hres_speed + pred_50
    q95 = hres_speed + pred_95
    actual = y_actual + hres_speed
    score = winkler_score(actual, q05, q95, alpha=ALPHA)
    coverage = ((actual >= q05) & (actual <= q95)).mean()
    width = float(np.mean(q95 - q05))
    return score, coverage, width


def search_speed_hyperparams():
    print("=" * 60)
    print("V22: Hyperparameter search for pressure speed models")
    print("=" * 60)
    t0 = time.time()
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    best_configs: dict[tuple, tuple] = {}

    for region in REGIONS:
        print(f"\n=== {region} ===")
        for level in PRESSURE_LEVELS:
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

                if len(tr) < 200 or len(vl) < 50:
                    continue

                X_tr = build_speed_features(tr, feat_cols_ref, horizon, 0, level)
                y_tr = tr["residual"].values.astype(np.float32)
                X_vl = build_speed_features(vl, feat_cols_ref, horizon, 0, level)
                y_vl = vl["residual"].values.astype(np.float32)
                hres_vl = compute_hres_speed(vl, level, horizon, 0)

                all_cols = sorted(set(X_tr.columns) | set(X_vl.columns))
                X_tr = align_columns(X_tr, all_cols)
                X_vl = align_columns(X_vl, all_cols)

                grid = PARAM_GRID.get(horizon, PARAM_GRID[1])
                best_score = float("inf")
                best_idx = 0

                for pidx, base_params in enumerate(grid):
                    params = _full_params(base_params)
                    models = _train_quantile_models(X_tr, y_tr, X_vl, y_vl, params)
                    score, coverage, width = _evaluate_on_split(models, X_vl, y_vl, hres_vl)
                    if score is None:
                        continue

                    results.append({
                        "region": region,
                        "level": level,
                        "horizon": horizon,
                        "param_idx": pidx,
                        "val_winkler": round(score, 4),
                        "val_coverage": round(coverage, 4),
                        "val_width": round(width, 4),
                    })
                    print(f"    config[{pidx}]: winkler={score:.4f} cov={coverage:.3f} width={width:.2f} "
                          f"(d={base_params['max_depth']} n={base_params['n_estimators']} lr={base_params['learning_rate']})")

                    if score < best_score:
                        best_score = score
                        best_idx = pidx

                best_configs[(region, level, horizon)] = (best_idx, grid[best_idx], best_score)
                print(f"    -> best: config[{best_idx}] winkler={best_score:.4f}")

    results_df = pd.DataFrame(results)
    results_path = SEARCH_DIR / "results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\nResults saved to {results_path}")
    print(f"Search done in {time.time()-t0:.0f}s")
    return best_configs


def retrain_with_best(best_configs: dict):
    print("\n" + "=" * 60)
    print("V22: Retraining with best params per horizon")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    for region in REGIONS:
        print(f"\n=== {region} ===")
        for level in PRESSURE_LEVELS:
            for horizon in HORIZONS:
                key = (region, level, horizon)
                if key not in best_configs:
                    continue

                best_idx, base_params, best_val_score = best_configs[key]
                params = _full_params(base_params)
                print(f"  {level}/d{horizon}: using config[{best_idx}] "
                      f"(d={base_params['max_depth']} n={base_params['n_estimators']} lr={base_params['learning_rate']})")

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

                models = _train_quantile_models(X_tr, y_tr, X_vl, y_vl, params)

                val_score = None
                if X_vl is not None and len(X_vl) > 0:
                    hres_vl = compute_hres_speed(vl, level, horizon, 0)
                    sc, cov, wid = _evaluate_on_split(models, X_vl, y_vl, hres_vl)
                    if sc is not None:
                        val_score = {"coverage": round(cov, 3), "width": round(wid, 2)}
                        print(f"    val: winkler={sc:.4f} coverage={cov:.3f} width={wid:.2f}")

                tune_score = None
                if X_tu is not None and len(X_tu) > 0:
                    hres_tu = compute_hres_speed(tu, level, horizon, 0)
                    sc, cov, wid = _evaluate_on_split(models, X_tu, y_tu, hres_tu)
                    if sc is not None:
                        tune_score = {"coverage": round(cov, 3), "width": round(wid, 2)}
                        print(f"    tune: winkler={sc:.4f} coverage={cov:.3f} width={wid:.2f}")

                save_path = SAVE_DIR / region / level / f"d{horizon}"
                save_path.mkdir(parents=True, exist_ok=True)
                with open(save_path / "model.pkl", "wb") as f:
                    pickle.dump({
                        "models": models,
                        "feature_cols": all_cols,
                        "region": region,
                        "level": level,
                        "horizon": horizon,
                        "params": base_params,
                        "val_score": val_score,
                        "tune_score": tune_score,
                    }, f)

    print(f"\nRetraining done in {time.time()-t0:.0f}s")


def predict_pressure_speed_v22():
    print("Predicting pressure speed from v22 models...")
    all_rows = []

    for region in REGIONS:
        for level in PRESSURE_LEVELS:
            for horizon in HORIZONS:
                model_path = SAVE_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    model_path = LOGS_DIR / "speed_models_v8" / region / level / f"d{horizon}" / "model.pkl"
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
                                "level": level,
                                "q05": q05[i],
                                "q50": q50[i],
                                "q95": q95[i],
                            })

    return pd.DataFrame(all_rows)


def generate_v22():
    print("\n" + "=" * 60)
    print("Generating V22 submission")
    print("=" * 60)
    t0 = time.time()

    best_configs = search_speed_hyperparams()

    retrain_with_best(best_configs)

    print("\nBuilding submission...")
    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    bl_grid["latitude"] = bl_grid["latitude"].astype(float).round(2)
    bl_grid["longitude"] = bl_grid["longitude"].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)

    pressure_speed = predict_pressure_speed_v22()
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

    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    print(f"  Done in {time.time()-t0:.0f}s")
    save_submission(submission, "v22")


if __name__ == "__main__":
    generate_v22()
