"""Shared helpers for late-stage direction breakthrough probes.

The v145-v147 experiments all test distribution-aware direction ideas against
the same failure mode: hidden-regime transfer. This module keeps the circular
math, replay frame assembly, context featurization, and conservative submission
updates in one place so each candidate can stay focused on its modeling lever.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import (
    ALPHA,
    HOLDOUT_END,
    HOLDOUT_START,
    HOURS,
    LOGS_DIR,
    PROJECT_ROOT,
    REGIONS,
    TRAIN_DIR,
    TRAIN_END,
    TRAIN_START,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)
from src.pipeline.pipeline_utils import save_submission
from src.scoring.winkler import _circ_dist, circular_winkler_score

ENRICHED_DIR = PROJECT_ROOT / "data" / "phase1_dataset" / "features_enriched"
SCORING_DIR = PROJECT_ROOT / "data" / "phase1_dataset" / "scoring"
BASE_V142_PATH = PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_v142.csv"
BASE_V132_PATH = PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_v132.csv"

SPLIT_RANGES = {
    "train": (pd.Timestamp(TRAIN_START), pd.Timestamp(TRAIN_END)),
    "val": (pd.Timestamp(VAL_START), pd.Timestamp(VAL_END)),
    "tune": (pd.Timestamp(TUNE_START), pd.Timestamp(TUNE_END)),
    "holdout": (pd.Timestamp(HOLDOUT_START), pd.Timestamp(HOLDOUT_END)),
}
EVAL_SPLITS = ("val", "tune", "holdout")

CONTEXT_COLS = [
    "ws10",
    "wd10",
    "ws100",
    "wd100",
    "wind_shear",
    "msl",
    "t2m",
    "z700",
    "blh",
    "cape",
    "sst",
    "ws10_daily_mean",
    "ws10_daily_range",
    "ws10_lag1d",
    "ws10_lag3d",
    "ws10_lag7d",
    "wd10_lag1d",
    "wd10_lag3d",
    "wd10_lag7d",
    "msl_lag1d",
    "msl_lag3d",
    "msl_lag7d",
    "t2m_lag1d",
    "t2m_lag3d",
    "z700_lag1d",
    "z700_lag3d",
    "ws10_rmean3d",
    "ws10_rstd3d",
    "ws10_rmean7d",
    "ws10_rstd7d",
    "ecs_pressure_gradient",
    "ns_pressure_gradient",
    "wpac_pc1",
    "wpac_pc2",
    "wpac_pc3",
    "natl_pc1",
    "natl_pc2",
    "natl_pc3",
    "dist_to_coast_km",
    "lsm",
    "elevation",
    "latitude",
    "longitude",
    "nearest_grid_lat",
    "nearest_grid_lon",
    "station_height_m",
]


def wrap_360(values: np.ndarray | pd.Series | float) -> np.ndarray:
    return np.mod(values, 360.0)


def signed_delta(actual: np.ndarray | pd.Series, predicted: np.ndarray | pd.Series) -> np.ndarray:
    return ((np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float) + 180.0) % 360.0) - 180.0


def direction_to_unit(deg: np.ndarray | pd.Series) -> tuple[np.ndarray, np.ndarray]:
    rad = np.deg2rad(np.asarray(deg, dtype=float))
    return np.cos(rad), np.sin(rad)


def unit_to_direction(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.rad2deg(np.arctan2(y, x)) % 360.0


def circular_mean_residual(residual_deg: np.ndarray, weights: np.ndarray) -> float:
    rad = np.deg2rad(residual_deg)
    s = float(np.sum(weights * np.sin(rad)))
    c = float(np.sum(weights * np.cos(rad)))
    return float(np.rad2deg(np.arctan2(s, c)))


def circular_blend(base_deg: np.ndarray, target_deg: np.ndarray, weight: float) -> np.ndarray:
    bx, by = direction_to_unit(base_deg)
    tx, ty = direction_to_unit(target_deg)
    return unit_to_direction((1.0 - weight) * bx + weight * tx, (1.0 - weight) * by + weight * ty)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    v = np.asarray(values, dtype=float)[order]
    w = np.asarray(weights, dtype=float)[order]
    total = float(np.sum(w))
    if total <= 0:
        return float(np.nanquantile(v, quantile))
    cdf = np.cumsum(w) / total
    return float(v[np.searchsorted(cdf, quantile, side="left").clip(0, len(v) - 1)])


def base_direction_col(horizon: int, hour: int, columns: set[str]) -> str:
    if horizon == 14 and f"fcst_dir_d10_h{hour}" in columns:
        return f"fcst_dir_d10_h{hour}"
    if f"fcst_dir_d{horizon}_h{hour}" in columns:
        return f"fcst_dir_d{horizon}_h{hour}"
    return f"dir_d{horizon}_h{hour}"


def base_speed_col(horizon: int, hour: int, columns: set[str]) -> str | None:
    if horizon == 14 and f"fcst_speed_d10_h{hour}" in columns:
        return f"fcst_speed_d10_h{hour}"
    if f"fcst_speed_d{horizon}_h{hour}" in columns:
        return f"fcst_speed_d{horizon}_h{hour}"
    if f"speed_d{horizon}_h{hour}" in columns:
        return f"speed_d{horizon}_h{hour}"
    return None


def split_for_target(target_time: pd.Series) -> pd.Series:
    out = pd.Series("", index=target_time.index, dtype=object)
    for split, (start, end) in SPLIT_RANGES.items():
        out.loc[(target_time >= start) & (target_time <= end)] = split
    return out


def score_direction(frame: pd.DataFrame, lo_col: str, hi_col: str, actual_col: str = "actual_direction") -> float:
    return circular_winkler_score(
        frame[actual_col].to_numpy(float),
        frame[lo_col].to_numpy(float),
        frame[hi_col].to_numpy(float),
        alpha=ALPHA,
    )


def half_width(lo: np.ndarray | pd.Series, hi: np.ndarray | pd.Series) -> np.ndarray:
    return ((np.asarray(hi, dtype=float) - np.asarray(lo, dtype=float)) % 360.0) / 2.0


def build_ecs_surface_replay(horizons: tuple[int, ...], rows_per_combo: int, level: str = "10m") -> pd.DataFrame:
    u_col, v_col = ("u10", "v10") if level == "10m" else ("u100", "v100")
    actual = pd.read_parquet(
        TRAIN_DIR / "reanalysis_east_china_sea_6h.parquet",
        columns=["time", "latitude", "longitude", u_col, v_col],
    )
    actual["target_time"] = pd.to_datetime(actual["time"])
    actual["latitude"] = actual["latitude"].astype(float).round(2)
    actual["longitude"] = actual["longitude"].astype(float).round(2)
    actual["actual_direction"] = (270.0 - np.degrees(np.arctan2(actual[v_col], actual[u_col]))) % 360.0
    actual = actual[["target_time", "latitude", "longitude", "actual_direction"]]

    features = pd.read_parquet(ENRICHED_DIR / "train_east_china_sea.parquet")
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    columns = set(features.columns)
    available = [c for c in CONTEXT_COLS if c in columns and c not in {"latitude", "longitude"}]
    frames = []

    for horizon in horizons:
        for hour in HOURS:
            dir_col = base_direction_col(int(horizon), int(hour), columns)
            speed_col = base_speed_col(int(horizon), int(hour), columns)
            cols = ["time", "latitude", "longitude", dir_col] + available
            if speed_col:
                cols.append(speed_col)
            sub = features[cols].copy()
            sub["target_time"] = sub["time"] + pd.Timedelta(days=int(horizon), hours=int(hour))
            sub["split"] = split_for_target(sub["target_time"])
            sub = sub[sub["split"].isin(SPLIT_RANGES)].copy()
            if len(sub) > rows_per_combo * len(SPLIT_RANGES):
                sub = (
                    sub.groupby("split", group_keys=False)
                    .apply(
                        lambda group: group.sample(
                            min(len(group), rows_per_combo),
                            random_state=45100 + int(horizon) * 10 + int(hour),
                        )
                    )
                    .reset_index(drop=True)
                )
            sub["family"] = "surface"
            sub["region"] = "east_china_sea"
            sub["level"] = level
            sub["horizon"] = int(horizon)
            sub["hour"] = int(hour)
            sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce") % 360.0
            sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
            sub = sub.drop(columns=[dir_col] + ([speed_col] if speed_col else []))
            merged = sub.merge(actual, on=["target_time", "latitude", "longitude"], how="inner")
            frames.append(merged.dropna(subset=["base_direction", "actual_direction"]))

    out = pd.concat(frames, ignore_index=True)
    out["signed_residual"] = signed_delta(out["actual_direction"], out["base_direction"])
    out["base_error"] = np.abs(out["signed_residual"])
    return out


def station_metadata(region: str) -> pd.DataFrame:
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    meta = meta[meta["region"].eq(region)].copy()
    meta["nearest_grid_lat"] = meta["nearest_grid_lat"].astype(float).round(2)
    meta["nearest_grid_lon"] = meta["nearest_grid_lon"].astype(float).round(2)
    return meta


def build_station_replay(horizon: int) -> pd.DataFrame:
    frames = []
    for region in REGIONS:
        features = pd.read_parquet(ENRICHED_DIR / f"train_{region}.parquet")
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        columns = set(features.columns)
        available = [c for c in CONTEXT_COLS if c in columns and c not in {"latitude", "longitude"}]
        obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
        obs["target_time"] = pd.to_datetime(obs["time"])
        obs = obs.dropna(subset=["direction"])
        meta = station_metadata(region)
        for station_row in meta.itertuples(index=False):
            grid = features[
                (features["latitude"] == round(float(station_row.nearest_grid_lat), 2))
                & (features["longitude"] == round(float(station_row.nearest_grid_lon), 2))
            ]
            station_obs = obs[obs["station"].eq(station_row.station)][["target_time", "direction"]]
            if grid.empty or station_obs.empty:
                continue
            for hour in HOURS:
                dir_col = base_direction_col(int(horizon), int(hour), columns)
                speed_col = base_speed_col(int(horizon), int(hour), columns)
                cols = ["time", "latitude", "longitude", dir_col] + available
                if speed_col:
                    cols.append(speed_col)
                sub = grid[cols].copy()
                sub["target_time"] = sub["time"] + pd.Timedelta(days=int(horizon), hours=int(hour))
                sub["split"] = split_for_target(sub["target_time"])
                sub = sub[sub["split"].isin(SPLIT_RANGES)].copy()
                sub["family"] = "station"
                sub["region"] = region
                sub["station"] = station_row.station
                sub["station_height_m"] = float(station_row.height_m)
                sub["nearest_grid_lat"] = float(station_row.nearest_grid_lat)
                sub["nearest_grid_lon"] = float(station_row.nearest_grid_lon)
                sub["horizon"] = int(horizon)
                sub["hour"] = int(hour)
                sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce") % 360.0
                sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
                sub = sub.drop(columns=[dir_col] + ([speed_col] if speed_col else []))
                merged = sub.merge(station_obs, on="target_time", how="inner")
                merged = merged.rename(columns={"direction": "actual_direction"})
                frames.append(merged.dropna(subset=["base_direction", "actual_direction"]))
    out = pd.concat(frames, ignore_index=True)
    out["signed_residual"] = signed_delta(out["actual_direction"], out["base_direction"])
    out["base_error"] = np.abs(out["signed_residual"])
    return out


def build_ecs_surface_inference(horizons: tuple[int, ...], level: str = "10m") -> pd.DataFrame:
    frames = []
    for window in range(1, 9):
        features = pd.read_parquet(ENRICHED_DIR / f"inference_window_{window}_east_china_sea.parquet")
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        columns = set(features.columns)
        available = [c for c in CONTEXT_COLS if c in columns and c not in {"latitude", "longitude"}]
        for horizon in horizons:
            for hour in HOURS:
                dir_col = base_direction_col(int(horizon), int(hour), columns)
                speed_col = base_speed_col(int(horizon), int(hour), columns)
                cols = ["time", "latitude", "longitude", dir_col] + available
                if speed_col:
                    cols.append(speed_col)
                sub = features[cols].copy()
                sub["family"] = "surface"
                sub["region"] = "east_china_sea"
                sub["level"] = level
                sub["window"] = int(window)
                sub["horizon"] = int(horizon)
                sub["hour"] = int(hour)
                sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce") % 360.0
                sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
                sub = sub.drop(columns=[dir_col] + ([speed_col] if speed_col else []))
                frames.append(sub.dropna(subset=["base_direction"]))
    return pd.concat(frames, ignore_index=True)


def build_station_inference(horizon: int) -> pd.DataFrame:
    frames = []
    for region in REGIONS:
        meta = station_metadata(region)
        for window in range(1, 9):
            features = pd.read_parquet(ENRICHED_DIR / f"inference_window_{window}_{region}.parquet")
            features["time"] = pd.to_datetime(features["time"])
            features["latitude"] = features["latitude"].astype(float).round(2)
            features["longitude"] = features["longitude"].astype(float).round(2)
            columns = set(features.columns)
            available = [c for c in CONTEXT_COLS if c in columns and c not in {"latitude", "longitude"}]
            for station_row in meta.itertuples(index=False):
                grid = features[
                    (features["latitude"] == round(float(station_row.nearest_grid_lat), 2))
                    & (features["longitude"] == round(float(station_row.nearest_grid_lon), 2))
                ]
                if grid.empty:
                    continue
                for hour in HOURS:
                    dir_col = base_direction_col(int(horizon), int(hour), columns)
                    speed_col = base_speed_col(int(horizon), int(hour), columns)
                    cols = ["time", "latitude", "longitude", dir_col] + available
                    if speed_col:
                        cols.append(speed_col)
                    sub = grid[cols].copy()
                    sub["family"] = "station"
                    sub["region"] = region
                    sub["station"] = station_row.station
                    sub["station_height_m"] = float(station_row.height_m)
                    sub["nearest_grid_lat"] = float(station_row.nearest_grid_lat)
                    sub["nearest_grid_lon"] = float(station_row.nearest_grid_lon)
                    sub["window"] = int(window)
                    sub["horizon"] = int(horizon)
                    sub["hour"] = int(hour)
                    sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce") % 360.0
                    sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
                    sub = sub.drop(columns=[dir_col] + ([speed_col] if speed_col else []))
                    frames.append(sub.dropna(subset=["base_direction"]))
    return pd.concat(frames, ignore_index=True)


def build_context_matrix(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    for col in CONTEXT_COLS:
        if col in frame.columns:
            out[col] = pd.to_numeric(frame[col], errors="coerce")
    out["horizon"] = pd.to_numeric(frame["horizon"], errors="coerce")
    out["hour"] = pd.to_numeric(frame["hour"], errors="coerce")
    if "time" in frame.columns:
        dt = pd.to_datetime(frame["time"])
    else:
        dt = pd.to_datetime(frame["target_time"])
    out["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
    out["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["base_speed"] = pd.to_numeric(frame.get("base_speed", np.nan), errors="coerce")
    out["base_dir_sin"] = np.sin(np.deg2rad(pd.to_numeric(frame["base_direction"], errors="coerce")))
    out["base_dir_cos"] = np.cos(np.deg2rad(pd.to_numeric(frame["base_direction"], errors="coerce")))
    if "station" in frame.columns:
        out["station_id"] = pd.Categorical(frame["station"]).codes.astype(float)
    if "region" in frame.columns:
        out["region_id"] = pd.Categorical(frame["region"]).codes.astype(float)
    out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if columns is not None:
        for col in columns:
            if col not in out.columns:
                out[col] = 0.0
        out = out[columns]
    return out


class ContextAnalog:
    def __init__(self, k: int = 80, min_sigma: float = 0.15):
        self.k = k
        self.min_sigma = min_sigma
        self.scaler = StandardScaler()
        self.columns: list[str] = []
        self.train_residual: np.ndarray | None = None
        self.train_abs_error: np.ndarray | None = None
        self.nn: NearestNeighbors | None = None

    def fit(self, train: pd.DataFrame) -> "ContextAnalog":
        X_df = build_context_matrix(train)
        self.columns = list(X_df.columns)
        X = self.scaler.fit_transform(X_df).astype(np.float32)
        n_neighbors = min(self.k, len(train))
        self.nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
        self.nn.fit(X)
        self.train_residual = train["signed_residual"].to_numpy(float)
        self.train_abs_error = train["base_error"].to_numpy(float)
        return self

    def neighbors(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if self.nn is None:
            raise RuntimeError("ContextAnalog must be fitted first")
        X = self.scaler.transform(build_context_matrix(frame, self.columns)).astype(np.float32)
        return self.nn.kneighbors(X, return_distance=True)

    def predict_residual(self, frame: pd.DataFrame) -> np.ndarray:
        if self.train_residual is None:
            raise RuntimeError("ContextAnalog must be fitted first")
        distances, indices = self.neighbors(frame)
        out = np.empty(len(frame), dtype=float)
        for i, (dist, idx) in enumerate(zip(distances, indices)):
            sigma = max(float(np.nanmedian(dist)), self.min_sigma)
            weights = np.exp(-0.5 * (dist / sigma) ** 2)
            out[i] = circular_mean_residual(self.train_residual[idx], weights)
        return out

    def predict_width(self, frame: pd.DataFrame, quantile: float = 1.0 - ALPHA) -> np.ndarray:
        if self.train_abs_error is None:
            raise RuntimeError("ContextAnalog must be fitted first")
        distances, indices = self.neighbors(frame)
        out = np.empty(len(frame), dtype=float)
        for i, (dist, idx) in enumerate(zip(distances, indices)):
            sigma = max(float(np.nanmedian(dist)), self.min_sigma)
            weights = np.exp(-0.5 * (dist / sigma) ** 2)
            out[i] = weighted_quantile(self.train_abs_error[idx], weights, quantile)
        return out


def add_base_interval(frame: pd.DataFrame, width_map_cols: tuple[str, ...]) -> pd.DataFrame:
    out = frame.copy()
    train = out[out["split"].eq("train")]
    fallback = float(np.nanquantile(train["base_error"], 1.0 - ALPHA)) if len(train) else float(np.nanquantile(out["base_error"], 1.0 - ALPHA))
    widths: dict[tuple, float] = {("__global__",): fallback}
    for keys, group in train.groupby(list(width_map_cols), dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        if len(group) >= 30:
            widths[keys] = float(np.nanquantile(group["base_error"], 1.0 - ALPHA))
    vals = []
    for row in out[list(width_map_cols)].itertuples(index=False, name=None):
        vals.append(widths.get(tuple(row), fallback))
    out["base_hw"] = np.asarray(vals, dtype=float)
    out["base_dir_05"] = wrap_360(out["base_direction"].to_numpy(float) - out["base_hw"].to_numpy(float))
    out["base_dir_95"] = wrap_360(out["base_direction"].to_numpy(float) + out["base_hw"].to_numpy(float))
    return out


def summarize_deltas(report: pd.DataFrame) -> pd.DataFrame:
    return (
        report.groupby("candidate", as_index=False)
        .agg(mean_delta_cws=("delta_cws", "mean"), worst_delta_cws=("delta_cws", "max"), cells=("delta_cws", "size"))
        .sort_values(["mean_delta_cws", "worst_delta_cws"])
    )


def write_manifest(out_dir: Path, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_base_predictions() -> pd.DataFrame:
    path = BASE_V142_PATH if BASE_V142_PATH.exists() else BASE_V132_PATH
    return pd.read_csv(path, engine="python")


def save_version(preds: pd.DataFrame, version: str) -> Path:
    return save_submission(preds, version)


def ensure_only_target_changed(preds: pd.DataFrame, original: pd.DataFrame, target_mask: pd.Series) -> int:
    changed = preds[["dir_05", "dir_50", "dir_95"]].round(6).ne(original[["dir_05", "dir_50", "dir_95"]].round(6)).any(axis=1)
    non_target = int((changed & ~target_mask).sum())
    if non_target:
        raise RuntimeError(f"Non-target direction rows changed: {non_target}")
    return int(changed.sum())
