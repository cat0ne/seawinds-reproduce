"""V30: Pressure-conditioned station speed overlay on top of v28.

V28 is the current promoted base. Its station speed comes from the v19
station-MOS model, which uses surface HRES/reanalysis features but leaves the
available HRES pressure-level wind stack mostly unused. This variant trains a
station speed model with pressure-level u/v wind features and applies it only
to station d1/d7 speed quantiles when validation blending beats the v19 model.

Usage:
    python -m src.pipeline.run_v30
"""

from __future__ import annotations

import pickle
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    HOURS,
    LOGS_DIR,
    PROJECT_ROOT,
    REGIONS,
    SCORING_DIR,
    TRAIN_DIR,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import fix_crossing, save_submission
from src.pipeline.run_v19 import (
    HORIZON_MAP,
    STATION_SPEED_DIR as V19_STATION_SPEED_DIR,
    _STATION_MAP,
    _station_speed_features as _station_speed_features_v19,
)
from src.scoring.winkler import winkler_score


TARGET_HORIZONS = (1, 7)
PRESSURE_LEVELS_FOR_STATIONS = ("1000", "925", "850", "700", "500")
V30_STATION_SPEED_DIR = LOGS_DIR / "station_speed_models_v30_pressure"
Q_COLS = ["q05", "q50", "q95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]
BLEND_WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def _pressure_feature_cols() -> list[str]:
    cols = [
        "fcst_speed", "fcst_dir",
        "ws10", "wd10", "ws100", "wd100", "wind_shear",
        "t2m", "msl", "sshf", "blh", "cape",
        "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d", "ws10_rstd7d",
        "msl_lag1d", "msl_lag3d", "t2m_lag1d", "t2m_lag3d",
        "z700", "z700_lag1d", "z700_lag3d", "z700_lag7d",
        "elevation", "height_m", "stat_lat", "stat_lon",
        "month_sin", "month_cos", "doy_sin", "doy_cos",
        "hour_0", "hour_6", "hour_12", "hour_18",
        "station_id",
    ]
    for level in PRESSURE_LEVELS_FOR_STATIONS:
        cols.extend([f"p{level}_u", f"p{level}_v", f"p{level}_speed"])
    cols.extend([
        "p_stack_mean", "p_stack_max", "p_stack_min", "p_stack_std",
        "p1000_minus_surface", "p925_minus_surface", "p850_minus_surface",
        "p_low_shear_925_1000", "p_mid_shear_700_925", "p_deep_shear_500_1000",
        "msl_x_p1000_speed", "height_x_p1000_speed",
    ])
    return cols


def _pressure_conditioned_features(
    df: pd.DataFrame,
    feat_cols: list[str],
    horizon: int,
    hour: int,
) -> pd.DataFrame:
    h_key = HORIZON_MAP[horizon]
    result = pd.DataFrame(index=df.index)

    fcst_speed = f"fcst_speed_{h_key}_h{hour}"
    fcst_dir = f"fcst_dir_{h_key}_h{hour}"
    result["fcst_speed"] = df[fcst_speed].astype(float) if fcst_speed in df.columns else np.nan
    result["fcst_dir"] = df[fcst_dir].astype(float) if fcst_dir in df.columns else np.nan

    base_cols = [
        "ws10", "wd10", "ws100", "wd100", "wind_shear",
        "t2m", "msl", "sshf", "blh", "cape",
        "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d", "ws10_rstd7d",
        "msl_lag1d", "msl_lag3d", "t2m_lag1d", "t2m_lag3d",
        "z700", "z700_lag1d", "z700_lag3d", "z700_lag7d",
        "elevation", "height_m",
    ]
    for col in base_cols:
        if col in df.columns:
            result[col] = df[col].astype(float)

    if "latitude" in df.columns:
        result["stat_lat"] = df["latitude"].astype(float)
    if "longitude" in df.columns:
        result["stat_lon"] = df["longitude"].astype(float)

    if "time" in df.columns:
        dt = pd.to_datetime(df["time"])
    else:
        dt = pd.to_datetime(df["issue_time"])
    result["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    result["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    result["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
    result["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

    for hr in HOURS:
        result[f"hour_{hr}"] = int(hr == hour)

    pressure_speeds = []
    for level in PRESSURE_LEVELS_FOR_STATIONS:
        u_col = f"fcst_u_{level}_{h_key}_h{hour}"
        v_col = f"fcst_v_{level}_{h_key}_h{hour}"
        u = df[u_col].astype(float) if u_col in df.columns else pd.Series(np.nan, index=df.index)
        v = df[v_col].astype(float) if v_col in df.columns else pd.Series(np.nan, index=df.index)
        speed = np.sqrt(u ** 2 + v ** 2)
        result[f"p{level}_u"] = u
        result[f"p{level}_v"] = v
        result[f"p{level}_speed"] = speed
        pressure_speeds.append(result[f"p{level}_speed"])

    stack = pd.concat(pressure_speeds, axis=1)
    result["p_stack_mean"] = stack.mean(axis=1)
    result["p_stack_max"] = stack.max(axis=1)
    result["p_stack_min"] = stack.min(axis=1)
    result["p_stack_std"] = stack.std(axis=1)
    result["p1000_minus_surface"] = result["p1000_speed"] - result["fcst_speed"]
    result["p925_minus_surface"] = result["p925_speed"] - result["fcst_speed"]
    result["p850_minus_surface"] = result["p850_speed"] - result["fcst_speed"]
    result["p_low_shear_925_1000"] = result["p925_speed"] - result["p1000_speed"]
    result["p_mid_shear_700_925"] = result["p700_speed"] - result["p925_speed"]
    result["p_deep_shear_500_1000"] = result["p500_speed"] - result["p1000_speed"]
    result["msl_x_p1000_speed"] = result.get("msl", 0.0) * result["p1000_speed"]
    result["height_x_p1000_speed"] = result.get("height_m", 0.0) * result["p1000_speed"]

    if "station" in df.columns:
        result["station_id"] = df["station"].map(_STATION_MAP).fillna(-1).astype(int)

    for col in feat_cols:
        if col not in result.columns:
            result[col] = 0.0

    return result[feat_cols]


def _build_station_training_frame(region: str, horizon: int) -> pd.DataFrame:
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)

    obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
    obs["time"] = pd.to_datetime(obs["time"])
    obs = obs.dropna(subset=["speed"])

    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    region_meta = meta[meta["region"] == region]

    rows = []
    for _, mrow in region_meta.iterrows():
        sid = mrow["station"]
        stat_obs = obs[obs["station"] == sid].copy()
        if stat_obs.empty:
            continue

        nlat = round(float(mrow["nearest_grid_lat"]), 2)
        nlon = round(float(mrow["nearest_grid_lon"]), 2)
        grid_feats = features[
            (features["latitude"] == nlat) & (features["longitude"] == nlon)
        ].copy()
        if grid_feats.empty:
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
            merged["height_m"] = float(mrow["height_m"])
            merged["latitude"] = float(mrow["latitude"])
            merged["longitude"] = float(mrow["longitude"])
            merged["hour"] = int(hour)
            merged["horizon"] = int(horizon)
            rows.append(merged)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _build_feature_matrix(df: pd.DataFrame, feat_cols: list[str], horizon: int) -> pd.DataFrame:
    parts = []
    for hour in HOURS:
        hour_rows = df[df["hour"].astype(int) == int(hour)]
        if hour_rows.empty:
            continue
        X_h = _pressure_conditioned_features(hour_rows, feat_cols, horizon, int(hour))
        parts.append(X_h)
    if not parts:
        return pd.DataFrame(columns=feat_cols)
    X = pd.concat(parts).sort_index()
    return X.loc[df.index].fillna(0.0)


def _build_v19_feature_matrix(df: pd.DataFrame, feat_cols: list[str], horizon: int) -> pd.DataFrame:
    parts = []
    for hour in HOURS:
        hour_rows = df[df["hour"].astype(int) == int(hour)]
        if hour_rows.empty:
            continue
        X_h = _station_speed_features_v19(hour_rows, feat_cols, horizon, int(hour))
        X_h["station_id"] = hour_rows["station"].map(_STATION_MAP).fillna(-1).astype(int).values
        parts.append(X_h)
    if not parts:
        return pd.DataFrame(columns=feat_cols)
    X = pd.concat(parts).sort_index()
    return X.loc[df.index].fillna(0.0)


def _predict_artifact(artifact: dict, X: pd.DataFrame, stations: np.ndarray) -> np.ndarray:
    models = artifact["models"]
    pred = np.column_stack([
        models[0.05].predict(X.values.astype(np.float32)),
        models[0.50].predict(X.values.astype(np.float32)),
        models[0.95].predict(X.values.astype(np.float32)),
    ])
    offsets = artifact.get("cqr_offsets", {})
    offset_arr = np.array([offsets.get(str(sid), 0.0) for sid in stations], dtype=float)
    pred[:, 0] = np.maximum(pred[:, 0] - offset_arr, 0.0)
    pred[:, 2] = pred[:, 2] + offset_arr
    return np.sort(pred, axis=1)


def _choose_blend_weight(y: np.ndarray, v19_pred: np.ndarray, v30_pred: np.ndarray) -> tuple[float, dict]:
    scores: dict[float, float] = {}
    for weight in BLEND_WEIGHTS:
        pred = (1.0 - weight) * v19_pred + weight * v30_pred
        pred = np.sort(pred, axis=1)
        scores[float(weight)] = float(winkler_score(y, pred[:, 0], pred[:, 2], alpha=ALPHA))
    best_weight = min(scores, key=scores.get)
    return float(best_weight), scores


def train_pressure_station_speed_models(force: bool = False) -> None:
    print("=" * 60)
    print("V30: Training pressure-conditioned station speed models")
    print("=" * 60)
    t0 = time.time()
    feat_cols = _pressure_feature_cols()
    V30_STATION_SPEED_DIR.mkdir(parents=True, exist_ok=True)

    for region in REGIONS:
        for horizon in TARGET_HORIZONS:
            save_dir = V30_STATION_SPEED_DIR / region / f"d{horizon}"
            model_path = save_dir / "model.pkl"
            if model_path.exists() and not force:
                print(f"  {region}/d{horizon}: cached")
                continue

            print(f"\n=== {region} d{horizon} ===")
            df = _build_station_training_frame(region, horizon)
            if df.empty:
                print("  No data, skipping")
                continue

            X = _build_feature_matrix(df, feat_cols, horizon)
            y = df["obs_speed"].values.astype(float)
            times = pd.to_datetime(df["time"])
            stations = df["station"].values

            train_mask = times < VAL_START
            val_mask = (times >= VAL_START) & (times <= VAL_END)
            tune_mask = (times >= TUNE_START) & (times <= TUNE_END)
            print(f"  Samples train={int(train_mask.sum()):,}, val={int(val_mask.sum()):,}, tune={int(tune_mask.sum()):,}")

            X_train = X.loc[train_mask].values.astype(np.float32)
            y_train = y[train_mask.values]
            models = {}
            for q in [0.05, 0.50, 0.95]:
                dtrain = lgb.Dataset(X_train, label=y_train)
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
                    "seed": 30,
                }
                models[q] = lgb.train(params, dtrain, num_boost_round=300)

            artifact = {
                "models": models,
                "feature_cols": feat_cols,
                "cqr_offsets": {},
                "blend_weight": 0.0,
                "validation_scores_by_weight": {},
                "validation_score_v19": None,
                "validation_score_v30": None,
                "apply_overlay": False,
            }

            X_tune = X.loc[tune_mask]
            y_tune = y[tune_mask.values]
            stations_tune = stations[tune_mask.values]
            for sid in np.unique(stations_tune):
                sid_mask = stations_tune == sid
                if sid_mask.sum() < 10:
                    artifact["cqr_offsets"][sid] = 0.0
                    continue
                raw = np.column_stack([
                    models[0.05].predict(X_tune.loc[sid_mask].values.astype(np.float32)),
                    models[0.95].predict(X_tune.loc[sid_mask].values.astype(np.float32)),
                ])
                residual = np.maximum(raw[:, 0] - y_tune[sid_mask], y_tune[sid_mask] - raw[:, 1])
                q_idx = min(int(np.ceil((1 - ALPHA) * (len(residual) + 1))) - 1, len(residual) - 1)
                artifact["cqr_offsets"][sid] = float(np.sort(residual)[max(q_idx, 0)])

            v19_path = V19_STATION_SPEED_DIR / region / f"d{horizon}" / "model.pkl"
            if v19_path.exists() and val_mask.sum() > 0:
                with open(v19_path, "rb") as f:
                    v19_artifact = pickle.load(f)
                val_rows = df.loc[val_mask].copy()
                X_val_v19 = _build_v19_feature_matrix(
                    val_rows,
                    v19_artifact["feature_cols"],
                    horizon,
                )
                X_val_v30 = X.loc[val_mask]
                y_val = y[val_mask.values]
                stations_val = stations[val_mask.values]
                pred_v19 = _predict_artifact(v19_artifact, X_val_v19, stations_val)
                pred_v30 = _predict_artifact(artifact, X_val_v30, stations_val)
                best_weight, scores = _choose_blend_weight(y_val, pred_v19, pred_v30)
                artifact["blend_weight"] = best_weight
                artifact["validation_scores_by_weight"] = scores
                artifact["validation_score_v19"] = scores[0.0]
                artifact["validation_score_v30"] = scores[1.0]
                artifact["apply_overlay"] = bool(best_weight > 0.0 and scores[best_weight] < scores[0.0])
                print(
                    "  Val Winkler v19={:.3f}, v30={:.3f}, best w={:.2f} score={:.3f}, apply={}".format(
                        scores[0.0],
                        scores[1.0],
                        best_weight,
                        scores[best_weight],
                        artifact["apply_overlay"],
                    )
                )
            else:
                print("  Missing v19 artifact or val rows; overlay disabled")

            save_dir.mkdir(parents=True, exist_ok=True)
            with open(model_path, "wb") as f:
                pickle.dump(artifact, f)

    print(f"\nV30 station speed training done in {time.time() - t0:.0f}s")


def predict_station_speed_v30() -> dict[tuple, tuple[float, float, float, float]]:
    print("\nPredicting station speed with v30 pressure-conditioned models...")
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    all_preds: dict[tuple, tuple[float, float, float]] = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]
        inference_cache = {}
        for horizon in TARGET_HORIZONS:
            model_path = V30_STATION_SPEED_DIR / region / f"d{horizon}" / "model.pkl"
            if not model_path.exists():
                print(f"  {region}/d{horizon}: no model")
                continue
            with open(model_path, "rb") as f:
                artifact = pickle.load(f)
            if not artifact.get("apply_overlay", False):
                print(f"  {region}/d{horizon}: validation gate disabled overlay")
                continue

            feat_cols = artifact["feature_cols"]
            weight = float(artifact.get("blend_weight", 1.0))
            print(f"  {region}/d{horizon}: applying blend weight {weight:.2f}")

            for _, mrow in region_meta.iterrows():
                sid = mrow["station"]
                nlat = round(float(mrow["nearest_grid_lat"]), 2)
                nlon = round(float(mrow["nearest_grid_lon"]), 2)

                for wid in range(1, 9):
                    if wid not in inference_cache:
                        try:
                            inference_cache[wid] = load_inference_features(wid, region)
                        except FileNotFoundError:
                            continue
                    inf = inference_cache[wid]
                    grid = inf[
                        (inf["latitude"].astype(float).round(2) == nlat)
                        & (inf["longitude"].astype(float).round(2) == nlon)
                    ].copy()
                    if grid.empty:
                        continue

                    for hour in HOURS:
                        pred_rows = grid.copy()
                        pred_rows["height_m"] = float(mrow["height_m"])
                        pred_rows["latitude"] = float(mrow["latitude"])
                        pred_rows["longitude"] = float(mrow["longitude"])
                        pred_rows["station"] = sid
                        pred_rows["hour"] = int(hour)
                        pred_rows["horizon"] = int(horizon)
                        X = _pressure_conditioned_features(pred_rows, feat_cols, horizon, int(hour)).fillna(0.0)
                        pred = _predict_artifact(artifact, X, np.array([sid] * len(pred_rows)))

                        for i in range(len(pred_rows)):
                            key = (int(wid), region, sid, int(horizon), int(hour))
                            all_preds[key] = (float(pred[i, 0]), float(pred[i, 1]), float(pred[i, 2]), weight)

        region_count = sum(1 for key in all_preds if key[1] == region)
        print(f"  {region}: {region_count:,} v30 station-speed entries")

    return all_preds


def pressure_conditioned_station_speed_overlay(
    base: pd.DataFrame,
    station_speed: dict[tuple, tuple[float, float, float, float]],
) -> pd.DataFrame:
    """Return `base` with blended v30 station speed for d1/d7 only."""
    out = base.copy()
    if not station_speed:
        return out

    pred_df = pd.DataFrame([
        {
            "window": key[0],
            "region": key[1],
            "station": key[2],
            "horizon": key[3],
            "hour": key[4],
            "q05_v30": value[0],
            "q50_v30": value[1],
            "q95_v30": value[2],
            "blend_weight": value[3],
        }
        for key, value in station_speed.items()
    ])
    pred_df["horizon"] = pred_df["horizon"].astype(int)
    pred_df["hour"] = pred_df["hour"].astype(int)

    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    merged = out.merge(pred_df, on=STATION_KEYS, how="left")
    target_mask = (
        merged["type"].eq("station")
        & merged["horizon"].isin(TARGET_HORIZONS)
        & merged["blend_weight"].notna()
    )

    for col in Q_COLS:
        merged.loc[target_mask, col] = (
            (1.0 - merged.loc[target_mask, "blend_weight"]) * merged.loc[target_mask, col]
            + merged.loc[target_mask, "blend_weight"] * merged.loc[target_mask, f"{col}_v30"]
        )

    merged = merged.drop(columns=["q05_v30", "q50_v30", "q95_v30", "blend_weight"])
    merged = fix_crossing(merged)
    return merged


def generate_v30(force_train: bool = False) -> None:
    print("\n" + "=" * 60)
    print("Generating V30 submission (v28 + pressure-conditioned station speed d1/d7)")
    print("=" * 60)
    t0 = time.time()

    train_pressure_station_speed_models(force=force_train)

    base = _load_predictions_csv(_phase1_path("predictions_v28.csv"))
    station_speed = predict_station_speed_v30()
    submission = pressure_conditioned_station_speed_overlay(base, station_speed)

    q_changed = (
        base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)
    ).any(axis=1)
    dir_changed = (
        base[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True)
        != submission[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True)
    ).any(axis=1)
    allowed = (
        submission["type"].eq("station")
        & submission["horizon"].astype(int).isin(TARGET_HORIZONS)
    )
    unexpected = q_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected speed changes outside station d1/d7: {int(unexpected.sum())}")
    if dir_changed.any():
        raise ValueError(f"Unexpected direction changes: {int(dir_changed.sum())}")

    print(f"  Station speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  Done in {time.time() - t0:.0f}s")
    save_submission(submission, "v30")


if __name__ == "__main__":
    generate_v30()
