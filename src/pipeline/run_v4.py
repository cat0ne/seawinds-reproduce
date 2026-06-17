"""V4: Cherry-pick baseline speed + LightGBM direction overlay.

Takes predictions_light.csv (baseline speed) and replaces all direction
columns with predictions from the pooled LightGBM sin/cos direction model
trained in generate_v3_submission.py.

Result: baseline speed quality + direction model quality.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission

PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"


def build_v4() -> Path:
    t0 = time.time()
    print("[v4] Loading light baseline ...")
    light = pd.read_csv(PHASE1 / "predictions_light.csv", low_memory=False)

    print("[v4] Loading v3 predictions (direction source) ...")
    v3 = pd.read_csv(PHASE1 / "predictions_v3.csv", low_memory=False)

    merge_keys = ["type", "window", "region", "latitude", "longitude",
                  "station", "horizon", "hour", "level"]

    for col in merge_keys:
        if col in light.columns:
            light[col] = light[col].astype(str)
            v3[col] = v3[col].astype(str)

    dir_cols = ["dir_05", "dir_50", "dir_95"]
    v3_dir = v3[merge_keys + dir_cols].copy()

    merged = light.merge(v3_dir, on=merge_keys, how="left",
                         suffixes=("_light", "_v3"))
    for col in dir_cols:
        v3_vals = merged[f"{col}_v3"]
        merged[col] = v3_vals.fillna(merged[f"{col}_light"])
        merged = merged.drop(columns=[f"{col}_light", f"{col}_v3"])

    for col in merge_keys:
        if col in merged.columns:
            if col in ("latitude", "longitude", "horizon", "hour"):
                merged[col] = merged[col].astype(float)

    q_cols = ["q05", "q50", "q95"]
    for col in q_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    for col in dir_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    q = merged[q_cols].values.astype(float)
    q = np.sort(q, axis=1)
    merged["q05"] = np.maximum(q[:, 0], 0)
    merged["q50"] = q[:, 1]
    merged["q95"] = q[:, 2]

    out = save_submission(merged, "v4")
    print(f"[v4] Done in {time.time() - t0:.1f}s  →  {out}")
    return out


if __name__ == "__main__":
    build_v4()
