"""Loaders for training and inference data.

All paths are resolved via src.data.paths — consumers never touch raw paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.data.paths import (
    DATASET_DIR,
    FEATURES_DIR,
    INFERENCE_DIR,
    N_WINDOWS,
    REGIONS,
    SCORING_DIR,
    TRAIN_DIR,
)


def load_reanalysis_surface(
    region: str,
    start_date: str | None = None,
    end_date: str | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    path = TRAIN_DIR / f"reanalysis_{region}_6h.parquet"
    df = pd.read_parquet(path, columns=columns)
    df["time"] = pd.to_datetime(df["time"])
    if start_date:
        df = df[df["time"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["time"] <= pd.Timestamp(end_date)]
    return df


def load_reanalysis_pressure(
    region: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    path = TRAIN_DIR / f"reanalysis_pressure_{region}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    if start_date:
        df = df[df["time"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["time"] <= pd.Timestamp(end_date)]
    return df


def load_reanalysis_worldwide(
    years: list[int] | None = None,
) -> pd.DataFrame:
    if years is None:
        years = [2019, 2020, 2021]
    frames = []
    for year in years:
        path = TRAIN_DIR / f"reanalysis_worldwide_daily_{year}.parquet"
        if not path.exists():
            print(f"  WARNING: {path.name} not found")
            continue
        df = pd.read_parquet(path)
        df["time"] = pd.to_datetime(df["time"])
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No worldwide reanalysis files found")
    return pd.concat(frames, ignore_index=True)


def load_hres_surface(region: str) -> pd.DataFrame:
    path = TRAIN_DIR / f"hres_{region}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_hres_pressure(region: str) -> pd.DataFrame:
    path = TRAIN_DIR / f"hres_pressure_{region}.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_stations(
    region: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    regions = [region] if region else REGIONS
    frames = []
    for r in regions:
        path = TRAIN_DIR / f"stations_{r}_6h.parquet"
        if not path.exists():
            print(f"  WARNING: {path.name} not found")
            continue
        df = pd.read_parquet(path)
        df["time"] = pd.to_datetime(df["time"])
        if start_date:
            df = df[df["time"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["time"] <= pd.Timestamp(end_date)]
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_elevation(region: str) -> xr.DataArray | None:
    path = TRAIN_DIR / f"elevation_{region}.nc"
    if not path.exists():
        return None
    ds = xr.open_dataset(path)
    var = "z" if "z" in ds else list(ds.data_vars)[0]
    da = ds[var]
    da.attrs["source"] = str(path)
    return da


def load_lsm(region: str) -> xr.DataArray | None:
    path = TRAIN_DIR / f"lsm_{region}.nc"
    if not path.exists():
        return None
    ds = xr.open_dataset(path)
    var = list(ds.data_vars)[0]
    return ds[var]


def load_features(region: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"train_{region}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_inference_features(window_id: int, region: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"inference_window_{window_id}_{region}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_inference_window(window_id: int) -> dict[str, pd.DataFrame]:
    wdir = INFERENCE_DIR / f"window_{window_id}"
    if not wdir.exists():
        raise FileNotFoundError(f"Window directory not found: {wdir}")

    result = {}

    meta_path = wdir / "metadata.json"
    if meta_path.exists():
        result["metadata"] = json.loads(meta_path.read_text())

    for key, filename in [
        ("worldwide", "context_worldwide_daily.parquet"),
    ]:
        path = wdir / filename
        if path.exists():
            df = pd.read_parquet(path)
            df["time"] = pd.to_datetime(df["time"])
            result[key] = df

    for region in REGIONS:
        for key, filename in [
            (f"reanalysis_{region}", f"context_reanalysis_{region}.parquet"),
            (f"reanalysis_pressure_{region}", f"context_reanalysis_pressure_{region}.parquet"),
            (f"hres_{region}", f"context_hres_{region}.parquet"),
            (f"hres_pressure_{region}", f"context_hres_pressure_{region}.parquet"),
            (f"stations_{region}", f"context_stations_{region}.parquet"),
        ]:
            path = wdir / filename
            if path.exists():
                df = pd.read_parquet(path)
                if "time" in df.columns:
                    df["time"] = pd.to_datetime(df["time"])
                result[key] = df

    return result


def load_all_inference_windows() -> dict[int, dict]:
    windows = {}
    for wid in range(1, N_WINDOWS + 1):
        wdir = INFERENCE_DIR / f"window_{wid}"
        if wdir.exists():
            windows[wid] = load_inference_window(wid)
    return windows


def load_sample_submission() -> pd.DataFrame:
    path = SCORING_DIR / "sample_submission.csv"
    return pd.read_csv(path)
