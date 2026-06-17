"""V53: narrow pressure-shear speed probe.

V52 showed that direct spatial replacement is unsafe even with a tight scope.
V53 moves to a more physical feature lane: pressure-level wind speed, cubic
wind speed, and vertical shear features. The first probe is deliberately narrow
because v48 already showed hidden-split signal on East China Sea pressure d7
speed while broader speed retraining damaged North Sea.

Scope:
- base: v51
- changed rows: grid / east_china_sea / pressure levels / horizon d7
- changed columns: q05, q50, q95 only
"""

from __future__ import annotations

import gc
import json
import pickle
import re
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.preprocessing import PowerTransformer

from src.data.paths import (
    FEATURES_DIR,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    PROJECT_ROOT,
    TRAIN_DIR,
    TRAIN_END,
    TRAIN_START,
    VAL_END,
    VAL_START,
)
from src.pipeline.pipeline_utils import save_submission
from src.pipeline.submission_guards import (
    Q_COLS,
    assert_base_file,
    assert_prediction_scope,
    write_manifest,
)


VERSION = "v53"
BASE_VERSION = "v51"
EXPECTED_BASE_FILE = "predictions_v51.csv"
REGION = "east_china_sea"
TARGET_LEVELS = [str(level) for level in PRESSURE_LEVELS]
TARGET_HORIZONS = [7]
FORECAST_HORIZONS = [1, 7, 10]
QUANTILES = [0.05, 0.50, 0.95]
MAX_TRAIN_ROWS = 500_000
EARLY_STOPPING_ROUNDS = 50
OUT_DIR = LOGS_DIR / "pressure_shear_v53"

LGBM_PARAMS = {
    "n_estimators": 1000,
    "max_depth": 7,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 50,
    "verbose": -1,
    "n_jobs": -1,
}

_UV_RE = re.compile(r"^fcst_([uv])_(1000|925|850|700|500)_d(1|7|10)_h(0|6|12|18)$")


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def _load_selected_features() -> dict:
    path = FEATURES_DIR / f"selected_features_heavy_per_level_{REGION}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing selected feature file: {path}")
    with path.open() as f:
        return json.load(f)


def _uv_contexts(columns: list[str]) -> set[tuple[str, int, int]]:
    contexts: set[tuple[str, int, int]] = set()
    colset = set(columns)
    for col in columns:
        match = _UV_RE.match(col)
        if not match:
            continue
        _, level, horizon, hour = match.groups()
        u_col = f"fcst_u_{level}_d{horizon}_h{hour}"
        v_col = f"fcst_v_{level}_d{horizon}_h{hour}"
        if u_col in colset and v_col in colset:
            contexts.add((level, int(horizon), int(hour)))
    return contexts


def pressure_uv_columns_for_contexts(contexts: set[tuple[str, int, int]]) -> set[str]:
    """Return required pressure forecast u/v columns for feature contexts."""

    cols: set[str] = set()
    for level, horizon, hour in contexts:
        cols.add(f"fcst_u_{level}_d{horizon}_h{hour}")
        cols.add(f"fcst_v_{level}_d{horizon}_h{hour}")
    return cols


