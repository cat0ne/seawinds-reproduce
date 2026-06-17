"""Track D: a local prototype for station-direction forecasting.

The current station-direction path in the repo is still mostly an adjusted
nearest-grid forecast with post-hoc bias handling. This prototype keeps the
scope narrow and structured:

- train one model per region and horizon on station observations from the
  historical training split
- decouple the circular forecast into a center model and a width model
- calibrate the half-width on a trailing slice of the training split
- compare the prototype against a simple nearest-grid bias baseline on the
  validation split

The goal is not to replace the production pipeline yet. The goal is to make a
small, runnable experiment that can tell us whether a proper circular model
actually buys anything locally before we wire it into submission code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

try:  # pragma: no cover - optional dependency
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

from sklearn.ensemble import GradientBoostingRegressor

from src.data.paths import (
    ALPHA,
    HOLDOUT_END,
    HOLDOUT_START,
    HOURS,
    HORIZONS,
    REGIONS,
    SCORING_DIR,
    TRAIN_DIR,
    TRAIN_END,
    TRAIN_START,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)
from src.io.dataset import load_features, load_inference_features
from src.scoring.winkler import _circ_dist, circular_winkler_score


SPLIT_RANGES = {
    "train": (pd.Timestamp(TRAIN_START), pd.Timestamp(TRAIN_END)),
    "val": (pd.Timestamp(VAL_START), pd.Timestamp(VAL_END)),
    "tune": (pd.Timestamp(TUNE_START), pd.Timestamp(TUNE_END)),
    "holdout": (pd.Timestamp(HOLDOUT_START), pd.Timestamp(HOLDOUT_END)),
}

BASE_DROP_COLS = {
    "target_direction",
    "target_time",
    "region",
    "window",
    "split",
}

DIR_COL_CANDIDATES = (
    "wd10",
    "wd100",
)


def _wrap_360(values: np.ndarray) -> np.ndarray:
    return np.mod(values, 360.0)


def _signed_circular_delta(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    return ((actual - predicted + 180.0) % 360.0) - 180.0


def _angle_from_components(sin_pred: np.ndarray, cos_pred: np.ndarray) -> np.ndarray:
    return _wrap_360(np.degrees(np.arctan2(sin_pred, cos_pred)))


def _arc_contains(actual: np.ndarray, dir_lo: np.ndarray, dir_hi: np.ndarray) -> np.ndarray:
    width = np.mod(dir_hi - dir_lo, 360.0)
    return np.mod(actual - dir_lo, 360.0) <= width


def _directional_columns(frame: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for col in frame.columns:
        if col.startswith("fcst_dir_"):
            cols.append(col)
        elif col.startswith("dir_d") and "_h" in col:
            cols.append(col)
        elif col in DIR_COL_CANDIDATES:
            cols.append(col)
    return cols


def _make_regressor(quantile: float | None = None, random_state: int = 0):
    params = {
        "n_estimators": 40,
        "learning_rate": 0.05,
        "random_state": random_state,
    }
    if lgb is not None:  # pragma: no branch - preferred path
        if quantile is not None:
            return lgb.LGBMRegressor(
                objective="quantile",
                alpha=quantile,
                num_leaves=63,
                min_child_samples=25,
                subsample=0.85,
                subsample_freq=1,
                colsample_bytree=0.85,
                n_jobs=-1,
                verbose=-1,
                **params,
            )
        return lgb.LGBMRegressor(
            objective="regression",
            num_leaves=63,
            min_child_samples=25,
            subsample=0.85,
            subsample_freq=1,
            colsample_bytree=0.85,
            n_jobs=-1,
            verbose=-1,
            **params,
        )

    if quantile is not None:
        return GradientBoostingRegressor(
            loss="quantile",
            alpha=quantile,
            **params,
        )
    return GradientBoostingRegressor(**params)


@dataclass
class FrameEncoder:
    """Build a stable numeric feature matrix from a station-direction frame."""

    feature_columns: list[str] = field(default_factory=list)

    def _augment(self, frame: pd.DataFrame) -> pd.DataFrame:
        work = frame.copy()

        if "time" in work.columns:
            dt = pd.to_datetime(work["time"])
            work["issue_month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
            work["issue_month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
            work["issue_doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
            work["issue_doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)
            work["issue_hour_sin"] = np.sin(2 * np.pi * dt.dt.hour / 24.0)
            work["issue_hour_cos"] = np.cos(2 * np.pi * dt.dt.hour / 24.0)

        for col in _directional_columns(work):
            values = pd.to_numeric(work[col], errors="coerce")
            radians = np.deg2rad(values)
            work[f"{col}__sin"] = np.sin(radians)
            work[f"{col}__cos"] = np.cos(radians)

        if "station" in work.columns:
            work["station"] = work["station"].astype(str)
        if "hour" in work.columns:
            work["hour"] = work["hour"].astype(str)

        drop_cols = set(BASE_DROP_COLS)
        drop_cols.update({"time", "target_time"})
        drop_cols.update({"obs_speed", "speed", "direction"})

        for col in drop_cols:
            if col in work.columns:
                work = work.drop(columns=col)

        categorical = [c for c in ("station", "hour") if c in work.columns]
        if categorical:
            work = pd.get_dummies(work, columns=categorical, dummy_na=False)

        numeric = work.select_dtypes(include=[np.number]).copy()
        numeric = numeric.fillna(0.0)
        return numeric

    def fit(self, frame: pd.DataFrame) -> "FrameEncoder":
        self.feature_columns = list(self._augment(frame).columns)
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        work = self._augment(frame)
        if not self.feature_columns:
            raise RuntimeError("FrameEncoder must be fit before transform")
        return work.reindex(columns=self.feature_columns, fill_value=0.0)

    def fit_transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return self.fit(frame).transform(frame)


@dataclass
class CircularDirectionBundle:
    """Center/width circular direction model with a conformal-style offset."""

    alpha: float = ALPHA
    calibration_days: int = 60
    params: dict | None = None
    encoder: FrameEncoder = field(default_factory=FrameEncoder)
    center_sin_model: object | None = None
    center_cos_model: object | None = None
    width_model: object | None = None
    calibration_offset: float = 0.0
    max_train_rows: int = 12_000
    max_calibration_rows: int = 4_000

    def _fit_split(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        if frame.empty:
            raise ValueError("Cannot fit on an empty frame")
        end = pd.to_datetime(frame["target_time"]).max()
        cal_start = end - pd.Timedelta(days=self.calibration_days)
        fit_frame = frame[pd.to_datetime(frame["target_time"]) < cal_start].copy()
        cal_frame = frame[pd.to_datetime(frame["target_time"]) >= cal_start].copy()
        if len(fit_frame) < 25 or len(cal_frame) < 10:
            return frame.copy(), frame.iloc[0:0].copy()
        return fit_frame, cal_frame

    def _build_width_matrix(
        self,
        base_matrix: pd.DataFrame,
        center_sin: np.ndarray,
        center_cos: np.ndarray,
    ) -> pd.DataFrame:
        extra = pd.DataFrame(
            {
                "center_sin": center_sin,
                "center_cos": center_cos,
                "center_strength": np.sqrt(center_sin**2 + center_cos**2),
            },
            index=base_matrix.index,
        )
        return pd.concat([base_matrix, extra], axis=1)

    def _predict_components(self, base_matrix: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        sin_pred = np.asarray(self.center_sin_model.predict(base_matrix), dtype=float)
        cos_pred = np.asarray(self.center_cos_model.predict(base_matrix), dtype=float)
        center = _angle_from_components(sin_pred, cos_pred)
        return sin_pred, cos_pred, center

    def fit(self, frame: pd.DataFrame) -> "CircularDirectionBundle":
        fit_frame, cal_frame = self._fit_split(frame)
        if len(fit_frame) > self.max_train_rows:
            fit_frame = fit_frame.sample(n=self.max_train_rows, random_state=7).sort_index()
        if len(cal_frame) > self.max_calibration_rows:
            cal_frame = cal_frame.sample(n=self.max_calibration_rows, random_state=13).sort_index()

        base_fit = self.encoder.fit_transform(fit_frame)
        y_fit = fit_frame["target_direction"].to_numpy(dtype=float)

        self.center_sin_model = _make_regressor(random_state=11)
        self.center_cos_model = _make_regressor(random_state=12)
        self.center_sin_model.fit(base_fit, np.sin(np.deg2rad(y_fit)))
        self.center_cos_model.fit(base_fit, np.cos(np.deg2rad(y_fit)))

        sin_fit, cos_fit, center_fit = self._predict_components(base_fit)
        width_fit = _circ_dist(y_fit, center_fit)
        width_matrix_fit = self._build_width_matrix(base_fit, sin_fit, cos_fit)
        self.width_model = _make_regressor(quantile=1.0 - self.alpha, random_state=13)
        self.width_model.fit(width_matrix_fit, width_fit)

        if not cal_frame.empty:
            base_cal = self.encoder.transform(cal_frame)
            y_cal = cal_frame["target_direction"].to_numpy(dtype=float)
            sin_cal, cos_cal, center_cal = self._predict_components(base_cal)
            width_matrix_cal = self._build_width_matrix(base_cal, sin_cal, cos_cal)
            width_cal = np.asarray(self.width_model.predict(width_matrix_cal), dtype=float)
            residual = _circ_dist(y_cal, center_cal) - width_cal
            n = len(residual)
            q_level = min(np.ceil((n + 1) * (1.0 - self.alpha)) / n, 1.0)
            self.calibration_offset = float(np.quantile(residual, q_level))
        else:
            self.calibration_offset = 0.0

        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        base = self.encoder.transform(frame)
        sin_pred, cos_pred, center = self._predict_components(base)
        width_matrix = self._build_width_matrix(base, sin_pred, cos_pred)
        width = np.asarray(self.width_model.predict(width_matrix), dtype=float) + self.calibration_offset
        width = np.clip(width, 0.0, 180.0)

        return pd.DataFrame(
            {
                "dir_05": _wrap_360(center - width),
                "dir_50": _wrap_360(center),
                "dir_95": _wrap_360(center + width),
                "center": center,
                "half_width": width,
            },
            index=frame.index,
        )


@dataclass
class StationDirectionBiasBaseline:
    """Nearest-grid circular baseline with per-station/hour bias correction."""

    source_prefix: str
    alpha: float = ALPHA
    bias_: dict[tuple[str, str], float] = field(default_factory=dict)
    width_: dict[tuple[str, str], float] = field(default_factory=dict)
    global_bias: float = 0.0
    global_width: float = 0.0

    def _source_columns(self, hour: int) -> tuple[str, str]:
        primary = f"{self.source_prefix}_h{hour}"
        fallback = f"{self.source_prefix.replace('fcst_', '')}_h{hour}"
        return primary, fallback

    def fit(self, frame: pd.DataFrame) -> "StationDirectionBiasBaseline":
        if frame.empty:
            raise ValueError("Cannot fit baseline on an empty frame")

        all_raw: list[np.ndarray] = []
        all_delta: list[np.ndarray] = []

        for (station, hour), group in frame.groupby(["station", "hour"]):
            primary, fallback = self._source_columns(int(hour))
            source_col = primary if primary in group.columns else fallback if fallback in group.columns else None
            if source_col is None:
                continue
            raw = pd.to_numeric(group[source_col], errors="coerce").to_numpy(dtype=float)
            target = group["target_direction"].to_numpy(dtype=float)
            valid = np.isfinite(raw) & np.isfinite(target)
            if not valid.any():
                continue
            raw = raw[valid]
            target = target[valid]
            delta = _signed_circular_delta(target, raw)
            bias = float(np.mean(delta))
            center = _wrap_360(raw + bias)
            width = np.quantile(_circ_dist(target, center), 1.0 - self.alpha)
            key = (str(station), str(hour))
            self.bias_[key] = bias
            self.width_[key] = float(width)
            all_raw.append(raw)
            all_delta.append(delta)

        if all_delta:
            merged_delta = np.concatenate(all_delta)
            self.global_bias = float(np.mean(merged_delta))
            self.global_width = float(np.quantile(np.abs(merged_delta), 1.0 - self.alpha))
        else:
            self.global_bias = 0.0
            self.global_width = 0.0
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = []
        for idx, row in frame.iterrows():
            hour = str(int(row["hour"]))
            station = str(row["station"])
            primary, fallback = self._source_columns(int(row["hour"]))
            raw = float(row.get(primary, row.get(fallback, np.nan)))
            bias = self.bias_.get((station, hour), self.global_bias)
            width = self.width_.get((station, hour), self.global_width)
            center = _wrap_360(np.array([raw + bias]))[0] if np.isfinite(raw) else np.nan
            out.append(
                {
                    "dir_05": _wrap_360(np.array([center - width]))[0] if np.isfinite(center) else np.nan,
                    "dir_50": center,
                    "dir_95": _wrap_360(np.array([center + width]))[0] if np.isfinite(center) else np.nan,
                    "center": center,
                    "half_width": width,
                }
            )
        return pd.DataFrame(out, index=frame.index)


def _load_station_meta(region: str) -> pd.DataFrame:
    return _load_station_meta_cached(region).copy()


@lru_cache(maxsize=None)
def _load_station_meta_cached(region: str) -> pd.DataFrame:
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    return meta[meta["region"] == region].copy()


def _build_station_direction_frame(region: str, horizon: int, split: str) -> pd.DataFrame:
    start, end = SPLIT_RANGES[split]
    features = _load_features_cached(region)
    obs = _load_station_obs_cached(region)

    meta = _load_station_meta(region)
    frames: list[pd.DataFrame] = []

    for row in meta.itertuples(index=False):
        station_obs = obs[obs["station"] == row.station][["time", "direction"]].copy()
        if station_obs.empty:
            continue

        grid = features[
            (features["latitude"] == round(float(row.nearest_grid_lat), 2))
            & (features["longitude"] == round(float(row.nearest_grid_lon), 2))
        ].copy()
        if grid.empty:
            continue

        for hour in HOURS:
            sub = grid.copy()
            sub["hour"] = int(hour)
            sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
            merged = sub.merge(
                station_obs.rename(columns={"time": "target_time", "direction": "target_direction"}),
                on="target_time",
                how="inner",
            )
            merged = merged[(merged["target_time"] >= start) & (merged["target_time"] <= end)].copy()
            if merged.empty:
                continue
            merged["station"] = row.station
            merged["station_lat"] = float(row.latitude)
            merged["station_lon"] = float(row.longitude)
            merged["station_height_m"] = float(row.height_m)
            merged["nearest_grid_lat"] = float(row.nearest_grid_lat)
            merged["nearest_grid_lon"] = float(row.nearest_grid_lon)
            merged["region"] = region
            merged["horizon"] = horizon
            merged["split"] = split
            frames.append(merged)

    if not frames:
        raise ValueError(f"No station direction data for {region}/d{horizon}/{split}")

    frame = pd.concat(frames, ignore_index=True)
    frame["target_direction"] = pd.to_numeric(frame["target_direction"], errors="coerce")
    frame = frame.dropna(subset=["target_direction"])
    return frame


def fit_production_models(calibration_days: int = 30) -> dict[tuple[str, int], CircularDirectionBundle]:
    """Fit one Track D bundle per region/horizon on the historical train split."""

    models: dict[tuple[str, int], CircularDirectionBundle] = {}
    for region in REGIONS:
        for horizon in HORIZONS:
            frame = _build_station_direction_frame(region, horizon, "train")
            bundle = CircularDirectionBundle(calibration_days=calibration_days)
            bundle.fit(frame)
            models[(region, horizon)] = bundle
    return models


def _build_station_direction_inference_frame(region: str, horizon: int, window: int) -> pd.DataFrame:
    """Build station-row features for one inference window."""

    features = load_inference_features(window, region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)

    meta = _load_station_meta(region)
    frames: list[pd.DataFrame] = []
    for row in meta.itertuples(index=False):
        grid = features[
            (features["latitude"] == round(float(row.nearest_grid_lat), 2))
            & (features["longitude"] == round(float(row.nearest_grid_lon), 2))
        ].copy()
        if grid.empty:
            continue

        for hour in HOURS:
            sub = grid.copy()
            sub["station"] = row.station
            sub["station_lat"] = float(row.latitude)
            sub["station_lon"] = float(row.longitude)
            sub["station_height_m"] = float(row.height_m)
            sub["nearest_grid_lat"] = float(row.nearest_grid_lat)
            sub["nearest_grid_lon"] = float(row.nearest_grid_lon)
            sub["region"] = region
            sub["horizon"] = int(horizon)
            sub["hour"] = int(hour)
            sub["window"] = int(window)
            frames.append(sub)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def predict_inference_overrides(
    models: dict[tuple[str, int], CircularDirectionBundle],
) -> pd.DataFrame:
    """Predict station-direction overrides for all phase-1 inference windows."""

    rows: list[pd.DataFrame] = []
    for region in REGIONS:
        for horizon in HORIZONS:
            bundle = models[(region, horizon)]
            for window in range(1, 9):
                frame = _build_station_direction_inference_frame(region, horizon, window)
                if frame.empty:
                    continue
                pred = bundle.predict(frame)
                keys = frame[["window", "region", "station", "horizon", "hour"]].reset_index(drop=True)
                rows.append(pd.concat([keys, pred[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True)], axis=1))

    if not rows:
        return pd.DataFrame(columns=["window", "region", "station", "horizon", "hour", "dir_05", "dir_50", "dir_95"])

    out = pd.concat(rows, ignore_index=True)
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    return out


@lru_cache(maxsize=None)
def _load_features_cached(region: str) -> pd.DataFrame:
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    return features


@lru_cache(maxsize=None)
def _load_station_obs_cached(region: str) -> pd.DataFrame:
    obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
    obs["time"] = pd.to_datetime(obs["time"])
    return obs.dropna(subset=["direction"]).copy()


def _source_prefix_for_horizon(horizon: int) -> str:
    return f"fcst_dir_d{horizon}"


def _score_frame(frame: pd.DataFrame, pred: pd.DataFrame) -> dict[str, float]:
    y = frame["target_direction"].to_numpy(dtype=float)
    return {
        "cws": circular_winkler_score(y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float), alpha=ALPHA),
        "mae": float(np.nanmean(_circ_dist(y, pred["dir_50"].to_numpy(dtype=float)))),
        "coverage": float(np.mean(_arc_contains(y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float)))),
        "width": float(np.nanmean(pred["half_width"].to_numpy(dtype=float))),
    }


def evaluate_local(split: str = "val", calibration_days: int = 60) -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for horizon in HORIZONS:
            train_frame = _build_station_direction_frame(region, horizon, "train")
            eval_frame = _build_station_direction_frame(region, horizon, split)

            baseline = StationDirectionBiasBaseline(_source_prefix_for_horizon(horizon))
            baseline.fit(train_frame)
            proto = CircularDirectionBundle(calibration_days=calibration_days)
            proto.fit(train_frame)

            base_pred = baseline.predict(eval_frame)
            proto_pred = proto.predict(eval_frame)
            base_scores = _score_frame(eval_frame, base_pred)
            proto_scores = _score_frame(eval_frame, proto_pred)
            rows.append(
                {
                    "dimension": f"dir_stations_d{horizon}_{'ns' if region == 'north_sea' else 'ecs'}",
                    "baseline_cws": base_scores["cws"],
                    "prototype_cws": proto_scores["cws"],
                    "delta_cws": proto_scores["cws"] - base_scores["cws"],
                    "baseline_mae": base_scores["mae"],
                    "prototype_mae": proto_scores["mae"],
                    "delta_mae": proto_scores["mae"] - base_scores["mae"],
                    "baseline_coverage": base_scores["coverage"],
                    "prototype_coverage": proto_scores["coverage"],
                    "prototype_width": proto_scores["width"],
                }
            )

    table = pd.DataFrame(rows).sort_values("dimension").reset_index(drop=True)
    return table


def summarize_local_results(table: pd.DataFrame) -> str:
    if table.empty:
        return "No validation results produced."

    best_row = table.loc[table["delta_cws"].idxmin()]
    worst_row = table.loc[table["delta_cws"].idxmax()]
    overall_delta = float((table["prototype_cws"] - table["baseline_cws"]).mean())

    lines = [
        "Track D local circular-direction prototype",
        "",
        table[["dimension", "baseline_cws", "prototype_cws", "delta_cws"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"),
        "",
        f"Mean delta across 6 station-direction dims: {overall_delta:+.3f} cWS",
        f"Strongest gain: {best_row['dimension']} ({best_row['delta_cws']:+.3f} cWS)",
        f"Largest regression risk: {worst_row['dimension']} ({worst_row['delta_cws']:+.3f} cWS)",
        f"Best prototype coverage: {table['prototype_coverage'].mean():.3f}",
    ]
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Track D circular direction prototype")
    parser.add_argument("--split", choices=sorted(SPLIT_RANGES), default="val")
    parser.add_argument("--calibration-days", type=int, default=60)
    args = parser.parse_args(list(argv) if argv is not None else None)

    table = evaluate_local(split=args.split, calibration_days=args.calibration_days)
    print(summarize_local_results(table))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
