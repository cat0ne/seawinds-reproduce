"""Track I: v38-anchored station-direction residual models.

This is the first implementation lane from the direction moat plan. It learns
station-direction residuals around a production-style baseline direction and
keeps the output narrow: station direction rows only, with optional filtering
to specific region/horizon cells before a submission is built.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

try:  # pragma: no cover - optional dependency in minimal environments
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

from sklearn.ensemble import GradientBoostingRegressor

from src.data.paths import ALPHA, HORIZONS, LOGS_DIR, REGIONS
from src.experiments.direction_error_atlas import (
    SPLIT_RANGES,
    apply_base_widths,
    arc_contains,
    build_inference_station_frame,
    build_station_direction_frame,
    calibrate_base_widths,
    signed_circular_delta,
    wrap_360,
)
from src.scoring.winkler import _circ_dist, circular_winkler_score


Q_LEVEL = 1.0 - ALPHA
MODEL_DIR = LOGS_DIR / "track_i_v38_residual_direction"
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
KEY_COLS = ["window", "region", "station", "horizon", "hour"]


def _make_regressor(quantile: float | None = None, random_state: int = 0):
    params = {
        "n_estimators": 60,
        "learning_rate": 0.04,
        "random_state": random_state,
    }
    if lgb is not None:
        if quantile is not None:
            return lgb.LGBMRegressor(
                objective="quantile",
                alpha=quantile,
                num_leaves=31,
                min_child_samples=15,
                subsample=0.9,
                subsample_freq=1,
                colsample_bytree=0.9,
                n_jobs=-1,
                verbose=-1,
                **params,
            )
        return lgb.LGBMRegressor(
            objective="regression",
            num_leaves=31,
            min_child_samples=15,
            subsample=0.9,
            subsample_freq=1,
            colsample_bytree=0.9,
            n_jobs=-1,
            verbose=-1,
            **params,
        )
    if quantile is not None:
        return GradientBoostingRegressor(loss="quantile", alpha=quantile, **params)
    return GradientBoostingRegressor(**params)


@dataclass
class ResidualFrameEncoder:
    feature_columns: list[str] = field(default_factory=list)

    def _augment(self, frame: pd.DataFrame) -> pd.DataFrame:
        work = frame.copy()

        if "time" in work.columns:
            dt = pd.to_datetime(work["time"])
            work["issue_month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
            work["issue_month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
            work["issue_doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
            work["issue_doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)

        for col in [
            "base_direction",
            "wd10",
            "wd100",
            "wd10_h6",
            "wd10_h18",
            "wd10_lag1d",
            "wd10_lag3d",
            "wd10_lag7d",
        ]:
            if col in work.columns:
                radians = np.deg2rad(pd.to_numeric(work[col], errors="coerce"))
                work[f"{col}__sin"] = np.sin(radians)
                work[f"{col}__cos"] = np.cos(radians)

        if "hour" in work.columns:
            radians = 2 * np.pi * pd.to_numeric(work["hour"], errors="coerce") / 24.0
            work["target_hour_sin"] = np.sin(radians)
            work["target_hour_cos"] = np.cos(radians)
        if "station" in work.columns:
            work["station"] = work["station"].astype(str)

        drop_cols = {
            "time",
            "target_time",
            "target_direction",
            "signed_residual",
            "abs_residual",
            "base_error",
            "base_dir_05",
            "base_dir_95",
            "base_hit",
            "base_cws_sample",
            "source_direction_col",
            "source_speed_col",
            "split",
            "region",
            "window",
        }
        for col in drop_cols:
            if col in work.columns:
                work = work.drop(columns=col)

        if "station" in work.columns:
            work = pd.get_dummies(work, columns=["station"], dummy_na=False)

        numeric = work.select_dtypes(include=[np.number]).copy()
        return numeric.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    def fit(self, frame: pd.DataFrame) -> "ResidualFrameEncoder":
        self.feature_columns = list(self._augment(frame).columns)
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not self.feature_columns:
            raise RuntimeError("ResidualFrameEncoder must be fit before transform")
        return self._augment(frame).reindex(columns=self.feature_columns, fill_value=0.0)

    def fit_transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return self.fit(frame).transform(frame)


@dataclass
class V38ResidualDirectionModel:
    encoder: ResidualFrameEncoder = field(default_factory=ResidualFrameEncoder)
    residual_sin_model: object | None = None
    residual_cos_model: object | None = None
    width_model: object | None = None
    calibration_offset: float = 0.0
    base_widths: dict[tuple[str, int], float] = field(default_factory=dict)

    def fit(self, train_frame: pd.DataFrame) -> "V38ResidualDirectionModel":
        if train_frame.empty:
            raise ValueError("Cannot fit residual direction model on empty frame")

        self.base_widths = calibrate_base_widths(train_frame)
        x = self.encoder.fit_transform(train_frame)
        residual = train_frame["signed_residual"].to_numpy(dtype=float)

        self.residual_sin_model = _make_regressor(random_state=101)
        self.residual_cos_model = _make_regressor(random_state=102)
        self.residual_sin_model.fit(x, np.sin(np.deg2rad(residual)))
        self.residual_cos_model.fit(x, np.cos(np.deg2rad(residual)))

        center = self.predict_center(train_frame)
        y = train_frame["target_direction"].to_numpy(dtype=float)
        corrected_error = _circ_dist(y, center)
        width_x = self._width_matrix(x, center)
        self.width_model = _make_regressor(quantile=Q_LEVEL, random_state=103)
        self.width_model.fit(width_x, corrected_error)

        raw_width = np.asarray(self.width_model.predict(width_x), dtype=float)
        residual_width = corrected_error - raw_width
        n = len(residual_width)
        q_level = min(np.ceil((n + 1) * Q_LEVEL) / n, 1.0)
        self.calibration_offset = float(np.nanquantile(residual_width, q_level))
        return self

    def _width_matrix(self, x: pd.DataFrame, center: np.ndarray) -> pd.DataFrame:
        extra = pd.DataFrame(
            {
                "pred_center_sin": np.sin(np.deg2rad(center)),
                "pred_center_cos": np.cos(np.deg2rad(center)),
            },
            index=x.index,
        )
        return pd.concat([x, extra], axis=1)

    def predict_center(self, frame: pd.DataFrame) -> np.ndarray:
        x = self.encoder.transform(frame)
        sin_pred = np.asarray(self.residual_sin_model.predict(x), dtype=float)
        cos_pred = np.asarray(self.residual_cos_model.predict(x), dtype=float)
        residual = np.degrees(np.arctan2(sin_pred, cos_pred))
        return wrap_360(frame["base_direction"].to_numpy(dtype=float) + residual)

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        x = self.encoder.transform(frame)
        center = self.predict_center(frame)
        width = np.asarray(self.width_model.predict(self._width_matrix(x, center)), dtype=float)
        width = np.clip(width + self.calibration_offset, 0.0, 180.0)
        return pd.DataFrame(
            {
                "dir_05": wrap_360(center - width),
                "dir_50": center,
                "dir_95": wrap_360(center + width),
                "center": center,
                "half_width": width,
            },
            index=frame.index,
        )


def _score_prediction(frame: pd.DataFrame, pred: pd.DataFrame) -> dict[str, float]:
    y = frame["target_direction"].to_numpy(dtype=float)
    center = pred["dir_50"].to_numpy(dtype=float)
    return {
        "cws": circular_winkler_score(y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float)),
        "mae": float(np.nanmean(_circ_dist(y, center))),
        "coverage": float(np.nanmean(arc_contains(y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float)))),
        "width": float(np.nanmean(pred["half_width"])),
    }


def _baseline_prediction(frame: pd.DataFrame, widths: dict[tuple[str, int], float]) -> pd.DataFrame:
    base = apply_base_widths(frame, widths)
    return pd.DataFrame(
        {
            "dir_05": base["base_dir_05"].to_numpy(dtype=float),
            "dir_50": base["base_direction"].to_numpy(dtype=float),
            "dir_95": base["base_dir_95"].to_numpy(dtype=float),
            "center": base["base_direction"].to_numpy(dtype=float),
            "half_width": base["base_width"].to_numpy(dtype=float),
        },
        index=frame.index,
    )


def fit_models() -> dict[tuple[str, int], V38ResidualDirectionModel]:
    models: dict[tuple[str, int], V38ResidualDirectionModel] = {}
    for region in REGIONS:
        for horizon in HORIZONS:
            train = build_station_direction_frame(region, horizon, "train")
            if train.empty:
                continue
            model = V38ResidualDirectionModel()
            model.fit(train)
            models[(region, horizon)] = model
    return models


def evaluate_local(splits: tuple[str, ...] = ("val", "tune", "holdout")) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    models = fit_models()
    for region in REGIONS:
        suffix = "ns" if region == "north_sea" else "ecs"
        for horizon in HORIZONS:
            model = models.get((region, horizon))
            if model is None:
                continue
            for split in splits:
                frame = build_station_direction_frame(region, horizon, split)
                if frame.empty:
                    continue
                base_pred = _baseline_prediction(frame, model.base_widths)
                cand_pred = model.predict(frame)
                base = _score_prediction(frame, base_pred)
                cand = _score_prediction(frame, cand_pred)
                rows.append(
                    {
                        "dimension": f"dir_stations_d{horizon}_{suffix}",
                        "region": region,
                        "horizon": horizon,
                        "split": split,
                        "rows": len(frame),
                        "baseline_cws": base["cws"],
                        "candidate_cws": cand["cws"],
                        "delta_cws": cand["cws"] - base["cws"],
                        "baseline_mae": base["mae"],
                        "candidate_mae": cand["mae"],
                        "delta_mae": cand["mae"] - base["mae"],
                        "candidate_coverage": cand["coverage"],
                        "candidate_width": cand["width"],
                    }
                )
    return pd.DataFrame(rows)


def predict_inference_overrides(
    models: dict[tuple[str, int], V38ResidualDirectionModel],
    targets: set[tuple[str, int]] | None = None,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for (region, horizon), model in models.items():
        if targets is not None and (region, horizon) not in targets:
            continue
        for window in range(1, 9):
            frame = build_inference_station_frame(region, horizon, window)
            if frame.empty:
                continue
            pred = model.predict(frame)
            keys = frame[KEY_COLS].reset_index(drop=True)
            rows.append(pd.concat([keys, pred[DIR_COLS].reset_index(drop=True)], axis=1))
    if not rows:
        return pd.DataFrame(columns=KEY_COLS + DIR_COLS)
    out = pd.concat(rows, ignore_index=True)
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    return out


def write_report() -> tuple[Path, pd.DataFrame]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    table = evaluate_local()
    path = MODEL_DIR / "local_station_direction_residual_eval.csv"
    table.to_csv(path, index=False)
    return path, table


def main() -> int:
    path, table = write_report()
    print(f"Wrote local evaluation: {path}")
    if table.empty:
        print("No results.")
    else:
        print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
