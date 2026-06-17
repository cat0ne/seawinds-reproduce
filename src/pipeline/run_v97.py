"""Build submission v97: gated Track I d7 NS station direction on v88 base.

Scope: ONLY north_sea station rows at horizon=7, direction columns.
All other rows (speed, other horizons, other regions, grid) are identical to v88.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    HOURS,
    LOGS_DIR,
    PROJECT_ROOT,
)

PHASE1_DIR = PROJECT_ROOT / "starting-kit" / "phase_1"
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"
from src.experiments.direction_error_atlas import build_inference_station_frame
from src.experiments.track_i_d7_ns_v88 import V38ResidualDirectionModel
from src.scoring.winkler import _circ_dist

MODEL_PATH = LOGS_DIR / "track_i_d7_ns_v88" / "d7_ns_model.pkl"
BASE_PREDICTIONS = PHASE1_DIR / "predictions_v88.csv"
OUTPUT_CSV = PHASE1_DIR / "predictions_v97.csv"
OUTPUT_ZIP = SUBMISSIONS_DIR / "submission_v97.zip"
MANIFEST_DIR = LOGS_DIR / "v97_gated_track_i_d7_ns"
GATE_THRESHOLD = 15.0


def _circ_dist_series(actual: pd.Series, predicted: pd.Series) -> pd.Series:
    """Element-wise circular distance in degrees, 0-180."""
    delta = ((actual - predicted + 180.0) % 360.0) - 180.0
    return delta.abs()


def build_submission() -> pd.DataFrame:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if not BASE_PREDICTIONS.exists():
        raise FileNotFoundError(f"Base predictions not found: {BASE_PREDICTIONS}")

    print("Loading v88 base predictions ...")
    base = pd.read_csv(BASE_PREDICTIONS, low_memory=False)

    region = "north_sea"
    horizon = 7

    print("Training Track I model ...")
    from src.experiments.direction_error_atlas import build_station_direction_frame
    train = build_station_direction_frame(region, horizon, "train")
    model = V38ResidualDirectionModel()
    model.fit(train)

    print(f"Building inference predictions for {region} horizon={horizon} ...")
    cand_rows: list[pd.DataFrame] = []
    for window in range(1, 9):
        frame = build_inference_station_frame(region, horizon, window)
        if frame.empty:
            continue
        pred = model.predict(frame)
        keys = frame[["window", "region", "station", "horizon", "hour"]].reset_index(drop=True)
        cand = pd.concat([keys, pred[["dir_05", "dir_50", "dir_95"]].reset_index(drop=True)], axis=1)
        cand_rows.append(cand)

    if not cand_rows:
        raise ValueError("No inference predictions generated")

    candidate = pd.concat(cand_rows, ignore_index=True)
    candidate["window"] = candidate["window"].astype(int)
    candidate["horizon"] = candidate["horizon"].astype(int)
    candidate["hour"] = candidate["hour"].astype(int)

    # Merge candidate onto base to compute gate
    print("Applying gate ...")
    # For station rows, level is NaN in base; match on window, region, station, horizon, hour
    merged = base.merge(
        candidate.rename(columns={
            "dir_05": "cand_dir_05",
            "dir_50": "cand_dir_50",
            "dir_95": "cand_dir_95",
        }),
        on=["window", "region", "station", "horizon", "hour"],
        how="left",
    )

    # Compute center shift for candidate rows
    merged["center_shift"] = _circ_dist_series(merged["dir_50"], merged["cand_dir_50"])

    # Apply gate: accept if shift <= 15° and candidate values are valid
    accept_mask = (
        merged["center_shift"].notna()
        & (merged["center_shift"] <= GATE_THRESHOLD)
        & merged["cand_dir_05"].notna()
        & merged["cand_dir_50"].notna()
        & merged["cand_dir_95"].notna()
    )

    accepted = int(accept_mask.sum())
    rejected = int(merged["center_shift"].notna().sum()) - accepted
    print(f"  Gate threshold: {GATE_THRESHOLD}°")
    print(f"  Candidate rows: {len(candidate)}")
    print(f"  Accepted: {accepted}")
    print(f"  Rejected: {rejected}")

    # Overwrite accepted rows
    merged.loc[accept_mask, "dir_05"] = merged.loc[accept_mask, "cand_dir_05"]
    merged.loc[accept_mask, "dir_50"] = merged.loc[accept_mask, "cand_dir_50"]
    merged.loc[accept_mask, "dir_95"] = merged.loc[accept_mask, "cand_dir_95"]

    # Drop candidate columns
    merged = merged.drop(columns=["cand_dir_05", "cand_dir_50", "cand_dir_95", "center_shift"])

    # Sort to original order (base was already in correct order)
    return merged


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_submission() -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    out = build_submission()
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote predictions: {OUTPUT_CSV}")

    # Verify no NaNs in prediction columns
    pred_cols = ["q05", "q50", "q95", "dir_05", "dir_50", "dir_95"]
    for col in pred_cols:
        nans = out[col].isna().sum()
        if nans > 0:
            raise ValueError(f"NaN values in {col}: {nans}")

    # Verify no quantile crossings for grid rows
    grid = out[out["type"] == "grid"]
    crossings = ((grid["q05"] > grid["q50"]) | (grid["q50"] > grid["q95"])).sum()
    if crossings > 0:
        raise ValueError(f"Quantile crossings in grid rows: {crossings}")

    # Create zip
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUTPUT_CSV, arcname="predictions.csv")
    print(f"Wrote zip: {OUTPUT_ZIP}")

    # Scope stats
    base = pd.read_csv(BASE_PREDICTIONS, low_memory=False)
    changed_speed = (
        (out["q05"] != base["q05"])
        | (out["q50"] != base["q50"])
        | (out["q95"] != base["q95"])
    ).sum()
    changed_dir = (
        (out["dir_05"] != base["dir_05"])
        | (out["dir_50"] != base["dir_50"])
        | (out["dir_95"] != base["dir_95"])
    ).sum()

    manifest = {
        "version": "v97",
        "base_version": "v88",
        "base_file": str(BASE_PREDICTIONS),
        "base_sha256": _sha256(BASE_PREDICTIONS),
        "output_file": str(OUTPUT_CSV),
        "output_sha256": _sha256(OUTPUT_CSV),
        "zip_file": str(OUTPUT_ZIP),
        "scope": "station/north_sea/d7/gated_track_i_direction",
        "rows": len(out),
        "changed_speed_rows": int(changed_speed),
        "changed_direction_rows": int(changed_dir),
        "gate_threshold_degrees": GATE_THRESHOLD,
        "nan_prediction_values": 0,
    }
    manifest_path = MANIFEST_DIR / "v97_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote manifest: {manifest_path}")

    print(f"\nScope verification:")
    print(f"  Total rows: {len(out):,}")
    print(f"  Changed speed rows: {changed_speed:,}")
    print(f"  Changed direction rows: {changed_dir:,}")
    print(f"  Expected changed direction rows: <= 256 (8 stations × 4 hours × 8 windows)")

    return OUTPUT_ZIP


def main() -> int:
    write_submission()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
