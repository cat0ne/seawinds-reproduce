"""Shared utilities for v7-v11 submission pipelines.

Provides common functions for:
- Data loading and target computation
- Feature engineering
- Model training helpers
- Submission assembly and saving
"""
from __future__ import annotations

import pickle
import time
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.io.dataset import load_inference_features

from src.data.paths import (
    ALPHA,
    FEATURES_DIR,
    HOLDOUT_END,
    HOLDOUT_START,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    PROJECT_ROOT,
    REGIONS,
    SCORING_DIR,
    SURFACE_LEVELS,
    TRAIN_DIR,
    TRAIN_END,
    TRAIN_START,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)

warnings.filterwarnings("ignore")

ALL_LEVELS = ["10m", "100m"] + [str(l) for l in PRESSURE_LEVELS]


def direction_from_uv(u, v):
    return (270.0 - np.degrees(np.arctan2(v, u))) % 360.0


def speed_from_uv(u, v):
    return np.sqrt(u ** 2 + v ** 2)


def load_reanalysis_level(region: str, level: str) -> pd.DataFrame:
    if level in ("10m", "100m"):
        path = TRAIN_DIR / f"reanalysis_{region}_6h.parquet"
        u_col = "u10" if level == "10m" else "u100"
        v_col = "v10" if level == "10m" else "v100"
    else:
        path = TRAIN_DIR / f"reanalysis_pressure_{region}.parquet"
        u_col = f"u_{level}"
        v_col = f"v_{level}"

    df = pd.read_parquet(path, columns=["time", "latitude", "longitude", u_col, v_col])
    df["time"] = pd.to_datetime(df["time"])
    df["speed"] = speed_from_uv(df[u_col], df[v_col])
    df["direction"] = direction_from_uv(df[u_col], df[v_col])
    df["latitude"] = df["latitude"].astype(float).round(2)
    df["longitude"] = df["longitude"].astype(float).round(2)
    return df[["time", "latitude", "longitude", "speed", "direction"]]


def get_base_feature_cols(columns: list[str]) -> list[str]:
    exclude = {"time", "latitude", "longitude"}
    exclude |= {c for c in columns if c.startswith(("speed_d", "dir_d"))}
    return sorted(c for c in columns if c not in exclude)


def split_by_time(df: pd.DataFrame):
    t = df["time"]
    return (
        df[(t >= TRAIN_START) & (t <= TRAIN_END)].copy(),
        df[(t >= VAL_START) & (t <= VAL_END)].copy(),
        df[(t >= TUNE_START) & (t <= TUNE_END)].copy(),
        df[(t >= HOLDOUT_START) & (t <= HOLDOUT_END)].copy(),
    )


def align_columns(df: pd.DataFrame, ref_cols: list[str]) -> pd.DataFrame:
    for c in ref_cols:
        if c not in df.columns:
            df[c] = 0
    return df[ref_cols].astype(np.float32)


def add_time_encodings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "time" not in df.columns:
        return df
    dt = pd.to_datetime(df["time"])
    month = dt.dt.month
    df["month_sin"] = np.sin(2 * np.pi * month / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * month / 12.0)
    doy = dt.dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.0)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.0)
    return df


def apply_height_correction(stations_df: pd.DataFrame) -> pd.DataFrame:
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    z0 = 0.03
    for _, row in meta.iterrows():
        h = float(row["height_m"])
        if abs(h - 10.0) < 0.1:
            continue
        ratio = np.log(h / z0) / np.log(10.0 / z0)
        mask = stations_df["station"] == row["station"]
        stations_df.loc[mask, "q05"] = np.maximum(stations_df.loc[mask, "q05"] * ratio, 0)
        stations_df.loc[mask, "q50"] = stations_df.loc[mask, "q50"] * ratio
        stations_df.loc[mask, "q95"] = stations_df.loc[mask, "q95"] * ratio
    return stations_df


