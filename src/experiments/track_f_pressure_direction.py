"""Track F: pressure-direction circular prototype.

Pressure direction remains a large rank block. This prototype evaluates a
bounded circular model against a calibrated HRES-direction baseline on
historical splits. It samples rows per level/horizon to keep local iteration
cheap before any full production training.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import HOURS, HORIZONS, LOGS_DIR, PRESSURE_LEVELS, REGIONS
from src.experiments.track_d_direction_proto import CircularDirectionBundle
from src.io.dataset import load_features, load_inference_features, load_reanalysis_pressure
from src.scoring.winkler import _circ_dist, circular_winkler_score
from src.validate import get_split_dates


def _direction_from_uv(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return (270.0 - np.degrees(np.arctan2(v, u))) % 360.0


def _build_frame(region: str, horizon: int, level: int | str) -> pd.DataFrame:
    level = str(level)
    features = load_features(region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)

    pressure = load_reanalysis_pressure(region)
    pressure["time"] = pd.to_datetime(pressure["time"])
    pressure["latitude"] = pressure["latitude"].astype(float).round(2)
    pressure["longitude"] = pressure["longitude"].astype(float).round(2)
    u_col, v_col = f"u_{level}", f"v_{level}"
    target = pressure[["time", "latitude", "longitude", u_col, v_col]].copy()
    target["target_direction"] = _direction_from_uv(target[u_col].to_numpy(dtype=float), target[v_col].to_numpy(dtype=float))
    target = target.rename(columns={"time": "target_time"})

    frames: list[pd.DataFrame] = []
    for hour in HOURS:
        sub = features.copy()
        sub["hour"] = int(hour)
        sub["horizon"] = int(horizon)
        sub["level"] = int(level)
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        merged = sub.merge(
            target[["target_time", "latitude", "longitude", "target_direction"]],
            on=["target_time", "latitude", "longitude"],
            how="inner",
        )
        if merged.empty:
            continue
        fcst_u = f"fcst_u_{level}_d{horizon}_h{hour}"
        fcst_v = f"fcst_v_{level}_d{horizon}_h{hour}"
        if fcst_u in merged.columns and fcst_v in merged.columns:
            merged["hres_direction"] = _direction_from_uv(
                pd.to_numeric(merged[fcst_u], errors="coerce").to_numpy(dtype=float),
                pd.to_numeric(merged[fcst_v], errors="coerce").to_numpy(dtype=float),
            )
        frames.append(merged)

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True).dropna(subset=["target_direction", "hres_direction"])
    return out


def _split(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    start, end = get_split_dates(split)
    t = pd.to_datetime(frame["target_time"])
    return frame[t.between(pd.Timestamp(start), pd.Timestamp(end))].copy()


def _train(frame: pd.DataFrame, max_rows: int = 4_000) -> CircularDirectionBundle:
    train = _split(frame, "train")
    if len(train) > max_rows:
        train = train.sample(n=max_rows, random_state=42).sort_index()
    bundle = CircularDirectionBundle(calibration_days=60, max_train_rows=max_rows, max_calibration_rows=3_000)
    bundle.fit(train)
    return bundle


MODEL_CACHE_DIR = LOGS_DIR / "track_f_pressure_direction_models"
MODEL_CACHE_VERSION = "track_f_pressure_direction_v1"
MODEL_SCOPE = {
    "version": MODEL_CACHE_VERSION,
    "levels": ["1000", "925", "850", "700", "500"],
    "horizons": [1, 7],
    "max_train_rows": 4000,
    "calibration_days": 60,
    "feature_builder": "track_f_pressure_direction._build_frame",
    "model_class": "CircularDirectionBundle",
}


def _model_cache_path(region: str, horizon: int, level: str) -> Path:
    safe_region = region.replace("/", "_")
    return MODEL_CACHE_DIR / f"{safe_region}_d{horizon}_{level}.pkl"


def _metadata_cache_path(region: str, horizon: int, level: str) -> Path:
    safe_region = region.replace("/", "_")
    return MODEL_CACHE_DIR / f"{safe_region}_d{horizon}_{level}.json"


def _cache_metadata(region: str, horizon: int, level: str) -> dict:
    return {
        **MODEL_SCOPE,
        "region": region,
        "horizon": int(horizon),
        "level": str(level),
    }


def _cache_matches(region: str, horizon: int, level: str) -> bool:
    meta_path = _metadata_cache_path(region, horizon, level)
    if not meta_path.exists():
        return False
    try:
        return json.loads(meta_path.read_text()) == _cache_metadata(region, horizon, level)
    except json.JSONDecodeError:
        return False


def fit_production_models(
    levels: tuple[int, ...] = (1000, 925, 850, 700, 500),
    horizons: tuple[int, ...] = (1, 7),
    use_cache: bool = True,
) -> dict[tuple[str, int, str], CircularDirectionBundle]:
    """Fit Track F production models for pressure direction."""

    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    models: dict[tuple[str, int, str], CircularDirectionBundle] = {}
    for region in REGIONS:
        for horizon in horizons:
            for level in levels:
                level_str = str(level)
                cache_path = _model_cache_path(region, horizon, level_str)
                if use_cache and cache_path.exists() and _cache_matches(region, horizon, level_str):
                    print(f"  [track_f] loading cached {region} d{horizon} level {level_str}")
                    with open(cache_path, "rb") as f:
                        models[(region, horizon, level_str)] = pickle.load(f)
                    continue

                print(f"  [track_f] training {region} d{horizon} level {level_str}")
                frame = _build_frame(region, horizon, level)
                if frame.empty:
                    continue
                model = _train(frame)
                models[(region, horizon, level_str)] = model
                if use_cache:
                    with open(cache_path, "wb") as f:
                        pickle.dump(model, f)
                    _metadata_cache_path(region, horizon, level_str).write_text(
                        json.dumps(_cache_metadata(region, horizon, level_str), indent=2)
                    )
    return models


def _build_inference_frame(region: str, horizon: int, level: int | str, window: int) -> pd.DataFrame:
    level = str(level)
    features = load_inference_features(window, region).copy()
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)

    frames: list[pd.DataFrame] = []
    for hour in HOURS:
        fcst_u = f"fcst_u_{level}_d{horizon}_h{hour}"
        fcst_v = f"fcst_v_{level}_d{horizon}_h{hour}"
        if fcst_u not in features.columns or fcst_v not in features.columns:
            continue
        sub = features.copy()
        sub["hour"] = int(hour)
        sub["horizon"] = int(horizon)
        sub["level"] = int(level)
        sub["window"] = int(window)
        sub["region"] = region
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        sub["hres_direction"] = _direction_from_uv(
            pd.to_numeric(sub[fcst_u], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(sub[fcst_v], errors="coerce").to_numpy(dtype=float),
        )
        frames.append(sub)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).dropna(subset=["hres_direction"])


def predict_inference_overrides(
    models: dict[tuple[str, int, str], CircularDirectionBundle],
) -> pd.DataFrame:
    """Predict pressure-direction overrides for all phase-1 inference windows."""

    rows: list[pd.DataFrame] = []
    for (region, horizon, level), model in models.items():
        for window in range(1, 9):
            frame = _build_inference_frame(region, horizon, level, window)
            if frame.empty:
                continue
            pred = model.predict(frame)
            keys = frame[["window", "region", "latitude", "longitude", "horizon", "hour", "level"]].reset_index(drop=True)
            rows.append(pd.concat([keys, pred[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True)], axis=1))

    if not rows:
        return pd.DataFrame(
            columns=["window", "region", "latitude", "longitude", "horizon", "hour", "level", "dir_05", "dir_50", "dir_95"]
        )
    out = pd.concat(rows, ignore_index=True)
    out["latitude"] = out["latitude"].astype(float).round(2)
    out["longitude"] = out["longitude"].astype(float).round(2)
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    out["level"] = out["level"].astype(str)
    return out


def _baseline_interval(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    width = float(np.nanquantile(_circ_dist(train["target_direction"], train["hres_direction"]), 0.90))
    center = eval_frame["hres_direction"].to_numpy(dtype=float)
    return (center - width) % 360.0, center, (center + width) % 360.0


def evaluate_local(
    split: str = "val",
    levels: tuple[int, ...] = (1000, 925, 850, 700, 500),
    horizons: tuple[int, ...] = (1, 7),
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for region in REGIONS:
        suffix = "ns" if region == "north_sea" else "ecs"
        for horizon in horizons:
            for level in levels:
                frame = _build_frame(region, horizon, level)
                if frame.empty:
                    continue
                train = _split(frame, "train")
                eval_frame = _split(frame, split)
                if train.empty or eval_frame.empty:
                    continue
                if len(eval_frame) > 5_000:
                    eval_frame = eval_frame.sample(n=5_000, random_state=7).sort_index()

                bundle = _train(frame)
                pred = bundle.predict(eval_frame)
                b05, _, b95 = _baseline_interval(train, eval_frame)
                y = eval_frame["target_direction"].to_numpy(dtype=float)
                base = circular_winkler_score(y, b05, b95)
                cand = circular_winkler_score(y, pred["dir_05"], pred["dir_95"])
                rows.append(
                    {
                        "dimension": f"dir_pressure_d{horizon}_{suffix}",
                        "region": region,
                        "horizon": horizon,
                        "level": str(level),
                        "baseline": base,
                        "track_f": cand,
                        "delta": cand - base,
                    }
                )
    return pd.DataFrame(rows)


def summarize_by_dimension(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    return (
        results.groupby("dimension", as_index=False)
        .agg(
            baseline=("baseline", "mean"),
            track_f=("track_f", "mean"),
            delta=("delta", "mean"),
            worst_level_delta=("delta", "max"),
        )
        .sort_values("dimension")
        .reset_index(drop=True)
    )


def main() -> int:
    for split in ("val", "tune", "holdout"):
        results = evaluate_local(split=split)
        summary = summarize_by_dimension(results)
        print("\n" + "=" * 80)
        print(f"Track F pressure-direction prototype | split={split}")
        print(summary.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        if not summary.empty:
            print(f"Mean delta: {summary['delta'].mean():+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