def add_pressure_physics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add pressure-speed, ws^3, and vertical-shear forecast features."""

    out = df.copy()
    contexts = _uv_contexts(list(out.columns))
    for level, horizon, hour in sorted(contexts, key=lambda x: (x[1], x[2], int(x[0]))):
        u_col = f"fcst_u_{level}_d{horizon}_h{hour}"
        v_col = f"fcst_v_{level}_d{horizon}_h{hour}"
        ws_col = f"phys_ws_{level}_d{horizon}_h{hour}"
        ws = np.sqrt(out[u_col].astype(float) ** 2 + out[v_col].astype(float) ** 2)
        out[ws_col] = ws.astype(np.float32)
        out[f"phys_ws3_{level}_d{horizon}_h{hour}"] = np.power(ws, 3).astype(np.float32)

    for horizon in FORECAST_HORIZONS:
        for hour in HOURS:
            for lower, upper in zip(TARGET_LEVELS[:-1], TARGET_LEVELS[1:]):
                lower_col = f"phys_ws_{lower}_d{horizon}_h{hour}"
                upper_col = f"phys_ws_{upper}_d{horizon}_h{hour}"
                if lower_col not in out.columns or upper_col not in out.columns:
                    continue
                shear = out[upper_col] - out[lower_col]
                out[f"phys_shear_{lower}_{upper}_d{horizon}_h{hour}"] = shear.astype(np.float32)
                out[f"phys_shear_abs_{lower}_{upper}_d{horizon}_h{hour}"] = np.abs(shear).astype(np.float32)

            low_col = f"phys_ws_{TARGET_LEVELS[0]}_d{horizon}_h{hour}"
            high_col = f"phys_ws_{TARGET_LEVELS[-1]}_d{horizon}_h{hour}"
            if low_col in out.columns and high_col in out.columns:
                bulk = out[high_col] - out[low_col]
                out[f"phys_bulk_shear_{TARGET_LEVELS[0]}_{TARGET_LEVELS[-1]}_d{horizon}_h{hour}"] = bulk.astype(np.float32)
                out[f"phys_bulk_shear_abs_{TARGET_LEVELS[0]}_{TARGET_LEVELS[-1]}_d{horizon}_h{hour}"] = np.abs(bulk).astype(np.float32)
    return out


def _target_mask(frame: pd.DataFrame) -> pd.Series:
    normalized = frame.copy()
    normalized["horizon"] = normalized["horizon"].astype(int)
    return (
        normalized["type"].eq("grid")
        & normalized["region"].eq(REGION)
        & normalized["level"].astype(str).isin(TARGET_LEVELS)
        & normalized["horizon"].isin(TARGET_HORIZONS)
    )


def assert_v53_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, int]:
    """Validate that v53 changes only ECS pressure d7 grid speed."""

    return assert_prediction_scope(
        base,
        candidate,
        _target_mask(candidate),
        expect_speed_changes=True,
        expect_direction_changes=False,
    )


def _build_speed_lookup(level: str) -> pd.Series:
    path = TRAIN_DIR / f"reanalysis_pressure_{REGION}.parquet"
    df = pd.read_parquet(path, columns=["time", "latitude", "longitude", f"u_{level}", f"v_{level}"])
    df["speed"] = np.sqrt(df[f"u_{level}"] ** 2 + df[f"v_{level}"] ** 2)
    df["time"] = pd.to_datetime(df["time"])
    df["latitude"] = df["latitude"].astype(float).round(2)
    df["longitude"] = df["longitude"].astype(float).round(2)
    df = df.drop_duplicates(subset=["time", "latitude", "longitude"])
    return df.set_index(["time", "latitude", "longitude"])["speed"].sort_index()


def _lookup_targets(features_df: pd.DataFrame, speed_lookup: pd.Series, horizon: int, hour: int) -> np.ndarray:
    target_time = features_df["time"] + pd.Timedelta(days=horizon, hours=hour)
    keys = pd.MultiIndex.from_arrays(
        [target_time.values, features_df["latitude"].values, features_df["longitude"].values]
    )
    return speed_lookup.reindex(keys).to_numpy()


def _train_quantile_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> dict | None:
    valid_train = np.isfinite(y_train)
    valid_val = np.isfinite(y_val)
    if valid_train.sum() < 500 or valid_val.sum() < 100:
        return None

    X_t = X_train[valid_train]
    y_t = y_train[valid_train]
    X_v = X_val[valid_val]
    y_v = y_val[valid_val]

    transformer = PowerTransformer(method="yeo-johnson", standardize=True)
    y_t_trans = transformer.fit_transform(y_t.reshape(-1, 1)).ravel()
    y_v_trans = transformer.transform(y_v.reshape(-1, 1)).ravel()

    models = []
    for quantile in QUANTILES:
        model = lgb.LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            random_state=53,
            **LGBM_PARAMS,
        )
        callbacks = [
            lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False),
            lgb.log_evaluation(0),
        ]
        model.fit(X_t, y_t_trans, eval_set=[(X_v, y_v_trans)], callbacks=callbacks)
        models.append(model)

    return {
        "models": models,
        "transformer": transformer,
        "best_iteration": int(models[1].best_iteration_ or models[1].n_estimators),
    }


def _predict_quantiles(model_dict: dict, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    transformer = model_dict["transformer"]
    preds = []
    for model in model_dict["models"]:
        pred_trans = model.predict(X)
        pred = transformer.inverse_transform(pred_trans.reshape(-1, 1)).ravel()
        preds.append(pred)
    stacked = np.column_stack(preds)
    stacked.sort(axis=1)
    return np.maximum(stacked[:, 0], 0.0), stacked[:, 1], np.maximum(stacked[:, 2], 0.0)


def _forecast_contexts_for_training(selected: dict, available: set[str]) -> set[tuple[str, int, int]]:
    contexts = _uv_contexts(list(available))
    selected_cols: set[str] = set()
    for level in TARGET_LEVELS:
        for horizon in TARGET_HORIZONS:
            for hour in HOURS:
                selected_cols.update(selected[level].get(f"speed_d{horizon}_h{hour}", []))
    selected_contexts = _uv_contexts(sorted(selected_cols & available))

    # Always include the closest available pressure column stack for each target
    # horizon so shear is available even when the heavy baseline selector chose
    # only one level's u/v columns. HRES has d1/d7/d10 forecasts, not d14.
    forced_horizons = {min(FORECAST_HORIZONS, key=lambda forecast_h: abs(forecast_h - h)) for h in TARGET_HORIZONS}
    forced = {
        (level, horizon, hour)
        for level in TARGET_LEVELS
        for horizon in forced_horizons
        for hour in HOURS
        if f"fcst_u_{level}_d{horizon}_h{hour}" in available
        and f"fcst_v_{level}_d{horizon}_h{hour}" in available
    }
    return (selected_contexts | forced) & contexts


def _load_and_prepare_training_frame() -> pd.DataFrame:
    selected = _load_selected_features()
    needed = {"time", "latitude", "longitude"}
    for level in TARGET_LEVELS:
        for horizon in TARGET_HORIZONS:
            for hour in HOURS:
                needed.update(selected[level].get(f"speed_d{horizon}_h{hour}", []))

    path = FEATURES_DIR / f"train_{REGION}.parquet"
    available = set(pq.ParquetFile(path).schema.names)
    contexts = _forecast_contexts_for_training(selected, available)
    keep = sorted((needed | pressure_uv_columns_for_contexts(contexts)) & available)
    df = pd.read_parquet(path, columns=keep)
    df["time"] = pd.to_datetime(df["time"])
    df["latitude"] = df["latitude"].astype(float).round(2)
    df["longitude"] = df["longitude"].astype(float).round(2)
    return add_pressure_physics_features(df)


def _feature_columns(frame: pd.DataFrame, base_features: list[str]) -> list[str]:
    phys_cols = [col for col in frame.columns if col.startswith("phys_")]
    cols = list(base_features) + [col for col in phys_cols if col not in base_features]
    return [col for col in cols if col in frame.columns]


def train_v53_models() -> dict:
    """Train the ECS pressure d7 physics-feature speed models."""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    selected = _load_selected_features()
    frame = _load_and_prepare_training_frame()

    train_mask = (frame["time"] >= TRAIN_START) & (frame["time"] <= TRAIN_END)
    val_mask = (frame["time"] >= VAL_START) & (frame["time"] <= VAL_END)
    train_full = frame.loc[train_mask].copy()
    val_frame = frame.loc[val_mask].copy()

    if len(train_full) > MAX_TRAIN_ROWS:
        rng = np.random.RandomState(53)
        train_frame = train_full.iloc[rng.choice(len(train_full), MAX_TRAIN_ROWS, replace=False)].copy()
    else:
        train_frame = train_full

    print(f"  Training rows: {len(train_frame):,}; validation rows: {len(val_frame):,}")
    phys_cols = [col for col in frame.columns if col.startswith("phys_")]
    print(f"  Pressure physics features: {len(phys_cols):,}")

    models: dict[str, dict] = {}
    for level in TARGET_LEVELS:
        print(f"\n  Target pressure level: {level}")
        lookup = _build_speed_lookup(level)
        for horizon in TARGET_HORIZONS:
            for hour in HOURS:
                target_col = f"speed_d{horizon}_h{hour}"
                key = f"{REGION}|{level}|d{horizon}|h{hour}"
                feat_cols = _feature_columns(train_frame, selected[level][target_col])
                X_train = train_frame[feat_cols].astype(np.float32).to_numpy()
                X_val = val_frame[feat_cols].astype(np.float32).to_numpy()
                y_train = _lookup_targets(train_frame, lookup, horizon, hour)
                y_val = _lookup_targets(val_frame, lookup, horizon, hour)

                t0 = time.time()
                result = _train_quantile_models(X_train, y_train, X_val, y_val)
                elapsed = time.time() - t0
                if result is None:
                    print(f"    {key}: skipped")
                    continue
                result["feature_cols"] = feat_cols
                result["n_train"] = int(np.isfinite(y_train).sum())
                result["n_val"] = int(np.isfinite(y_val).sum())
                models[key] = result
                print(
                    f"    {key}: {len(feat_cols)} feats, n={result['n_train']:,}, "
                    f"best={result['best_iteration']}, {elapsed:.1f}s"
                )
        del lookup
        gc.collect()

    with (OUT_DIR / "models.pkl").open("wb") as f:
        pickle.dump(models, f)
    with (OUT_DIR / "model_summary.json").open("w") as f:
        json.dump(
            {
                "version": VERSION,
                "base_version": BASE_VERSION,
                "n_models": len(models),
                "target_region": REGION,
                "target_levels": TARGET_LEVELS,
                "target_horizons": TARGET_HORIZONS,
                "pressure_physics_features": len(phys_cols),
            },
            f,
            indent=2,
        )
    return models


def predict_v53_speed(models: dict) -> pd.DataFrame:
    rows = []
    for window in range(1, 9):
        inf_path = FEATURES_DIR / f"inference_window_{window}_{REGION}.parquet"
        df = pd.read_parquet(inf_path)
        df["latitude"] = df["latitude"].astype(float).round(2)
        df["longitude"] = df["longitude"].astype(float).round(2)
        df = add_pressure_physics_features(df)
        lats = df["latitude"].to_numpy()
        lons = df["longitude"].to_numpy()

        for level in TARGET_LEVELS:
            for horizon in TARGET_HORIZONS:
                for hour in HOURS:
                    key = f"{REGION}|{level}|d{horizon}|h{hour}"
                    if key not in models:
                        continue
                    model = models[key]
                    feat_cols = model["feature_cols"]
                    for col in feat_cols:
                        if col not in df.columns:
                            df[col] = np.nan
                    X = df[feat_cols].astype(np.float32).to_numpy()
                    q05, q50, q95 = _predict_quantiles(model, X)
                    rows.append(
                        pd.DataFrame(
                            {
                                "window": window,
                                "region": REGION,
                                "latitude": lats,
                                "longitude": lons,
                                "horizon": horizon,
                                "hour": hour,
                                "level": level,
                                "q05_new": q05,
                                "q50_new": q50,
                                "q95_new": q95,
                            }
                        )
                    )
        print(f"  Inference window {window}: done")
        del df
        gc.collect()

    return pd.concat(rows, ignore_index=True)


def apply_v53_speed(base: pd.DataFrame, speed_df: pd.DataFrame) -> pd.DataFrame:
    """Merge narrow v53 speed predictions into a v51 base."""

    out = base.copy()
    out["_row_order"] = np.arange(len(out))
    grid_mask = out["type"].eq("grid")
    grid = out.loc[grid_mask].copy()
    stations = out.loc[~grid_mask].copy()

    for frame in (grid, speed_df):
        frame["latitude"] = frame["latitude"].astype(float).round(2)
        frame["longitude"] = frame["longitude"].astype(float).round(2)
        frame["horizon"] = frame["horizon"].astype(int)
        frame["hour"] = frame["hour"].astype(int)
        frame["level"] = frame["level"].astype(str)

    keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    merged = grid.merge(speed_df, on=keys, how="left")
    target = merged["q50_new"].notna()
    for col in Q_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_new"].astype(float)
    merged = merged.drop(columns=[col for col in merged.columns if col.endswith("_new")])
    combined = pd.concat([merged, stations], ignore_index=True)
    combined = combined.sort_values("_row_order").drop(columns=["_row_order"])
    return combined.reset_index(drop=True)


def generate_v53() -> None:
    horizon_label = "+".join(f"d{h}" for h in TARGET_HORIZONS)
    print("\n" + "=" * 60)
    print(f"Generating {VERSION.upper()} submission ({REGION} pressure {horizon_label} speed with shear/ws3)")
    print("=" * 60)

    base_path = _phase1_path(EXPECTED_BASE_FILE)
    base_hash = assert_base_file(base_path, EXPECTED_BASE_FILE)

    print("\n[1/4] Training pressure physics models")
    t0 = time.time()
    models = train_v53_models()
    print(f"  Trained {len(models)} models in {(time.time() - t0) / 60:.1f} min")

    print("\n[2/4] Predicting inference rows")
    speed_df = predict_v53_speed(models)
    print(f"  Candidate speed rows: {len(speed_df):,}")

    print(f"\n[3/4] Merging into {BASE_VERSION} base")
    base = _load_predictions_csv(base_path)
    candidate = apply_v53_speed(base, speed_df)
    metrics = assert_v53_scope(base, candidate)
    print(f"  Speed rows changed: {metrics['speed_changed_rows']:,}")
    print(f"  Direction rows changed: {metrics['direction_changed_rows']:,}")

    manifest = write_manifest(
        OUT_DIR,
        version=VERSION,
        base_version=BASE_VERSION,
        base_path=base_path,
        base_hash=base_hash,
        donor_versions=[],
        scope=f"grid/{REGION}/pressure/{horizon_label}/speed_only",
        metrics=metrics,
    )
    print(f"  Manifest: {manifest}")

    print("\n[4/4] Saving submission")
    save_submission(candidate, VERSION)


if __name__ == "__main__":
    generate_v53()
