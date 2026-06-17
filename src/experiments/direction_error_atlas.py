"""Direction error atlas for v38-era residual modelling.

The direction moat plan starts by measuring direction errors relative to the
current production-style baseline, not relative to a raw HRES-only forecast.
For station rows, the closest historical proxy available in the feature matrix
is the starter-kit direction column for the target horizon/hour. This module
builds split-aware station-direction residual tables around that proxy so that
candidate residual models can be trained, audited, and compared consistently.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    HOLDOUT_END,
    HOLDOUT_START,
    HOURS,
    HORIZONS,
    LOGS_DIR,
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
from src.scoring.winkler import _circ_dist, circular_winkler_per_sample, circular_winkler_score


SPLIT_RANGES = {
    "train": (pd.Timestamp(TRAIN_START), pd.Timestamp(TRAIN_END)),
    "val": (pd.Timestamp(VAL_START), pd.Timestamp(VAL_END)),
    "tune": (pd.Timestamp(TUNE_START), pd.Timestamp(TUNE_END)),
    "holdout": (pd.Timestamp(HOLDOUT_START), pd.Timestamp(HOLDOUT_END)),
}

ATLAS_DIR = LOGS_DIR / "direction_error_atlas"


def wrap_360(values: np.ndarray | pd.Series | float) -> np.ndarray:
    return np.mod(values, 360.0)


def signed_circular_delta(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    return ((actual - predicted + 180.0) % 360.0) - 180.0


def arc_contains(actual: np.ndarray, dir_lo: np.ndarray, dir_hi: np.ndarray) -> np.ndarray:
    width = np.mod(dir_hi - dir_lo, 360.0)
    return np.mod(actual - dir_lo, 360.0) <= width


def source_direction_column(horizon: int, hour: int, columns: set[str]) -> str | None:
    candidates = [
        f"dir_d{horizon}_h{hour}",
        f"fcst_dir_d{horizon}_h{hour}",
        "wd10",
    ]
    return next((col for col in candidates if col in columns), None)


def source_speed_column(horizon: int, hour: int, columns: set[str]) -> str | None:
    candidates = [
        f"speed_d{horizon}_h{hour}",
        f"fcst_speed_d{horizon}_h{hour}",
        "ws10",
    ]
    return next((col for col in candidates if col in columns), None)


@lru_cache(maxsize=None)
def load_station_meta(region: str) -> pd.DataFrame:
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    return meta[meta["region"] == region].copy()


@lru_cache(maxsize=None)
def load_region_features(region: str) -> pd.DataFrame:
    features = load_features(region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    return features


@lru_cache(maxsize=None)
def load_station_observations(region: str) -> pd.DataFrame:
    obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
    obs["time"] = pd.to_datetime(obs["time"])
    return obs.dropna(subset=["direction"]).copy()


def build_station_direction_frame(region: str, horizon: int, split: str) -> pd.DataFrame:
    """Build station-direction residual rows for one region/horizon/split."""

    start, end = SPLIT_RANGES[split]
    features = load_region_features(region)
    columns = set(features.columns)
    obs = load_station_observations(region)
    meta = load_station_meta(region)
    frames: list[pd.DataFrame] = []

    for station_row in meta.itertuples(index=False):
        station_obs = obs[obs["station"] == station_row.station][["time", "direction"]].copy()
        if station_obs.empty:
            continue

        grid = features[
            (features["latitude"] == round(float(station_row.nearest_grid_lat), 2))
            & (features["longitude"] == round(float(station_row.nearest_grid_lon), 2))
        ].copy()
        if grid.empty:
            continue

        for hour in HOURS:
            dir_col = source_direction_column(horizon, int(hour), columns)
            if dir_col is None:
                continue
            speed_col = source_speed_column(horizon, int(hour), columns)

            sub = grid.copy()
            sub["hour"] = int(hour)
            sub["horizon"] = int(horizon)
            sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
            sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce")
            sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
            sub["source_direction_col"] = dir_col
            sub["source_speed_col"] = speed_col or ""

            merged = sub.merge(
                station_obs.rename(columns={"time": "target_time", "direction": "target_direction"}),
                on="target_time",
                how="inner",
            )
            merged = merged[(merged["target_time"] >= start) & (merged["target_time"] <= end)].copy()
            if merged.empty:
                continue

            merged["station"] = station_row.station
            merged["station_lat"] = float(station_row.latitude)
            merged["station_lon"] = float(station_row.longitude)
            merged["station_height_m"] = float(station_row.height_m)
            merged["nearest_grid_lat"] = float(station_row.nearest_grid_lat)
            merged["nearest_grid_lon"] = float(station_row.nearest_grid_lon)
            merged["region"] = region
            merged["split"] = split
            frames.append(merged)

    if not frames:
        return pd.DataFrame()

    frame = pd.concat(frames, ignore_index=True)
    frame["target_direction"] = pd.to_numeric(frame["target_direction"], errors="coerce")
    frame["base_direction"] = pd.to_numeric(frame["base_direction"], errors="coerce") % 360.0
    frame = frame.dropna(subset=["target_direction", "base_direction"]).copy()
    frame["signed_residual"] = signed_circular_delta(
        frame["target_direction"].to_numpy(dtype=float),
        frame["base_direction"].to_numpy(dtype=float),
    )
    frame["abs_residual"] = np.abs(frame["signed_residual"])
    frame["base_error"] = _circ_dist(
        frame["target_direction"].to_numpy(dtype=float),
        frame["base_direction"].to_numpy(dtype=float),
    )
    frame["base_width"] = np.nan
    frame["base_dir_05"] = np.nan
    frame["base_dir_95"] = np.nan
    frame["base_hit"] = False
    frame["base_cws_sample"] = np.nan
    return frame


def calibrate_base_widths(train_frame: pd.DataFrame) -> dict[tuple[str, int], float]:
    """Return per station/hour 90th-pct residual widths plus global fallback."""

    widths: dict[tuple[str, int], float] = {}
    if train_frame.empty:
        return widths
    global_width = float(np.nanquantile(train_frame["base_error"], 1.0 - ALPHA))
    widths[("__global__", -1)] = global_width
    for (station, hour), group in train_frame.groupby(["station", "hour"]):
        if len(group) < 10:
            continue
        widths[(str(station), int(hour))] = float(np.nanquantile(group["base_error"], 1.0 - ALPHA))
    return widths


def apply_base_widths(frame: pd.DataFrame, widths: dict[tuple[str, int], float]) -> pd.DataFrame:
    out = frame.copy()
    fallback = widths.get(("__global__", -1), float(np.nanquantile(out["base_error"], 1.0 - ALPHA)))
    width_values = np.array(
        [widths.get((str(st), int(hr)), fallback) for st, hr in zip(out["station"], out["hour"])],
        dtype=float,
    )
    center = out["base_direction"].to_numpy(dtype=float)
    actual = out["target_direction"].to_numpy(dtype=float)
    out["base_width"] = width_values
    out["base_dir_05"] = wrap_360(center - width_values)
    out["base_dir_95"] = wrap_360(center + width_values)
    out["base_hit"] = arc_contains(actual, out["base_dir_05"].to_numpy(dtype=float), out["base_dir_95"].to_numpy(dtype=float))
    out["base_cws_sample"] = circular_winkler_per_sample(
        actual,
        out["base_dir_05"].to_numpy(dtype=float),
        out["base_dir_95"].to_numpy(dtype=float),
        alpha=ALPHA,
    )
    return out


def build_station_atlas(region: str, horizon: int, split: str) -> pd.DataFrame:
    train_frame = build_station_direction_frame(region, horizon, "train")
    frame = build_station_direction_frame(region, horizon, split)
    if frame.empty:
        return frame
    widths = calibrate_base_widths(train_frame)
    return apply_base_widths(frame, widths)


def summarize_atlas(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in frame.groupby(["region", "horizon", "split"], dropna=False):
        y = group["target_direction"].to_numpy(dtype=float)
        rows.append(
            {
                "region": keys[0],
                "horizon": int(keys[1]),
                "split": keys[2],
                "rows": len(group),
                "base_cws": circular_winkler_score(
                    y,
                    group["base_dir_05"].to_numpy(dtype=float),
                    group["base_dir_95"].to_numpy(dtype=float),
                    alpha=ALPHA,
                ),
                "base_mae": float(np.nanmean(group["base_error"])),
                "base_coverage": float(np.nanmean(group["base_hit"])),
                "base_width": float(np.nanmean(group["base_width"])),
            }
        )
    return pd.DataFrame(rows)


def build_inference_station_frame(region: str, horizon: int, window: int) -> pd.DataFrame:
    features = load_inference_features(window, region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    columns = set(features.columns)
    meta = load_station_meta(region)
    frames: list[pd.DataFrame] = []

    for station_row in meta.itertuples(index=False):
        grid = features[
            (features["latitude"] == round(float(station_row.nearest_grid_lat), 2))
            & (features["longitude"] == round(float(station_row.nearest_grid_lon), 2))
        ].copy()
        if grid.empty:
            continue

        for hour in HOURS:
            dir_col = source_direction_column(horizon, int(hour), columns)
            if dir_col is None:
                continue
            speed_col = source_speed_column(horizon, int(hour), columns)
            sub = grid.copy()
            sub["station"] = station_row.station
            sub["station_lat"] = float(station_row.latitude)
            sub["station_lon"] = float(station_row.longitude)
            sub["station_height_m"] = float(station_row.height_m)
            sub["nearest_grid_lat"] = float(station_row.nearest_grid_lat)
            sub["nearest_grid_lon"] = float(station_row.nearest_grid_lon)
            sub["region"] = region
            sub["horizon"] = int(horizon)
            sub["hour"] = int(hour)
            sub["window"] = int(window)
            sub["base_direction"] = pd.to_numeric(sub[dir_col], errors="coerce") % 360.0
            sub["base_speed"] = pd.to_numeric(sub[speed_col], errors="coerce") if speed_col else np.nan
            sub["source_direction_col"] = dir_col
            sub["source_speed_col"] = speed_col or ""
            frames.append(sub)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).dropna(subset=["base_direction"])


def write_station_atlas(splits: tuple[str, ...] = ("val", "tune", "holdout")) -> tuple[Path, Path]:
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for region in REGIONS:
        for horizon in HORIZONS:
            for split in splits:
                frame = build_station_atlas(region, horizon, split)
                if not frame.empty:
                    frames.append(frame)
    atlas = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    atlas_path = ATLAS_DIR / "station_direction_atlas.parquet"
    summary_path = ATLAS_DIR / "station_direction_summary.csv"
    atlas.to_parquet(atlas_path, index=False)
    summarize_atlas(atlas).to_csv(summary_path, index=False)
    return atlas_path, summary_path


def main() -> int:
    atlas_path, summary_path = write_station_atlas()
    print(f"Wrote atlas: {atlas_path}")
    print(f"Wrote summary: {summary_path}")
    print(pd.read_csv(summary_path).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
