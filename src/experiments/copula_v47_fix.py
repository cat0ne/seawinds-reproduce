"""A1 fix: Speed-direction copula with per-horizon damping.

v46 copula improved NS direction but regressed ECS d14 (+0.66 cWS) and ECS d7
pressure (+0.59 cWS). Root cause: ECS 500 hPa has κ_slope=0.453 (10× NS),
causing 30% widening for low-speed d14 predictions where speed is uncertain.

Fix: dampen copula modulation by horizon (d1 full, d7 ×0.7, d14 ×0.4) and
use tighter clips for levels with extreme κ_slope.

Generates v47 from v41 base.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.data.paths import (
    HORIZONS,
    PRESSURE_LEVELS,
    PROJECT_ROOT,
    REGIONS,
    SURFACE_LEVELS,
    TRAIN_DIR,
)
from src.pipeline.pipeline_utils import save_submission
from src.scoring.winkler import _circ_dist

OUT_DIR = PROJECT_ROOT / "logs" / "copula_v47"
Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]

LEVELS = SURFACE_LEVELS + PRESSURE_LEVELS

HORIZON_DAMPING = {1: 1.0, 7: 0.7, 14: 0.4}

EXTREME_KAPPA_SLOPE = 0.10
EXTREME_CLIP = (0.85, 1.15)
NORMAL_CLIP = (0.7, 1.3)


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _estimate_circular_linear_correlation(speed: np.ndarray, direction_deg: np.ndarray) -> float:
    valid = np.isfinite(speed) & np.isfinite(direction_deg) & (speed > 0)
    speed = speed[valid]
    theta_rad = np.deg2rad(direction_deg[valid])
    if len(speed) < 100:
        return 0.0
    r_ce = np.corrcoef(speed, np.cos(theta_rad))[0, 1]
    r_se = np.corrcoef(speed, np.sin(theta_rad))[0, 1]
    rho = np.sqrt(r_ce**2 + r_se**2)
    sign = np.sign(r_ce * np.mean(np.cos(theta_rad)) + r_se * np.mean(np.sin(theta_rad)))
    return float(np.clip(sign * rho, -0.99, 0.99))


def _estimate_kappa_relationship(
    speed: np.ndarray, direction_deg: np.ndarray, n_bins: int = 10,
) -> tuple[float, float, float]:
    valid = np.isfinite(speed) & np.isfinite(direction_deg) & (speed > 0)
    speed = speed[valid]
    direction_deg = direction_deg[valid]
    if len(speed) < 200:
        return 10.0, 2.0, 0.0
    speed_bins = pd.qcut(speed, n_bins, duplicates="drop")
    kappas, medians = [], []
    for label, group_idx in pd.Series(speed).groupby(speed_bins):
        dirs = direction_deg[group_idx.index]
        if len(dirs) < 20:
            continue
        theta = np.deg2rad(dirs)
        C, S = np.mean(np.cos(theta)), np.mean(np.sin(theta))
        R = np.sqrt(C**2 + S**2)
        if R < 0.01 or R > 0.99:
            continue
        kappa = R * (2 - R**2) / (1 - R**2)
        kappas.append(max(kappa, 0.1))
        medians.append(float(np.median(group_idx.values)))
    if len(kappas) < 3:
        return 10.0, 2.0, 0.0
    medians, kappas = np.array(medians), np.array(kappas)
    median_speed = float(np.median(speed))
    median_kappa = float(np.median(kappas))
    slope = np.polyfit(medians, kappas, 1)[0] if len(medians) >= 3 else 0.0
    return median_speed, median_kappa, float(slope)


def fit_copula_models() -> dict:
    models = {}
    for region in REGIONS:
        print(f"\n  Fitting copula for {region}...")
        for level in LEVELS:
            t0 = time.time()
            if level in ("10m", "100m"):
                path = TRAIN_DIR / f"reanalysis_{region}_6h.parquet"
                u_col = "u10" if level == "10m" else "u100"
                v_col = "v10" if level == "100m" else "v100"
            else:
                path = TRAIN_DIR / f"reanalysis_pressure_{region}.parquet"
                u_col, v_col = f"u_{level}", f"v_{level}"
            try:
                df = pd.read_parquet(path, columns=["time", u_col, v_col])
            except Exception as e:
                print(f"    {level}: skipped ({e})")
                continue
            u = df[u_col].values.astype(float)
            v = df[v_col].values.astype(float)
            speed = np.sqrt(u**2 + v**2)
            direction = (270.0 - np.degrees(np.arctan2(v, u))) % 360.0
            valid = np.isfinite(speed) & np.isfinite(direction) & (speed > 0)
            speed, direction = speed[valid], direction[valid]
            if len(speed) > 100000:
                idx = np.random.RandomState(42).choice(len(speed), 100000, replace=False)
                speed_sample, direction_sample = speed[idx], direction[idx]
            else:
                speed_sample, direction_sample = speed, direction
            rho = _estimate_circular_linear_correlation(speed_sample, direction_sample)
            median_speed, median_kappa, kappa_slope = _estimate_kappa_relationship(
                speed_sample, direction_sample
            )
            speed_median = float(np.median(speed))
            models[(region, level)] = {
                "rho": rho,
                "median_speed": median_speed,
                "speed_median": speed_median,
                "median_kappa": median_kappa,
                "kappa_slope": kappa_slope,
                "n_samples": len(speed),
            }
            elapsed = time.time() - t0
            print(f"    {level}: ρ={rho:.3f}, κ_slope={kappa_slope:.3f}, "
                  f"extreme={'YES' if abs(kappa_slope)>EXTREME_KAPPA_SLOPE else 'no'} "
                  f"({elapsed:.1f}s)")
    return models


def _compute_narrowing_factor(
    speed_pred: float,
    speed_median: float,
    median_kappa: float,
    kappa_slope: float,
    rho: float,
    horizon: int,
) -> float:
    if abs(rho) < 0.05 or abs(kappa_slope) < 0.01:
        return 1.0

    kappa_at_speed = median_kappa + kappa_slope * (speed_pred - speed_median)
    kappa_at_speed = max(kappa_at_speed, 0.5)
    ratio = np.sqrt(median_kappa / kappa_at_speed)

    blend = min(abs(rho) * 2, 1.0)

    damp = HORIZON_DAMPING.get(horizon, 0.5)
    blend *= damp

    factor = 1.0 + blend * (ratio - 1.0)

    if abs(kappa_slope) > EXTREME_KAPPA_SLOPE:
        lo, hi = EXTREME_CLIP
    else:
        lo, hi = NORMAL_CLIP

    return float(np.clip(factor, lo, hi))


def apply_copula_v47(
    preds: pd.DataFrame,
    models: dict,
) -> tuple[pd.DataFrame, dict]:
    out = preds.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)

    stats_report = {
        "total_grid": 0, "adjusted": 0, "narrowed": 0, "widened": 0, "unchanged": 0,
        "by_horizon": {1: {"narrowed": 0, "widened": 0, "unchanged": 0},
                       7: {"narrowed": 0, "widened": 0, "unchanged": 0},
                       14: {"narrowed": 0, "widened": 0, "unchanged": 0}},
    }

    grid_mask = out["type"] == "grid"
    stats_report["total_grid"] = int(grid_mask.sum())

    for (region, level), model in models.items():
        mask = grid_mask & (out["region"] == region) & (out["level"] == level)
        idx = out.index[mask]
        if idx.empty:
            continue

        rho = model["rho"]
        if abs(rho) < 0.05:
            continue

        speed_median = model["speed_median"]
        median_kappa = model["median_kappa"]
        kappa_slope = model["kappa_slope"]

        q50_speed = out.loc[idx, "q50"].values.astype(float)
        d50 = out.loc[idx, "dir_50"].values.astype(float)
        d05 = out.loc[idx, "dir_05"].values.astype(float)
        d95 = out.loc[idx, "dir_95"].values.astype(float)
        horizons = out.loc[idx, "horizon"].values.astype(int)

        old_widths = (d95 - d05) % 360.0

        for i_pos, i in enumerate(idx):
            sp = q50_speed[i_pos]
            h = int(horizons[i_pos])
            if not np.isfinite(sp) or sp <= 0:
                continue

            factor = _compute_narrowing_factor(
                sp, speed_median, median_kappa, kappa_slope, rho, h
            )
            old_hw = old_widths[i_pos] / 2.0
            new_hw = old_hw * factor
            new_hw = np.clip(new_hw, 10, 170)

            center = d50[i_pos]
            out.loc[i, "dir_05"] = (center - new_hw) % 360.0
            out.loc[i, "dir_95"] = (center + new_hw) % 360.0

            stats_report["adjusted"] += 1
            if factor < 0.99:
                stats_report["narrowed"] += 1
                stats_report["by_horizon"][h]["narrowed"] += 1
            elif factor > 1.01:
                stats_report["widened"] += 1
                stats_report["by_horizon"][h]["widened"] += 1
            else:
                stats_report["unchanged"] += 1
                stats_report["by_horizon"][h]["unchanged"] += 1

    return out, stats_report


def run_v47() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("v47: Copula with per-horizon damping + level-aware clips")
    print("=" * 60)
    print(f"  Horizon damping: {HORIZON_DAMPING}")
    print(f"  Extreme κ_slope threshold: {EXTREME_KAPPA_SLOPE}")
    print(f"  Extreme clip: {EXTREME_CLIP}")
    print(f"  Normal clip: {NORMAL_CLIP}")

    print("\nStep 1: Fitting copula models...")
    t0 = time.time()
    models = fit_copula_models()
    print(f"\n  Fitting complete in {time.time()-t0:.1f}s")

    model_serializable = {f"{k[0]}|{k[1]}": v for k, v in models.items()}
    with open(OUT_DIR / "copula_models_v47.json", "w") as f:
        json.dump(model_serializable, f, indent=2)

    print(f"\nStep 2: Loading v41 predictions (base)...")
    preds = pd.read_csv(_phase1_path("predictions_v41.csv"), low_memory=False)
    print(f"  Loaded {len(preds):,} rows")

    print("\nStep 3: Applying damped copula...")
    t0 = time.time()
    adjusted, stats_report = apply_copula_v47(preds, models)
    print(f"  Applied in {time.time()-t0:.1f}s")

    print(f"\n  Grid rows total:     {stats_report['total_grid']:,}")
    print(f"  Direction adjusted:  {stats_report['adjusted']:,}")
    print(f"    Narrowed:          {stats_report['narrowed']:,}")
    print(f"    Widened:           {stats_report['widened']:,}")
    print(f"    Unchanged:         {stats_report['unchanged']:,}")
    print(f"\n  By horizon:")
    for h in [1, 7, 14]:
        bh = stats_report["by_horizon"][h]
        print(f"    d{h:2d}: narrowed={bh['narrowed']:,}, widened={bh['widened']:,}, "
              f"unchanged={bh['unchanged']:,}")

    q_changed = (preds[Q_COLS].reset_index(drop=True) != adjusted[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (preds[DIR_COLS].reset_index(drop=True) != adjusted[DIR_COLS].reset_index(drop=True)).any(axis=1)
    nans = adjusted[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"\n  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  NaNs: {int(nans)}")

    save_submission(adjusted, "v47")
    print("\nDone. v47 generated.")

    with open(OUT_DIR / "stats_report_v47.json", "w") as f:
        json.dump(stats_report, f, indent=2)

    print(f"\n  Compare with v46 stats:")
    v46_report = PROJECT_ROOT / "logs" / "copula_v46" / "stats_report.json"
    if v46_report.exists():
        with open(v46_report) as f:
            old = json.load(f)
        print(f"    v46: narrowed={old['narrowed']:,}, widened={old['widened']:,}")
        print(f"    v47: narrowed={stats_report['narrowed']:,}, widened={stats_report['widened']:,}")
        print(f"    Delta: narrowed {stats_report['narrowed']-old['narrowed']:+,}, "
              f"widened {stats_report['widened']-old['widened']:+,}")


if __name__ == "__main__":
    run_v47()
