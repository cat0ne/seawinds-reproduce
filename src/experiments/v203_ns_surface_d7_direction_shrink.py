"""v203: NS surface d7 direction width — extend v191 mechanism to surface.

dir_surface_d7_ns: rank 3, gap +8.89 cWS to the leader (276.92 vs our 285.81).
Median halfwidth = 129.6deg (very wide), p90 = 129.8 (saturated/uniform).

v191 mechanism on pressure d7 cells worked; v198 confirmed it transfers to NS
pressure. This is the first attempt on a SURFACE cell. Same speed-conditioned
circular concentration response, applied only to surface (10m + 100m) levels.

Risk: surface intervals are already saturated at 129deg (a single CQR width
applied broadly). Like v204 stations d14 ns, this means the "level percentile"
ranking won't have variation — the mechanism may fire uniformly. Different from
pressure where halfwidth varies within a level.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments._next7_utils import diff_checks, load_predictions, output_dir, write_submission_with_manifest  # noqa: E402
from src.experiments._post_v185_utils import apply_center_frozen_direction_width_response  # noqa: E402

VERSION = "v203"
BASE_VERSION = "v173"
OUT_DIR = output_dir(VERSION, "ns_surface_d7_direction_shrink")


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("grid")
        & frame["region"].eq("north_sea")
        & frame["horizon"].astype(int).eq(7)
        & frame["level"].astype(str).isin(["10m", "100m"])
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_predictions(BASE_VERSION)
    target = target_mask(base)
    candidate, allowed_dir, stats = apply_center_frozen_direction_width_response(
        base,
        target,
        max_shrink_deg=14.0,
        min_halfwidth_deg=28.0,
        speed_floor=0.15,
        halfwidth_floor=0.05,
        level_weights={"10m": 1.00, "100m": 1.00},
    )
    checks = diff_checks(
        base,
        candidate,
        allowed_q=pd.Series(False, index=base.index),
        allowed_dir=allowed_dir,
        forbid_q50_change=True,
        forbid_dir50_change=True,
    )
    manifest = {
        "target_dimension": "dir_surface_d7_ns",
        "scope": "grid/north_sea/surface/d7/direction_endpoints_only",
        "mechanism": "speed-conditioned circular concentration response (v191 mirror, surface levels); dir_50 frozen",
        "stats": stats,
        "checks": checks,
        "wrote_submission": True,
    }
    zip_path = write_submission_with_manifest(
        version=VERSION,
        base_version=BASE_VERSION,
        candidate=candidate,
        manifest_dir=OUT_DIR,
        manifest=manifest,
    )
    print(json.dumps({**manifest, "zip_path": str(zip_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
