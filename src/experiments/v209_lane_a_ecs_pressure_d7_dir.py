"""v209: Lane A pilot — von Mises kappa-MLE direction widths on ECS pressure d7.

Pilot scope:
  type=grid, region=east_china_sea, level in {1000, 925, 850, 700, 500},
  horizon=7, hour in {0,6,12,18}. 20 cells total.

Base: v207 (current best compound; preserves v191's -1.18 cWS gain on this cell).
Frozen: q-columns, dir_50. Only dir_05 / dir_95 may move on accepted rows.

Mechanism per (level, hour):
  - Pool TRAIN rows (2019-01..2020-09) of HRES vs reanalysis for the cell.
  - Bin by HRES forecast speed (6 quantile bins; coarsen to >= 3 if needed).
  - Fit von Mises kappa via the R-bar MLE per bin.
  - Fit isotonic regression: speed midpoint -> kappa (monotone increasing).
  - At inference, lookup kappa from HRES forecast speed and translate to a
    half-width via scipy.stats.vonmises.ppf(0.95, kappa).

Regime gate (per row):
  - candidate_hw within [0.70, 1.50] of v207_hw
  - |candidate_hw - v207_hw| > 2 deg
  - speed_rank (within (level, hour)) > 0.15
  - dir_50 not in wrap zone (min(dir_50, 360-dir_50) > 30 deg)
  - finite candidate kappa & speed >= 5 m/s absolute floor
  - candidate_hw within [5, 175] deg
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import (  # noqa: E402
    FEATURES_DIR,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    PROJECT_ROOT,
    TRAIN_DIR,
    TRAIN_END,
    TRAIN_START,
)
from src.experiments._lane_a_vm_utils import (  # noqa: E402
    RegimeGate,
    VonMisesKappaEstimator,
    apply_vm_width_response,
    signed_delta,
    vm_hw_fast,
)
from src.experiments._next7_utils import (  # noqa: E402
    diff_checks,
    load_predictions,
    output_dir,
    write_submission_with_manifest,
)

VERSION = "v209"
BASE_VERSION = "v207"
REGION = "east_china_sea"
HORIZON = 7
TARGET_LEVELS = [str(level) for level in PRESSURE_LEVELS]
OUT_DIR = output_dir(VERSION, "lane_a_ecs_pressure_d7_dir")

# Auto-ship sanity gates (held by manifest, not Winkler):
GATE_MIN_ACTIVATION = 0.05    # 5% rows
GATE_MAX_ACTIVATION = 0.95    # 95% rows
GATE_MIN_MEAN_MOVEMENT_DEG = 1.0
GATE_MAX_MEAN_MOVEMENT_DEG = 30.0
GATE_HW_FLOOR_DEG = 5.0
GATE_HW_CEILING_DEG = 175.0


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("grid")
        & frame["region"].eq(REGION)
        & frame["horizon"].astype(int).eq(HORIZON)
        & ~frame["level"].astype(str).isin(["10m", "100m"])
    )


def fit_kappa_per_cell() -> dict[tuple[str, int], VonMisesKappaEstimator]:
    """Fit one VonMisesKappaEstimator per (level, hour). 20 cells for ECS d7."""
    print(f"  Loading reanalysis truth ({REGION})...")
    truth_cols = ["time", "latitude", "longitude"] + [c for level in TARGET_LEVELS for c in (f"u_{level}", f"v_{level}")]
    truth = pd.read_parquet(TRAIN_DIR / f"reanalysis_pressure_{REGION}.parquet", columns=truth_cols)
    truth["time"] = pd.to_datetime(truth["time"])
    truth["latitude"] = truth["latitude"].astype(float).round(2)
    truth["longitude"] = truth["longitude"].astype(float).round(2)
    truth = truth.rename(columns={"time": "target_time"})

    estimators: dict[tuple[str, int], VonMisesKappaEstimator] = {}
    cell_diagnostics: dict[str, dict] = {}

    for hour in HOURS:
        # Load all 5 levels' u/v for d7/hHOUR at once (joint over all init times).
        cols_for_hour = ["time", "latitude", "longitude"]
        for level in TARGET_LEVELS:
            cols_for_hour.append(f"fcst_u_{level}_d{HORIZON}_h{hour}")
            cols_for_hour.append(f"fcst_v_{level}_d{HORIZON}_h{hour}")
        print(f"\n  [hour={hour}] Loading HRES forecast...")
        hres = pd.read_parquet(TRAIN_DIR / f"hres_pressure_{REGION}.parquet", columns=cols_for_hour)
        hres["time"] = pd.to_datetime(hres["time"])
        hres["latitude"] = hres["latitude"].astype(float).round(2)
        hres["longitude"] = hres["longitude"].astype(float).round(2)
        train_mask = (hres["time"] >= TRAIN_START) & (hres["time"] <= TRAIN_END)
        hres = hres.loc[train_mask].copy()
        hres["target_time"] = hres["time"] + pd.Timedelta(days=HORIZON, hours=hour)
        merged = hres.merge(
            truth,
            on=["target_time", "latitude", "longitude"],
            how="inner",
        )
        print(f"    merged rows: {len(merged):,}")

        for level in TARGET_LEVELS:
            u_f = merged[f"fcst_u_{level}_d{HORIZON}_h{hour}"].astype(float).to_numpy()
            v_f = merged[f"fcst_v_{level}_d{HORIZON}_h{hour}"].astype(float).to_numpy()
            u_o = merged[f"u_{level}"].astype(float).to_numpy()
            v_o = merged[f"v_{level}"].astype(float).to_numpy()
            speed_fcst = np.sqrt(u_f * u_f + v_f * v_f)
            dir_fcst = (270.0 - np.degrees(np.arctan2(v_f, u_f))) % 360.0
            dir_obs = (270.0 - np.degrees(np.arctan2(v_o, u_o))) % 360.0
            residual = signed_delta(dir_obs, dir_fcst)

            est = VonMisesKappaEstimator(n_bins=6, min_obs_per_bin=200, min_bins=3)
            est.fit(speed_fcst, residual)
            estimators[(level, int(hour))] = est
            cell_key = f"{level}|h{hour}"
            cell_diagnostics[cell_key] = {
                "n_train": est.n_train,
                "fit_status": est.fit_status,
                "global_kappa": est.global_kappa,
                "bin_midpoints": [float(x) for x in est.bin_midpoints],
                "bin_kappas": [float(x) for x in est.bin_kappas],
                "bin_hw_deg": [float(x) for x in vm_hw_fast(est.bin_kappas)],
                "bin_counts": [int(x) for x in est.bin_counts],
                "residual_std_deg": float(np.nanstd(residual)),
                "residual_mean_deg": float(np.nanmean(residual)),
                "speed_mean": float(np.nanmean(speed_fcst)),
            }
            print(
                f"    cell={level:>4s} h{hour}: n={est.n_train:,} status={est.fit_status} "
                f"global_k={est.global_kappa:.3f} "
                f"bin_k=[{', '.join(f'{k:.2f}' for k in est.bin_kappas)}] "
                f"bin_hw=[{', '.join(f'{h:.1f}' for h in vm_hw_fast(est.bin_kappas))}]"
            )
        del hres, merged
    return estimators, cell_diagnostics


def load_inference_speed_by_row(base: pd.DataFrame) -> np.ndarray:
    """Build per-row HRES forecast speed array aligned to base order.

    Only rows in the target scope receive a finite value; everything else NaN.
    """
    target = target_mask(base)
    out = np.full(len(base), np.nan, dtype=float)

    # Group by (window, level, hour) and merge in HRES speed.
    sub = base.loc[target, ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]].copy()
    sub["latitude"] = sub["latitude"].astype(float).round(2)
    sub["longitude"] = sub["longitude"].astype(float).round(2)
    sub["row_idx"] = sub.index.to_numpy()

    for window in sorted(sub["window"].unique()):
        win_sub = sub[sub["window"] == int(window)]
        if win_sub.empty:
            continue
        inf_path = FEATURES_DIR / f"inference_window_{int(window)}_{REGION}.parquet"
        # Load only u/v cols we need for d7 (all 5 levels x 4 hours = 40 cols + 3 keys)
        wanted = ["latitude", "longitude"]
        for level in TARGET_LEVELS:
            for hour in HOURS:
                wanted.append(f"fcst_u_{level}_d{HORIZON}_h{hour}")
                wanted.append(f"fcst_v_{level}_d{HORIZON}_h{hour}")
        inf = pd.read_parquet(inf_path, columns=wanted)
        inf["latitude"] = inf["latitude"].astype(float).round(2)
        inf["longitude"] = inf["longitude"].astype(float).round(2)

        # Per (level, hour) build speed column then merge to win_sub.
        for level in TARGET_LEVELS:
            for hour in HOURS:
                cell_sub = win_sub[
                    (win_sub["level"].astype(str) == level)
                    & (win_sub["hour"].astype(int) == int(hour))
                ]
                if cell_sub.empty:
                    continue
                u = inf[f"fcst_u_{level}_d{HORIZON}_h{hour}"].astype(float).to_numpy()
                v = inf[f"fcst_v_{level}_d{HORIZON}_h{hour}"].astype(float).to_numpy()
                spd = np.sqrt(u * u + v * v)
                spd_df = pd.DataFrame({
                    "latitude": inf["latitude"].to_numpy(),
                    "longitude": inf["longitude"].to_numpy(),
                    "speed": spd,
                })
                merged = cell_sub[["row_idx", "latitude", "longitude"]].merge(
                    spd_df, on=["latitude", "longitude"], how="left", validate="one_to_one",
                )
                if merged["speed"].isna().any():
                    n_missing = int(merged["speed"].isna().sum())
                    raise RuntimeError(
                        f"HRES speed missing for window={window} level={level} hour={hour}: {n_missing}"
                    )
                out[merged["row_idx"].to_numpy()] = merged["speed"].to_numpy()
        del inf

    n_target = int(target.sum())
    n_filled = int(np.isfinite(out[target.values]).sum())
    if n_filled != n_target:
        raise RuntimeError(f"Speed missing for some target rows: filled {n_filled}/{n_target}")
    return out


def compare_to_v191(candidate: pd.DataFrame, base: pd.DataFrame, target: pd.Series) -> dict:
    """Compare candidate (v209) widths to v191 widths on the same target rows."""
    v191 = load_predictions("v191")
    if not (len(v191) == len(base) and len(candidate) == len(base)):
        raise RuntimeError("v191 / base / candidate row counts disagree")
    idx = base.index[target]
    hw_v191 = ((v191.loc[idx, "dir_95"].astype(float).to_numpy()
                - v191.loc[idx, "dir_05"].astype(float).to_numpy()) % 360.0) / 2.0
    hw_v207 = ((base.loc[idx, "dir_95"].astype(float).to_numpy()
                - base.loc[idx, "dir_05"].astype(float).to_numpy()) % 360.0) / 2.0
    hw_v209 = ((candidate.loc[idx, "dir_95"].astype(float).to_numpy()
                - candidate.loc[idx, "dir_05"].astype(float).to_numpy()) % 360.0) / 2.0
    return {
        "n_target_rows": int(len(idx)),
        "v191_hw_mean": float(np.mean(hw_v191)),
        "v207_hw_mean": float(np.mean(hw_v207)),
        "v209_hw_mean": float(np.mean(hw_v209)),
        "v209_minus_v191_hw_mean": float(np.mean(hw_v209 - hw_v191)),
        "v209_minus_v207_hw_mean": float(np.mean(hw_v209 - hw_v207)),
        "frac_rows_differ_from_v191": float(np.mean(np.abs(hw_v209 - hw_v191) > 0.05)),
        "frac_rows_differ_from_v207": float(np.mean(np.abs(hw_v209 - hw_v207) > 0.05)),
    }


def evaluate_ship_gates(stats: dict, comparison: dict) -> dict:
    """Decide whether to ship the submission zip based on local sanity gates."""
    activation = stats["activation_rate"]
    mean_move = stats["movement_deg_on_changed"]["mean"]
    candidate_mean_hw = stats["candidate_hw_deg"]["mean_all_valid"]
    reasons = []
    if activation < GATE_MIN_ACTIVATION:
        reasons.append(f"activation_rate {activation:.4f} < {GATE_MIN_ACTIVATION}")
    if activation > GATE_MAX_ACTIVATION:
        reasons.append(f"activation_rate {activation:.4f} > {GATE_MAX_ACTIVATION}")
    if mean_move < GATE_MIN_MEAN_MOVEMENT_DEG:
        reasons.append(f"mean movement {mean_move:.2f} < {GATE_MIN_MEAN_MOVEMENT_DEG}")
    if mean_move > GATE_MAX_MEAN_MOVEMENT_DEG:
        reasons.append(f"mean movement {mean_move:.2f} > {GATE_MAX_MEAN_MOVEMENT_DEG}")
    if candidate_mean_hw is not None and (candidate_mean_hw < GATE_HW_FLOOR_DEG or candidate_mean_hw > GATE_HW_CEILING_DEG):
        reasons.append(f"candidate_mean_hw {candidate_mean_hw:.2f} outside [{GATE_HW_FLOOR_DEG},{GATE_HW_CEILING_DEG}]")
    return {
        "ship": len(reasons) == 0,
        "reasons_to_hold": reasons,
        "gates": {
            "min_activation": GATE_MIN_ACTIVATION,
            "max_activation": GATE_MAX_ACTIVATION,
            "min_mean_movement_deg": GATE_MIN_MEAN_MOVEMENT_DEG,
            "max_mean_movement_deg": GATE_MAX_MEAN_MOVEMENT_DEG,
            "hw_floor_deg": GATE_HW_FLOOR_DEG,
            "hw_ceiling_deg": GATE_HW_CEILING_DEG,
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print(f"{VERSION.upper()}: Lane A pilot — von Mises kappa-MLE, ECS pressure d7 direction")
    print(f"Base: {BASE_VERSION}  Region: {REGION}  Horizon: d{HORIZON}")
    print("=" * 72)

    print(f"\n[1/4] Fitting kappa per cell (TRAIN: {TRAIN_START} .. {TRAIN_END})")
    t0 = time.time()
    estimators, cell_diagnostics = fit_kappa_per_cell()
    print(f"  Fit {len(estimators)} cells in {(time.time() - t0)/60:.1f} min")

    print(f"\n[2/4] Loading base predictions ({BASE_VERSION})")
    base = load_predictions(BASE_VERSION)
    print(f"  Base rows: {len(base):,}")
    target = target_mask(base)
    print(f"  Target rows: {int(target.sum()):,}")

    print("\n[3/4] Building per-row HRES forecast speed for inference scope")
    speed_by_row = load_inference_speed_by_row(base)
    n_target = int(target.sum())
    target_speeds = speed_by_row[target.values]
    print(
        f"  HRES speed on target: mean={np.nanmean(target_speeds):.2f}, "
        f"median={np.nanmedian(target_speeds):.2f}, "
        f"min={np.nanmin(target_speeds):.2f}, max={np.nanmax(target_speeds):.2f}"
    )

    print("\n[4/4] Applying VM width response under regime gate")
    candidate, allowed_dir, stats = apply_vm_width_response(
        base,
        target,
        speed_by_row=speed_by_row,
        kappa_by_cell=estimators,
        regime=RegimeGate(
            hw_ratio_lo=0.70,
            hw_ratio_hi=1.50,
            min_movement_deg=2.0,
            speed_rank_floor=0.15,
            wrap_zone_deg=30.0,
        ),
        speed_floor_value=5.0,
        halfwidth_floor=5.0,
        halfwidth_ceiling=175.0,
    )
    print(f"  Changed rows: {stats['changed_rows']:,} / {stats['target_rows']:,} "
          f"({stats['activation_rate']*100:.2f}%)")
    print(f"  Mean movement on changed: {stats['movement_deg_on_changed']['mean']:.2f} deg")
    print(f"  Frac widened (vs v207): {stats['frac_widened_rows']*100:.2f}%")
    print(f"  Gate failures: {stats['gate_failure_counts']}")

    # Scope checks: forbid any q or non-target dir changes; dir_50 frozen.
    checks = diff_checks(
        base,
        candidate,
        allowed_q=pd.Series(False, index=base.index),
        allowed_dir=allowed_dir,
        forbid_q50_change=True,
        forbid_dir50_change=True,
    )

    # Comparison to v191 on same rows.
    comparison = compare_to_v191(candidate, base, target)
    print("\n  vs v191/v207 (on target rows):")
    for k, v in comparison.items():
        print(f"    {k}: {v}")

    # Ship decision.
    decision = evaluate_ship_gates(stats, comparison)

    manifest = {
        "target_dimension": "dir_pressure_d7_ecs",
        "scope": f"grid/{REGION}/pressure/d{HORIZON}/direction_endpoints_only",
        "mechanism": (
            "Per-(level,hour) von Mises kappa-MLE: bin TRAIN residuals "
            "(actual-HRES) by HRES speed, fit kappa per bin, monotone "
            "(isotonic) speed->kappa, half-width = vonmises.ppf(0.95, kappa). "
            "Regime gate filters extreme/calm/wrap rows back to v207."
        ),
        "speed_scale_choice": "HRES forecast speed at both training and inference (consistent scale)",
        "cell_diagnostics": cell_diagnostics,
        "application_stats": stats,
        "comparison_vs_v191": comparison,
        "diff_checks": checks,
        "decision": decision,
        "wrote_submission": decision["ship"],
    }

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float) + "\n",
                                            encoding="utf-8")
    print(f"\nDecision: ship={decision['ship']}")
    if not decision["ship"]:
        print(f"  Reasons to hold: {decision['reasons_to_hold']}")
        print(f"  Manifest only: {OUT_DIR / 'manifest.json'}")
        return 0

    zip_path = write_submission_with_manifest(
        version=VERSION,
        base_version=BASE_VERSION,
        candidate=candidate,
        manifest_dir=OUT_DIR,
        manifest=manifest,
    )
    print(f"  SHIPPED: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
