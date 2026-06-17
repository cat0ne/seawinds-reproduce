"""Track I d7 NS: regularized residual direction model with gate analysis.

Rebuilds the station-direction atlas for north_sea horizon=7 using the
feature-column baseline, trains a strongly-regularized Track I residual model,
and evaluates gated vs ungated performance on val/tune/holdout splits.

If the conservative gate (center_shift <= 15°) shows stable improvements,
this feeds into a submission builder that applies the gated correction to
v88's actual baseline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

try:  # pragma: no cover
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

from sklearn.ensemble import GradientBoostingRegressor

from src.data.paths import ALPHA, LOGS_DIR
from src.experiments.direction_error_atlas import (
    SPLIT_RANGES,
    arc_contains,
    build_inference_station_frame,
    build_station_direction_frame,
    calibrate_base_widths,
    signed_circular_delta,
    wrap_360,
)
from src.scoring.winkler import _circ_dist, circular_winkler_per_sample, circular_winkler_score

Q_LEVEL = 1.0 - ALPHA
MODEL_DIR = LOGS_DIR / "track_i_d7_ns_v88"
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
KEY_COLS = ["window", "region", "station", "horizon", "hour"]


def _make_regressor(quantile: float | None = None, random_state: int = 0):
    params = {
        "n_estimators": 40,
        "learning_rate": 0.03,
        "random_state": random_state,
    }
    if lgb is not None:
        if quantile is not None:
            return lgb.LGBMRegressor(
                objective="quantile",
                alpha=quantile,
                num_leaves=31,
                min_child_samples=20,
                subsample=0.8,
                subsample_freq=1,
                colsample_bytree=0.8,
                n_jobs=-1,
                verbose=-1,
                **params,
            )
        return lgb.LGBMRegressor(
            objective="regression",
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
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
        "cws": circular_winkler_score(
            y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float)
        ),
        "mae": float(np.nanmean(_circ_dist(y, center))),
        "coverage": float(
            np.nanmean(arc_contains(y, pred["dir_05"].to_numpy(dtype=float), pred["dir_95"].to_numpy(dtype=float)))
        ),
        "width": float(np.nanmean(pred["half_width"])),
    }


def _baseline_prediction(frame: pd.DataFrame, widths: dict[tuple[str, int], float]) -> pd.DataFrame:
    from src.experiments.direction_error_atlas import apply_base_widths

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


def evaluate_with_gates(
    model: V38ResidualDirectionModel,
    frame: pd.DataFrame,
    gate_thresholds: tuple[float, ...] = (float("inf"), 20.0, 15.0, 10.0, 5.0),
) -> list[dict[str, float | str]]:
    """Evaluate candidate predictions with various gate thresholds."""
    if frame.empty:
        return []

    base_pred = _baseline_prediction(frame, model.base_widths)
    cand_pred = model.predict(frame)

    base_scores = _score_prediction(frame, base_pred)
    cand_scores = _score_prediction(frame, cand_pred)

    y = frame["target_direction"].to_numpy(dtype=float)
    center_shift = _circ_dist(cand_pred["center"].to_numpy(dtype=float), base_pred["center"].to_numpy(dtype=float))

    results = []
    # Ungated
    results.append(
        {
            "gate": "ungated",
            "threshold": float("inf"),
            "rows": len(frame),
            "accepted": len(frame),
            "rejected": 0,
            "base_cws": base_scores["cws"],
            "cand_cws": cand_scores["cws"],
            "delta_cws": cand_scores["cws"] - base_scores["cws"],
            "base_mae": base_scores["mae"],
            "cand_mae": cand_scores["mae"],
            "delta_mae": cand_scores["mae"] - base_scores["mae"],
            "cand_coverage": cand_scores["coverage"],
            "cand_width": cand_scores["width"],
            "mean_shift": float(np.nanmean(center_shift)),
            "max_shift": float(np.nanmax(center_shift)),
        }
    )

    for thresh in gate_thresholds:
        if thresh == float("inf"):
            continue
        mask = center_shift <= thresh
        accepted = mask.sum()
        rejected = len(frame) - accepted

        if accepted == 0:
            # All rejected: scores = baseline
            results.append(
                {
                    "gate": f"<={thresh}",
                    "threshold": thresh,
                    "rows": len(frame),
                    "accepted": 0,
                    "rejected": rejected,
                    "base_cws": base_scores["cws"],
                    "cand_cws": base_scores["cws"],
                    "delta_cws": 0.0,
                    "base_mae": base_scores["mae"],
                    "cand_mae": base_scores["mae"],
                    "delta_mae": 0.0,
                    "cand_coverage": base_scores["coverage"],
                    "cand_width": base_scores["width"],
                    "mean_shift": float(np.nanmean(center_shift)),
                    "max_shift": float(np.nanmax(center_shift)),
                }
            )
            continue

        # Blend: accepted rows from candidate, rejected from baseline
        blend = base_pred.copy()
        blend.loc[mask, :] = cand_pred.loc[mask, :]
        blend_scores = _score_prediction(frame, blend)

        results.append(
            {
                "gate": f"<={thresh}",
                "threshold": thresh,
                "rows": len(frame),
                "accepted": int(accepted),
                "rejected": int(rejected),
                "base_cws": base_scores["cws"],
                "cand_cws": blend_scores["cws"],
                "delta_cws": blend_scores["cws"] - base_scores["cws"],
                "base_mae": base_scores["mae"],
                "cand_mae": blend_scores["mae"],
                "delta_mae": blend_scores["mae"] - base_scores["mae"],
                "cand_coverage": blend_scores["coverage"],
                "cand_width": blend_scores["width"],
                "mean_shift": float(np.nanmean(center_shift)),
                "max_shift": float(np.nanmax(center_shift)),
            }
        )

    return results


def run_evaluation() -> pd.DataFrame:
    region = "north_sea"
    horizon = 7

    print(f"Building station direction frame for {region} horizon={horizon} ...")
    train = build_station_direction_frame(region, horizon, "train")
    print(f"  train rows: {len(train)}")

    if train.empty:
        raise ValueError("Training frame is empty")

    print("Fitting regularized Track I model ...")
    model = V38ResidualDirectionModel()
    model.fit(train)

    rows = []
    for split in ("val", "tune", "holdout"):
        frame = build_station_direction_frame(region, horizon, split)
        print(f"  {split} rows: {len(frame)}")
        if frame.empty:
            continue
        for result in evaluate_with_gates(model, frame):
            result["region"] = region
            result["horizon"] = horizon
            result["split"] = split
            rows.append(result)

    return pd.DataFrame(rows)


def save_model(model: V38ResidualDirectionModel, path: Path) -> None:
    import pickle
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved model: {path}")


def load_model(path: Path) -> V38ResidualDirectionModel:
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    table = run_evaluation()
    path = MODEL_DIR / "d7_ns_v88_eval.csv"
    table.to_csv(path, index=False)
    print(f"\nWrote evaluation: {path}")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Save a summary for quick inspection
    summary = table[["split", "gate", "accepted", "rejected", "base_cws", "cand_cws", "delta_cws", "cand_coverage"]]
    print("\nSummary:")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Save model for inference
    region = "north_sea"
    horizon = 7
    train = build_station_direction_frame(region, horizon, "train")
    model = V38ResidualDirectionModel()
    model.fit(train)
    save_model(model, MODEL_DIR / "d7_ns_model.pkl")

    # Save metadata
    meta = {
        "region": region,
        "horizon": horizon,
        "model_params": {
            "n_estimators": 40,
            "learning_rate": 0.03,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_samples": 20,
        },
        "eval_path": str(path),
    }
    with open(MODEL_DIR / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
