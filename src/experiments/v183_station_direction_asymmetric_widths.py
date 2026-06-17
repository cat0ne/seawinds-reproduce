"""v183: station direction asymmetric width-only re-optimizer.

Station direction centers are hard-frozen. This candidate fits station/hour
empirical residual endpoints on replay data and applies only dir_05/dir_95
around the incumbent dir_50. It starts with the biggest safe target,
North Sea station d14, and optionally includes North Sea station d7 only if the
same center-frozen asymmetric calibration clears replay gates.
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

from src.data.paths import LOGS_DIR  # noqa: E402
from src.experiments._direction_breakthrough_utils import (  # noqa: E402
    EVAL_SPLITS,
    build_station_inference,
    build_station_replay,
    score_direction,
    signed_delta,
    summarize_deltas,
)
from src.experiments._next7_utils import (  # noqa: E402
    DIR_COLS,
    diff_checks,
    load_predictions,
    output_dir,
    wrap_360,
    write_json,
    write_submission_with_manifest,
)

VERSION = "v183"
BASE_VERSION = "v173"
REGION = "north_sea"
OUT_DIR = output_dir(VERSION, "station_direction_asymmetric_widths")
HORIZONS = (14, 7)
BLENDS = (0.10, 0.18, 0.25, 0.35, 0.50)
MIN_MEAN_GAIN_CWS = 0.25
MAX_SPLIT_REGRESSION_CWS = 0.0
MIN_SIDE_DEG = 10.0
MAX_SIDE_DEG = 179.0


def fit_endpoint_table(frame: pd.DataFrame) -> pd.DataFrame:
    train = frame[frame["split"].eq("train")].copy()
    train["residual"] = signed_delta(train["actual_direction"], train["base_direction"])
    global_lo = float(np.quantile(train["residual"], 0.05))
    global_hi = float(np.quantile(train["residual"], 0.95))
    rows = []
    for (station, hour), group in train.groupby(["station", "hour"]):
        n = float(len(group))
        lo = float(np.quantile(group["residual"], 0.05))
        hi = float(np.quantile(group["residual"], 0.95))
        # Empirical-Bayes shrinkage toward regional residual endpoints.
        lo = (n * lo + 80.0 * global_lo) / (n + 80.0)
        hi = (n * hi + 80.0 * global_hi) / (n + 80.0)
        rows.append({"station": station, "hour": int(hour), "lo_resid": lo, "hi_resid": hi, "n": int(n)})
    return pd.DataFrame(rows)


def candidate_frame(eval_frame: pd.DataFrame, table: pd.DataFrame, blend: float) -> pd.DataFrame:
    out = eval_frame.merge(table, on=["station", "hour"], how="left")
    fallback_lo = float(table["lo_resid"].median())
    fallback_hi = float(table["hi_resid"].median())
    out["lo_resid"] = out["lo_resid"].fillna(fallback_lo)
    out["hi_resid"] = out["hi_resid"].fillna(fallback_hi)
    old_lo = signed_delta(out["base_dir_05"], out["base_direction"])
    old_hi = signed_delta(out["base_dir_95"], out["base_direction"])
    new_lo = (1.0 - blend) * old_lo + blend * out["lo_resid"].to_numpy(float)
    new_hi = (1.0 - blend) * old_hi + blend * out["hi_resid"].to_numpy(float)
    new_lo = np.clip(new_lo, -MAX_SIDE_DEG, -MIN_SIDE_DEG)
    new_hi = np.clip(new_hi, MIN_SIDE_DEG, MAX_SIDE_DEG)
    out["candidate_dir_50"] = out["base_direction"].to_numpy(float)
    out["candidate_dir_05"] = wrap_360(out["base_direction"].to_numpy(float) + new_lo)
    out["candidate_dir_95"] = wrap_360(out["base_direction"].to_numpy(float) + new_hi)
    return out


def evaluate_horizon(horizon: int) -> tuple[pd.DataFrame, pd.DataFrame, float | None]:
    replay = build_station_replay(horizon)
    replay = replay[replay["region"].eq(REGION)].copy()
    replay = replay.rename(
        columns={"base_direction": "base_direction_raw"}
    )
    # Use the replay center as the reference center; endpoints come from the
    # empirical residual table and are evaluated against actual directions.
    replay["base_direction"] = replay["base_direction_raw"]
    base_width = 90.0
    replay["base_dir_05"] = wrap_360(replay["base_direction"].to_numpy(float) - base_width)
    replay["base_dir_95"] = wrap_360(replay["base_direction"].to_numpy(float) + base_width)
    table = fit_endpoint_table(replay)
    eval_frame = replay[replay["split"].isin(EVAL_SPLITS)].copy()
    rows = []
    for blend in BLENDS:
        cand = candidate_frame(eval_frame, table, blend)
        for split, group in cand.groupby("split"):
            rows.append(
                {
                    "horizon": horizon,
                    "candidate": f"d{horizon}_asym_{blend:.2f}",
                    "blend": blend,
                    "split": split,
                    "rows": int(len(group)),
                    "base_cws": score_direction(group, "base_dir_05", "base_dir_95"),
                    "candidate_cws": score_direction(group, "candidate_dir_05", "candidate_dir_95"),
                }
            )
    report = pd.DataFrame(rows)
    report["delta_cws"] = report["candidate_cws"] - report["base_cws"]
    selected = None
    summary = summarize_deltas(report)
    for row in summary.itertuples(index=False):
        group = report[report["candidate"].eq(row.candidate)]
        if row.mean_delta_cws <= -MIN_MEAN_GAIN_CWS and row.worst_delta_cws <= MAX_SPLIT_REGRESSION_CWS:
            selected = float(group["blend"].iloc[0])
            break
    return report, table, selected


def apply_to_submission(base: pd.DataFrame, selections: dict[int, tuple[pd.DataFrame, float]]) -> tuple[pd.DataFrame, pd.Series]:
    out = base.copy()
    allowed = pd.Series(False, index=base.index)
    for horizon, (table, blend) in selections.items():
        inference = build_station_inference(horizon)
        inference = inference[inference["region"].eq(REGION)].copy()
        inf = inference[["window", "region", "station", "horizon", "hour"]].copy()
        inf = inf.merge(table[["station", "hour", "lo_resid", "hi_resid"]], on=["station", "hour"], how="left")
        inf["lo_resid"] = inf["lo_resid"].fillna(float(table["lo_resid"].median()))
        inf["hi_resid"] = inf["hi_resid"].fillna(float(table["hi_resid"].median()))
        target = out["type"].eq("station") & out["region"].eq(REGION) & out["horizon"].astype(int).eq(horizon)
        current = out.loc[target, ["window", "region", "station", "horizon", "hour"] + DIR_COLS].copy()
        merged = current.reset_index().merge(inf, on=["window", "region", "station", "horizon", "hour"], how="inner")
        if len(merged) != int(target.sum()):
            raise RuntimeError(f"d{horizon} merge mismatch: {len(merged)} vs {int(target.sum())}")
        old_lo = signed_delta(merged["dir_05"], merged["dir_50"])
        old_hi = signed_delta(merged["dir_95"], merged["dir_50"])
        lo = np.clip((1.0 - blend) * old_lo + blend * merged["lo_resid"].to_numpy(float), -MAX_SIDE_DEG, -MIN_SIDE_DEG)
        hi = np.clip((1.0 - blend) * old_hi + blend * merged["hi_resid"].to_numpy(float), MIN_SIDE_DEG, MAX_SIDE_DEG)
        idx = merged["index"].to_numpy(int)
        center = merged["dir_50"].to_numpy(float)
        out.loc[idx, "dir_05"] = np.round(wrap_360(center + lo), 1)
        out.loc[idx, "dir_95"] = np.round(wrap_360(center + hi), 1)
        allowed |= target
    return out, allowed


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    selections: dict[int, tuple[pd.DataFrame, float]] = {}
    selected_manifest: dict[str, float] = {}
    for horizon in HORIZONS:
        report, table, blend = evaluate_horizon(horizon)
        reports.append(report)
        report.to_csv(OUT_DIR / f"d{horizon}_split_report.csv", index=False)
        table.to_csv(OUT_DIR / f"d{horizon}_endpoint_table.csv", index=False)
        if blend is not None:
            # d14 is primary. d7 is allowed only if it independently clears.
            selections[horizon] = (table, blend)
            selected_manifest[f"d{horizon}"] = blend
    report_all = pd.concat(reports, ignore_index=True)
    report_all.to_csv(OUT_DIR / "split_report.csv", index=False)
    summarize_deltas(report_all).to_csv(OUT_DIR / "candidate_summary.csv", index=False)

    manifest = {
        "target_dimension": "dir_stations_d14_ns_then_d7_ns",
        "selected": selected_manifest,
        "center_moved": False,
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    if 14 not in selections:
        manifest["decision"] = "REJECT_NO_ZIP_D14_GATE_FAILED"
        write_json(OUT_DIR / "manifest.json", {"version": VERSION, "base_version": BASE_VERSION, **manifest})
        print(json.dumps(manifest, indent=2))
        return 2

    base = load_predictions(BASE_VERSION)
    candidate, allowed_dir = apply_to_submission(base, selections)
    checks = diff_checks(base, candidate, allowed_q=pd.Series(False, index=base.index), allowed_dir=allowed_dir, forbid_dir50_change=True)
    manifest.update({"decision": "PROMOTE_CANDIDATE", "checks": checks})
    zip_path = write_submission_with_manifest(
        version=VERSION,
        base_version=BASE_VERSION,
        candidate=candidate,
        manifest_dir=OUT_DIR,
        manifest=manifest,
    )
    print(f"Wrote {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
