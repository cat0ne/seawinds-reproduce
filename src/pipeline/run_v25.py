"""V25: d14 pressure-speed analog ensemble probe.

This is the tactical follow-up for the remaining pressure-speed gap:
`speed_pressure_d14_ns` and `speed_pressure_d14_ecs`.

The model changes only d14 pressure speed. It leaves surface, stations,
direction, and d1/d7 pressure speed exactly as v16, then blends v16's baseline
d14 pressure intervals with empirical analog quantiles built from 2019-2021
provided data.

Usage:
    python -m src.pipeline.run_v25 --analog-weight 0.35
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from src.data.paths import HOURS, PRESSURE_LEVELS, PROJECT_ROOT, REGIONS
from src.io.dataset import load_features, load_inference_features
from src.models.analog import AnalogEnsemble
from src.pipeline.pipeline_utils import (
    fix_crossing,
    load_reanalysis_level,
    save_submission,
    speed_from_uv,
)
from src.pipeline.run_v16 import generate_v16


ANALOG_PREDICTORS = (
    "msl",
    "z700",
    "ws10",
    "ws100",
    "wind_shear",
    "ws10_lag1d",
    "ws10_lag3d",
    "ws10_lag7d",
    "msl_lag1d",
    "msl_lag3d",
    "msl_lag7d",
    "ws10_rmean3d",
    "ws10_rstd3d",
    "ws10_rmean7d",
    "ws10_rstd7d",
    "t2m",
    "sst",
    "blh",
    "cape",
    "elevation",
    "woy_sin",
    "woy_cos",
    "fcst_p_d7_speed",
    "fcst_p_d10_speed",
)


def load_v16_predictions() -> pd.DataFrame:
    """Load existing v16 predictions, generating them if needed."""
    csv_path = PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_v16.csv"
    if not csv_path.exists():
        generate_v16()
    return pd.read_csv(csv_path, low_memory=False)


def add_pressure_forecast_speeds(df: pd.DataFrame, level: str, hour: int) -> pd.DataFrame:
    """Add d7/d10 pressure HRES speed predictors for a level/hour."""
    out = df.copy()
    for lead in (7, 10):
        u_col = f"fcst_u_{level}_d{lead}_h{hour}"
        v_col = f"fcst_v_{level}_d{lead}_h{hour}"
        speed_col = f"fcst_p_d{lead}_speed"
        if u_col in out.columns and v_col in out.columns:
            out[speed_col] = speed_from_uv(out[u_col].astype(float), out[v_col].astype(float))
        else:
            out[speed_col] = np.nan
    return out


def available_predictors(df: pd.DataFrame) -> list[str]:
    """Return the configured analog predictors present in a frame."""
    return [col for col in ANALOG_PREDICTORS if col in df.columns]


def build_training_frame(
    region: str,
    level: str,
    hour: int,
    max_rows: int,
    random_state: int,
) -> tuple[pd.DataFrame, list[str]]:
    """Build historical analog rows for one region/level/hour."""
    features = load_features(region)
    features["time"] = pd.to_datetime(features["time"])
    features["latitude"] = features["latitude"].astype(float).round(2)
    features["longitude"] = features["longitude"].astype(float).round(2)
    features = add_pressure_forecast_speeds(features, level, hour)

    predictors = available_predictors(features)
    if not predictors:
        raise ValueError(f"No analog predictors available for {region}/{level}/h{hour}")

    sub = features[["time", "latitude", "longitude", *predictors]].copy()
    sub["target_time"] = sub["time"] + pd.Timedelta(days=14, hours=hour)
    sub["month"] = sub["target_time"].dt.month

    target = load_reanalysis_level(region, level)
    target = target.rename(columns={"time": "target_time", "speed": "target"})
    merged = sub.merge(
        target[["target_time", "latitude", "longitude", "target"]],
        on=["target_time", "latitude", "longitude"],
        how="inner",
    )
    merged = merged[np.isfinite(merged["target"])]

    if max_rows and len(merged) > max_rows:
        merged = merged.sample(n=max_rows, random_state=random_state).reset_index(drop=True)

    return merged, predictors


def build_inference_frame(window_id: int, region: str, level: str, hour: int) -> tuple[pd.DataFrame, list[str]]:
    """Build analog context rows for one inference window/level/hour."""
    inf = load_inference_features(window_id, region)
    inf["time"] = pd.to_datetime(inf["time"])
    inf["latitude"] = inf["latitude"].astype(float).round(2)
    inf["longitude"] = inf["longitude"].astype(float).round(2)
    inf = add_pressure_forecast_speeds(inf, level, hour)
    predictors = available_predictors(inf)
    context = inf[["time", "latitude", "longitude", *predictors]].copy()
    target_time = context["time"] + pd.Timedelta(days=14, hours=hour)
    context["month"] = target_time.dt.month
    return context, predictors


def predict_d14_pressure_analogs(
    *,
    k: int,
    max_train_rows: int,
    random_state: int,
) -> pd.DataFrame:
    """Predict d14 pressure-speed analog quantiles for all inference windows."""
    rows = []
    for region in REGIONS:
        print(f"\n=== {region} ===")
        for level in PRESSURE_LEVELS:
            for hour in HOURS:
                label = f"{region}/{level}/h{hour}"
                print(f"  Training analog {label}...")
                train_df, predictors = build_training_frame(
                    region=region,
                    level=str(level),
                    hour=hour,
                    max_rows=max_train_rows,
                    random_state=random_state,
                )
                if len(train_df) < k:
                    print(f"    SKIP: only {len(train_df):,} rows")
                    continue

                model = AnalogEnsemble(
                    k=k,
                    predictors=tuple(predictors),
                    target_col="target",
                    group_cols=("month",),
                    min_group_size=max(k, 100),
                ).fit(train_df)

                for wid in range(1, 9):
                    context, _ = build_inference_frame(wid, region, str(level), hour)
                    pred = model.predict_distribution(context, target_lead_days=14)
                    for pred_idx, (_, row) in enumerate(context.iterrows()):
                        rows.append(
                            {
                                "window": wid,
                                "region": region,
                                "latitude": float(row["latitude"]),
                                "longitude": float(row["longitude"]),
                                "horizon": 14,
                                "hour": hour,
                                "level": str(level),
                                "analog_q05": pred.q05[pred_idx],
                                "analog_q50": pred.q50[pred_idx],
                                "analog_q95": pred.q95[pred_idx],
                                "analog_mean_distance": pred.mean_distance[pred_idx],
                                "analog_n_neighbors": int(pred.n_neighbors[pred_idx]),
                            }
                        )
                print(f"    done: {len(train_df):,} train rows, {len(predictors)} predictors")

    return pd.DataFrame(rows)


def merge_analog_speed(v16: pd.DataFrame, analog: pd.DataFrame, analog_weight: float) -> pd.DataFrame:
    """Blend analog d14 pressure speed into a v16 submission frame."""
    if analog.empty:
        raise ValueError("analog predictions are empty")

    out = v16.copy()
    for col in ["latitude", "longitude"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
        analog[col] = pd.to_numeric(analog[col], errors="coerce").round(2)
    for col in ["horizon", "hour"]:
        out[col] = out[col].astype(int)
        analog[col] = analog[col].astype(int)
    level_mask = out["level"].notna()
    out.loc[level_mask, "level"] = out.loc[level_mask, "level"].astype(str)
    analog["level"] = analog["level"].astype(str)

    keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    merged = out.merge(analog, on=keys, how="left")

    mask = (
        (merged["type"] == "grid")
        & (merged["horizon"] == 14)
        & (merged["level"].isin(PRESSURE_LEVELS))
        & merged["analog_q05"].notna()
    )
    if not mask.any():
        raise ValueError("No v16 pressure d14 rows matched analog predictions")

    base = (
        merged.loc[mask, "q05"].to_numpy(dtype=float),
        merged.loc[mask, "q50"].to_numpy(dtype=float),
        merged.loc[mask, "q95"].to_numpy(dtype=float),
    )
    analog_q = (
        merged.loc[mask, "analog_q05"].to_numpy(dtype=float),
        merged.loc[mask, "analog_q50"].to_numpy(dtype=float),
        merged.loc[mask, "analog_q95"].to_numpy(dtype=float),
    )
    q05, q50, q95 = AnalogEnsemble.blend_quantiles(base, analog_q, analog_weight)
    merged.loc[mask, "q05"] = q05
    merged.loc[mask, "q50"] = q50
    merged.loc[mask, "q95"] = q95

    drop_cols = [col for col in merged.columns if col.startswith("analog_")]
    merged = merged.drop(columns=drop_cols)
    return fix_crossing(merged)


def generate_v25(analog_weight: float = 0.35, k: int = 50, max_train_rows: int = 120_000) -> None:
    print("\n" + "=" * 60)
    print("Generating V25 submission (d14 pressure analog blend)")
    print("=" * 60)
    t0 = time.time()

    v16 = load_v16_predictions()
    analog = predict_d14_pressure_analogs(k=k, max_train_rows=max_train_rows, random_state=42)
    out = merge_analog_speed(v16, analog, analog_weight=analog_weight)

    changed = (
        (out["type"] == "grid")
        & (out["horizon"].astype(int) == 14)
        & (out["level"].astype(str).isin(PRESSURE_LEVELS))
    ).sum()
    print(f"  Blended analog speed into {changed:,} pressure d14 rows")
    print(f"  Done in {time.time() - t0:.0f}s")

    tag = f"v25_anen_w{analog_weight:.2f}".replace(".", "p")
    save_submission(out, tag)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analog-weight", type=float, default=0.35)
    parser.add_argument("--k", type=int, default=50)
    parser.add_argument("--max-train-rows", type=int, default=120_000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_v25(
        analog_weight=args.analog_weight,
        k=args.k,
        max_train_rows=args.max_train_rows,
    )
