"""V6: V4 base + log-wind profile height correction for non-10m stations.

Stations at heights other than 10m get a physically-motivated speed
adjustment via the log-wind profile:
    speed(z) = speed(10m) × ln(z/z0) / ln(10/z0)
where z0 = 0.03m (offshore roughness length).

Correction ratios:
  NS_01 (102m)  ×1.400
  NS_02 (14m)   ×1.058
  ECS_01 (42.3m) ×1.248
  ECS_06 (3m)    ×0.793
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
from src.pipeline.pipeline_utils import apply_height_correction, save_submission

PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"


def build_v6() -> Path:
    t0 = time.time()
    print("[v6] Loading v4 predictions ...")
    df = pd.read_csv(PHASE1 / "predictions_v4.csv", low_memory=False)

    station_mask = df["type"] == "station"
    stations = df.loc[station_mask].copy()
    stations = apply_height_correction(stations)
    df.loc[station_mask] = stations

    out = save_submission(df, "v6")
    print(f"[v6] Done in {time.time() - t0:.1f}s  →  {out}")
    return out


if __name__ == "__main__":
    build_v6()