def fix_crossing(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    q = df[["q05", "q50", "q95"]].values
    q_s = np.sort(q, axis=1)
    df["q05"] = np.maximum(q_s[:, 0], 0)
    df["q50"] = q_s[:, 1]
    df["q95"] = q_s[:, 2]
    return df


SUB_COLS = [
    "type", "window", "region", "latitude", "longitude", "station",
    "horizon", "hour", "level", "q05", "q50", "q95",
    "dir_05", "dir_50", "dir_95",
]


def save_submission(df: pd.DataFrame, version: str) -> Path:
    out_dir = PROJECT_ROOT / "submissions"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = df[SUB_COLS].copy()
    csv_path = out_dir / f"predictions_{version}.csv"
    df.to_csv(csv_path, index=False)
    zip_path = out_dir / f"submission_{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname="predictions.csv")
    size_mb = zip_path.stat().st_size / 1e6
    print(f"  Saved: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


def load_baseline():
    return pd.read_csv(
        PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_light.csv",
        low_memory=False,
    )


def load_geospatial(region: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"geospatial_{region}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def load_geospatial_inference(window_id: int, region: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"geospatial_inference_window_{window_id}_{region}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


POOLED_DIR_DIR = LOGS_DIR / "direction_models"
PERHORIZ_DIR_DIR = LOGS_DIR / "direction_models_v7"


def generate_hybrid_direction(
    perhoriz_dir: Path = PERHORIZ_DIR_DIR,
    pooled_dir: Path = POOLED_DIR_DIR,
    d14_only_perhoriz: bool = True,
) -> dict:
    if d14_only_perhoriz:
        horizons_perhoriz = {14}
    else:
        horizons_perhoriz = set(HORIZONS)

    pooled_cache: dict[tuple, object] = {}
    for region in REGIONS:
        for level in ALL_LEVELS:
            p = pooled_dir / region / level / "model.pkl"
            if p.exists():
                import pickle as _pkl
                with open(p, "rb") as f:
                    pooled_cache[(region, level)] = _pkl.load(f)

    all_dir: dict[tuple, tuple] = {}

    for region in REGIONS:
        for level in ALL_LEVELS:
            pooled_art = pooled_cache.get((region, level))
            for horizon in HORIZONS:
                use_perhoriz = horizon in horizons_perhoriz
                perhoriz_path = perhoriz_dir / region / level / f"d{horizon}" / "model.pkl"
                perhoriz_art = None
                if use_perhoriz and perhoriz_path.exists():
                    import pickle as _pkl
                    with open(perhoriz_path, "rb") as f:
                        perhoriz_art = _pkl.load(f)

                if perhoriz_art is None and pooled_art is None:
                    continue

                active_art = perhoriz_art if perhoriz_art else pooled_art
                active_feat = active_art["feature_cols"]

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    available = [c for c in active_feat if c in inf.columns]
                    missing = set(active_feat) - set(available) - {
                        c for c in active_feat if c.startswith(("hour_", "horizon_", "month_", "doy_"))
                    }
                    if missing:
                        continue

                    for hour in HOURS:
                        df_pred = inf[available].copy()
                        for hr in HOURS:
                            df_pred[f"hour_{hr}"] = int(hr == hour)

                        if perhoriz_art is None:
                            for h in HORIZONS:
                                df_pred[f"horizon_{h}"] = int(h == horizon)

                        dt = pd.to_datetime(inf["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        if perhoriz_art is not None:
                            df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
                            df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

                        X = align_columns(df_pred, active_feat)
                        d05, d50, d95 = active_art["model"].predict(X)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, float(lats[i]), float(lons[i]), int(horizon), int(hour), str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(all_dir):,} dir entries")

    return all_dir


def direction_df_from_dict(all_dir: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {"window": k[0], "region": k[1], "latitude": k[2], "longitude": k[3],
         "horizon": k[4], "hour": k[5], "level": k[6],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in all_dir.items()
    ])


def merge_direction_onto_grid(grid_df: pd.DataFrame, dir_df: pd.DataFrame) -> pd.DataFrame:
    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    grid_df["latitude"] = grid_df["latitude"].astype(float).round(2)
    grid_df["longitude"] = grid_df["longitude"].astype(float).round(2)
    grid_df["horizon"] = grid_df["horizon"].astype(int)
    grid_df["hour"] = grid_df["hour"].astype(int)
    for c in ["latitude", "longitude"]:
        dir_df[c] = dir_df[c].astype(float).round(2)
    dir_df["horizon"] = dir_df["horizon"].astype(int)
    dir_df["hour"] = dir_df["hour"].astype(int)

    before = len(grid_df)
    grid_df = grid_df.merge(dir_df, on=merge_keys, how="left", suffixes=("_old", ""))
    for dcol in ["dir_05", "dir_50", "dir_95"]:
        if f"{dcol}_old" in grid_df.columns:
            grid_df[dcol] = grid_df[dcol].fillna(grid_df[f"{dcol}_old"])
            grid_df = grid_df.drop(columns=[f"{dcol}_old"])
    assert len(grid_df) == before, f"Row count changed: {before} -> {len(grid_df)}"
    return grid_df
