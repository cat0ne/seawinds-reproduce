from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    GT_GROUPS,
    HORIZONS,
    HOURS,
    PRESSURE_LEVELS,
    PROBLEMS,
    REGION_SHORT,
    REGIONS,
    SURFACE_LEVELS,
    TRAIN_DIR,
)
from src.scoring.winkler import (
    circular_winkler_score,
    winkler_score,
)


def _wind_speed_direction(u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    speed = np.sqrt(u**2 + v**2)
    direction = (270.0 - np.degrees(np.arctan2(v, u))) % 360.0
    return speed, direction


def build_surface_gt(
    region: str,
    data_dir=None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    if data_dir is None:
        data_dir = TRAIN_DIR
    path = data_dir / f"reanalysis_{region}_6h.parquet"
    df = pd.read_parquet(
        path,
        columns=["time", "latitude", "longitude", "u10", "v10", "u100", "v100"],
    )
    df["time"] = pd.to_datetime(df["time"])
    if start_date:
        df = df[df["time"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["time"] <= pd.Timestamp(end_date)]

    df["latitude"] = df["latitude"].round(2)
    df["longitude"] = df["longitude"].round(2)

    rows = []
    for level, u_col, v_col in [("10m", "u10", "v10"), ("100m", "u100", "v100")]:
        sub = df[df[u_col].notna() & df[v_col].notna()].copy()
        speed, direction = _wind_speed_direction(sub[u_col].values, sub[v_col].values)
        sub = sub[["time", "latitude", "longitude"]].copy()
        sub["level"] = level
        sub["speed"] = speed
        sub["direction"] = direction
        rows.append(sub)
    result = pd.concat(rows, ignore_index=True)
    result["region"] = region
    return result


def build_pressure_gt(
    region: str,
    data_dir=None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    if data_dir is None:
        data_dir = TRAIN_DIR
    path = data_dir / f"reanalysis_pressure_{region}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    if start_date:
        df = df[df["time"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["time"] <= pd.Timestamp(end_date)]

    df["latitude"] = df["latitude"].round(2)
    df["longitude"] = df["longitude"].round(2)

    rows = []
    for lev in PRESSURE_LEVELS:
        u_col, v_col = f"u_{lev}", f"v_{lev}"
        if u_col not in df.columns or v_col not in df.columns:
            continue
        sub = df[df[u_col].notna() & df[v_col].notna()].copy()
        speed, direction = _wind_speed_direction(sub[u_col].values, sub[v_col].values)
        sub = sub[["time", "latitude", "longitude"]].copy()
        sub["level"] = str(lev)
        sub["speed"] = speed
        sub["direction"] = direction
        rows.append(sub)
    result = pd.concat(rows, ignore_index=True)
    result["region"] = region
    return result


def build_station_gt(
    region: str,
    data_dir=None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    if data_dir is None:
        data_dir = TRAIN_DIR
    path = data_dir / f"stations_{region}_6h.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    if start_date:
        df = df[df["time"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["time"] <= pd.Timestamp(end_date)]
    df = df.rename(columns={"speed": "speed", "direction": "direction"})
    df["region"] = region
    return df[["time", "station", "region", "speed", "direction"]].copy()


def _match_predictions_to_gt(
    preds: pd.DataFrame,
    gt: pd.DataFrame,
    match_cols: list[str],
) -> pd.DataFrame:
    return preds.merge(
        gt[match_cols + ["speed", "direction"]],
        on=match_cols,
        how="inner",
    )


def _resolve_target_time(preds: pd.DataFrame) -> pd.DataFrame:
    preds = preds.copy()
    init = pd.to_datetime(preds["time"])
    horizon = preds["horizon"].astype(int)
    hour = preds["hour"].astype(int)
    preds["_target_time"] = init.dt.normalize() + pd.to_timedelta(horizon, unit="D") + pd.to_timedelta(hour, unit="h")
    preds["_target_date"] = preds["_target_time"].dt.date
    return preds


def evaluate_predictions(
    preds: pd.DataFrame,
    gt_surface: dict[str, pd.DataFrame] | None = None,
    gt_pressure: dict[str, pd.DataFrame] | None = None,
    gt_stations: dict[str, pd.DataFrame] | None = None,
    data_dir=None,
) -> pd.DataFrame:
    if data_dir is None:
        from src.data.paths import TRAIN_DIR as data_dir

    if gt_surface is None:
        gt_surface = {}
    if gt_pressure is None:
        gt_pressure = {}
    if gt_stations is None:
        gt_stations = {}

    preds = _resolve_target_time(preds)

    scores = {}

    for region in REGIONS:
        rshort = REGION_SHORT[region]

        if region not in gt_surface:
            gt_surface[region] = build_surface_gt(region, data_dir)
        if region not in gt_pressure:
            gt_pressure[region] = build_pressure_gt(region, data_dir)
        if region not in gt_stations:
            gt_stations[region] = build_station_gt(region, data_dir)

        for h in HORIZONS:
            for gt_group in GT_GROUPS:
                for problem in PROBLEMS:
                    dim_key = f"{problem}_{gt_group}_d{h}_{rshort}"
                    try:
                        score = _score_dimension(
                            preds, region, h, gt_group, problem,
                            gt_surface[region], gt_pressure[region],
                            gt_stations[region],
                        )
                        scores[dim_key] = score
                    except Exception as e:
                        scores[dim_key] = float("nan")

    result = pd.DataFrame([
        {"dimension": k, "score": v} for k, v in sorted(scores.items())
    ])
    return result


def _score_dimension(
    preds: pd.DataFrame,
    region: str,
    horizon: int,
    gt_group: str,
    problem: str,
    gt_surface: pd.DataFrame,
    gt_pressure: pd.DataFrame,
    gt_stations: pd.DataFrame,
) -> float:
    pred_region = preds[
        (preds["region"] == region) & (preds["horizon"] == horizon)
    ].copy()

    if gt_group == "stations":
        return _score_station_dim(pred_region, problem, gt_stations)
    elif gt_group == "surface":
        return _score_grid_dim(pred_region, problem, gt_surface, SURFACE_LEVELS)
    elif gt_group == "pressure":
        return _score_grid_dim(pred_region, problem, gt_pressure, PRESSURE_LEVELS)
    else:
        raise ValueError(f"Unknown gt_group: {gt_group}")


def _score_station_dim(
    pred_region: pd.DataFrame,
    problem: str,
    gt_stations: pd.DataFrame,
) -> float:
    gt = gt_stations.copy()
    gt["_target_date"] = gt["time"].dt.date
    gt["_target_hour"] = gt["time"].dt.hour

    pred_stations = pred_region[pred_region["type"] == "station"].copy()
    if pred_stations.empty:
        return float("nan")

    pred_stations["_target_date"] = pred_stations["_target_time"].dt.date
    pred_stations["_target_hour"] = pred_stations["_target_time"].dt.hour.astype(int)

    merged = pred_stations.merge(
        gt[["station", "_target_date", "_target_hour", "speed", "direction"]],
        on=["station", "_target_date", "_target_hour"],
        how="inner",
    )
    if merged.empty:
        return float("nan")

    if problem == "speed":
        actual = merged["speed"].values
        q_lo = merged["q05"].values
        q_hi = merged["q95"].values
        valid = actual > 0
        return winkler_score(actual[valid], q_lo[valid], q_hi[valid])
    else:
        actual = merged["direction"].values
        dir_lo = merged["dir_05"].values
        dir_hi = merged["dir_95"].values
        valid = np.isfinite(actual)
        return circular_winkler_score(actual[valid], dir_lo[valid], dir_hi[valid])


def _score_grid_dim(
    pred_region: pd.DataFrame,
    problem: str,
    gt_grid: pd.DataFrame,
    levels: list[str],
) -> float:
    gt = gt_grid.copy()
    gt["_target_date"] = gt["time"].dt.date
    gt["_target_hour"] = gt["time"].dt.hour

    pred_grid = pred_region[
        (pred_region["type"] == "grid") & (pred_region["level"].isin(levels))
    ].copy()
    if pred_grid.empty:
        return float("nan")

    pred_grid["latitude"] = pred_grid["latitude"].astype(float).round(2)
    pred_grid["longitude"] = pred_grid["longitude"].astype(float).round(2)
    pred_grid["_target_date"] = pred_grid["_target_time"].dt.date
    pred_grid["_target_hour"] = pred_grid["_target_time"].dt.hour.astype(int)

    merged = pred_grid.merge(
        gt[["latitude", "longitude", "level", "_target_date", "_target_hour", "speed", "direction"]],
        on=["latitude", "longitude", "level", "_target_date", "_target_hour"],
        how="inner",
    )
    if merged.empty:
        return float("nan")

    if problem == "speed":
        actual = merged["speed"].values
        q_lo = merged["q05"].values
        q_hi = merged["q95"].values
        valid = actual > 0
        return winkler_score(actual[valid], q_lo[valid], q_hi[valid])
    else:
        actual = merged["direction"].values
        dir_lo = merged["dir_05"].values
        dir_hi = merged["dir_95"].values
        valid = np.isfinite(actual)
        return circular_winkler_score(actual[valid], dir_lo[valid], dir_hi[valid])
