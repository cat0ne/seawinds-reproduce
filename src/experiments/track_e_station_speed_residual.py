"""Track E: station-speed residual distribution model.

This track tests a stricter version of the station-speed idea: model only the
station residual around the nearest-grid forecast, then add quantile residuals
back to the forecast center. It avoids the Track A joint speed/direction
coupling and reports historical split deltas before any submission wiring.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data.paths import HOURS, HORIZONS, REGIONS, SCORING_DIR, TRAIN_END
from src.io.dataset import load_features, load_inference_features, load_stations
from src.models.quantile_gbm import QuantileGBM
from src.scoring.winkler import winkler_score
from src.validate import get_split_dates


CALIBRATION_START = pd.Timestamp("2020-07-01")


@dataclass
class StationSpeedResidualModel:
    region: str
    horizon: int
    feature_cols: list[str]
    encoded_cols: list[str]
    model: QuantileGBM
    baseline_width: float


def _station_meta() -> pd.DataFrame:
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    meta["nearest_grid_lat"] = meta["nearest_grid_lat"].astype(float).round(2)
    meta["nearest_grid_lon"] = meta["nearest_grid_lon"].astype(float).round(2)
    return meta


def _forecast_speed(frame: pd.DataFrame, horizon: int) -> np.ndarray:
    values = np.full(len(frame), np.nan, dtype=float)
    source_horizon = 10 if horizon == 14 else horizon
    for hour in HOURS:
        mask = frame["hour"].astype(int).eq(int(hour)).to_numpy()
        use_col = f"fcst_speed_d{source_horizon}_h{hour}"
        if use_col in frame.columns:
            values[mask] = pd.to_numeric(frame.loc[mask, use_col], errors="coerce").to_numpy(dtype=float)
    return values


def _build_rows(region: str, horizon: int) -> pd.DataFrame:
    features = load_features(region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)

    stations = load_stations(region).dropna(subset=["speed"]).copy()
    stations["time"] = pd.to_datetime(stations["time"])
    meta = _station_meta()
    meta = meta[meta["region"].eq(region)].copy()

    frames: list[pd.DataFrame] = []
    for row in meta.itertuples(index=False):
        grid = features[
            (features["latitude"] == row.nearest_grid_lat)
            & (features["longitude"] == row.nearest_grid_lon)
        ].copy()
        obs = stations[stations["station"].eq(row.station)][["time", "speed"]].copy()
        if grid.empty or obs.empty:
            continue
        for hour in HOURS:
            sub = grid.copy()
            sub["hour"] = int(hour)
            sub["horizon"] = int(horizon)
            sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
            merged = sub.merge(
                obs.rename(columns={"time": "target_time", "speed": "obs_speed"}),
                on="target_time",
                how="inner",
            )
            if merged.empty:
                continue
            merged["station"] = row.station
            merged["height_m"] = float(row.height_m)
            merged["station_lat"] = float(row.latitude)
            merged["station_lon"] = float(row.longitude)
            merged["nearest_grid_lat"] = float(row.nearest_grid_lat)
            merged["nearest_grid_lon"] = float(row.nearest_grid_lon)
            frames.append(merged)

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["forecast_speed"] = _forecast_speed(out, horizon)
    out["residual"] = out["obs_speed"] - out["forecast_speed"]
    dt = pd.to_datetime(out["time"])
    out["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
    out["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"].astype(float) / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"].astype(float) / 24.0)
    out["log_height_m"] = np.log(out["height_m"].clip(lower=0.1))
    return out.dropna(subset=["forecast_speed", "residual"])


def _feature_cols(frame: pd.DataFrame) -> list[str]:
    exclude = {
        "time",
        "target_time",
        "obs_speed",
        "residual",
        "speed",
        "direction",
    }
    exclude |= {c for c in frame.columns if c.startswith(("speed_d", "dir_d")) and "_h" in c}
    keep = [c for c in frame.columns if c not in exclude]
    return sorted(keep)


def _encode(frame: pd.DataFrame, feature_cols: list[str], ref_cols: list[str] | None = None) -> pd.DataFrame:
    work = frame.reindex(columns=feature_cols).copy()
    categorical = [c for c in work.columns if work[c].dtype == "object"]
    if categorical:
        work = pd.get_dummies(work, columns=categorical, dummy_na=False)
    for col in work.columns:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)
    if ref_cols is not None:
        for col in ref_cols:
            if col not in work.columns:
                work[col] = 0.0
        work = work[ref_cols]
    return work.astype(np.float32)


def _split(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    if split == "train":
        return frame[pd.to_datetime(frame["target_time"]) <= pd.Timestamp(TRAIN_END)].copy()
    start, end = get_split_dates(split)
    t = pd.to_datetime(frame["target_time"])
    return frame[t.between(pd.Timestamp(start), pd.Timestamp(end))].copy()


def fit_model(region: str, horizon: int) -> tuple[StationSpeedResidualModel, pd.DataFrame]:
    rows = _build_rows(region, horizon)
    train = _split(rows, "train")
    fit = train[pd.to_datetime(train["target_time"]) < CALIBRATION_START].copy()
    cal = train[pd.to_datetime(train["target_time"]) >= CALIBRATION_START].copy()
    if fit.empty:
        fit = train
        cal = train.iloc[0:0].copy()

    feature_cols = _feature_cols(fit)
    X_fit = _encode(fit, feature_cols)
    X_cal = _encode(cal, feature_cols, list(X_fit.columns)) if not cal.empty else None
    y_fit = fit["residual"].to_numpy(dtype=float)
    y_cal = cal["residual"].to_numpy(dtype=float) if not cal.empty else None
    model = QuantileGBM(
        params={
            "n_estimators": 180,
            "learning_rate": 0.04,
            "num_leaves": 31,
            "min_child_samples": 25,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "verbose": -1,
            "n_jobs": -1,
        }
    )
    model.fit(X_fit, y_fit, X_cal, y_cal)

    baseline_width = float(np.nanquantile(np.abs(train["residual"].to_numpy(dtype=float)), 0.90))
    return (
        StationSpeedResidualModel(region, horizon, feature_cols, list(X_fit.columns), model, baseline_width),
        rows,
    )


def fit_production_models() -> dict[tuple[str, int], StationSpeedResidualModel]:
    """Fit Track E models for all region/horizon station-speed cells."""

    models: dict[tuple[str, int], StationSpeedResidualModel] = {}
    for region in REGIONS:
        for horizon in HORIZONS:
            model, _ = fit_model(region, horizon)
            models[(region, horizon)] = model
    return models


def _build_inference_rows(region: str, horizon: int, window: int) -> pd.DataFrame:
    features = load_inference_features(window, region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    meta = _station_meta()
    meta = meta[meta["region"].eq(region)].copy()

    frames: list[pd.DataFrame] = []
    for row in meta.itertuples(index=False):
        grid = features[
            (features["latitude"] == row.nearest_grid_lat)
            & (features["longitude"] == row.nearest_grid_lon)
        ].copy()
        if grid.empty:
            continue
        for hour in HOURS:
            sub = grid.copy()
            sub["window"] = int(window)
            sub["region"] = region
            sub["station"] = row.station
            sub["hour"] = int(hour)
            sub["horizon"] = int(horizon)
            sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
            sub["height_m"] = float(row.height_m)
            sub["station_lat"] = float(row.latitude)
            sub["station_lon"] = float(row.longitude)
            sub["nearest_grid_lat"] = float(row.nearest_grid_lat)
            sub["nearest_grid_lon"] = float(row.nearest_grid_lon)
            frames.append(sub)

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["forecast_speed"] = _forecast_speed(out, horizon)
    dt = pd.to_datetime(out["time"])
    out["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0)
    out["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0)
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"].astype(float) / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"].astype(float) / 24.0)
    out["log_height_m"] = np.log(out["height_m"].clip(lower=0.1))
    return out.dropna(subset=["forecast_speed"])


def predict_inference_overrides(
    models: dict[tuple[str, int], StationSpeedResidualModel],
) -> pd.DataFrame:
    """Predict station speed overrides for all inference windows."""

    rows: list[pd.DataFrame] = []
    for region in REGIONS:
        for horizon in HORIZONS:
            fitted = models[(region, horizon)]
            for window in range(1, 9):
                frame = _build_inference_rows(region, horizon, window)
                if frame.empty:
                    continue
                X = _encode(frame, fitted.feature_cols, fitted.encoded_cols)
                r05, r50, r95 = fitted.model.predict(X)
                center = frame["forecast_speed"].to_numpy(dtype=float)
                pred = pd.DataFrame(
                    {
                        "q05": np.clip(center + r05, 0.0, None),
                        "q50": np.clip(center + r50, 0.0, None),
                        "q95": np.clip(center + r95, 0.0, None),
                    }
                )
                pred = pd.DataFrame(np.sort(pred[["q05", "q50", "q95"]].to_numpy(), axis=1), columns=["q05", "q50", "q95"])
                keys = frame[["window", "region", "station", "horizon", "hour"]].reset_index(drop=True)
                rows.append(pd.concat([keys, pred.reset_index(drop=True)], axis=1))

    if not rows:
        return pd.DataFrame(columns=["window", "region", "station", "horizon", "hour", "q05", "q50", "q95"])
    out = pd.concat(rows, ignore_index=True)
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    return out


def evaluate_local(split: str = "val") -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for region in REGIONS:
        suffix = "ns" if region == "north_sea" else "ecs"
        for horizon in HORIZONS:
            fitted, all_rows = fit_model(region, horizon)
            eval_rows = _split(all_rows, split)
            if eval_rows.empty:
                continue
            X = _encode(eval_rows, fitted.feature_cols, fitted.encoded_cols)
            r05, _, r95 = fitted.model.predict(X)
            center = eval_rows["forecast_speed"].to_numpy(dtype=float)
            y = eval_rows["obs_speed"].to_numpy(dtype=float)
            base_q05 = np.clip(center - fitted.baseline_width, 0.0, None)
            base_q95 = np.clip(center + fitted.baseline_width, 0.0, None)
            cand_q05 = np.clip(center + r05, 0.0, None)
            cand_q95 = np.clip(center + r95, 0.0, None)
            base_score = winkler_score(y, base_q05, base_q95)
            cand_score = winkler_score(y, cand_q05, cand_q95)
            rows.append(
                {
                    "dimension": f"speed_stations_d{horizon}_{suffix}",
                    "baseline": base_score,
                    "track_e": cand_score,
                    "delta": cand_score - base_score,
                }
            )
    return pd.DataFrame(rows).sort_values("dimension").reset_index(drop=True)


def main() -> int:
    for split in ("val", "tune", "holdout"):
        table = evaluate_local(split=split)
        print("\n" + "=" * 80)
        print(f"Track E station-speed residual distribution | split={split}")
        print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        if not table.empty:
            print(f"Mean delta: {table['delta'].mean():+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
