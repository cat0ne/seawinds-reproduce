"""v196: mild-plus bracket for the v191 ECS pressure d7 direction response.

v191 validated a center-frozen concentration response on ECS pressure d7. This
candidate keeps the same mechanism and target, but nudges the amplitude upward
modestly instead of jumping to an aggressive shrink:

- same target: grid / east_china_sea / pressure / d7 / direction endpoints
- same frozen center: no ``dir_50`` movement
- same speed columns: no q05/q50/q95 movement
- bracket: max shrink 14 -> 17 degrees, minimum halfwidth 28 -> 27 degrees

It is built from v173 as a standalone parameter bracket and compared against
both v173 and promoted v191 in the manifest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments._next7_utils import diff_checks, load_predictions, output_dir, write_submission_with_manifest  # noqa: E402
from src.experiments._post_v185_utils import apply_center_frozen_direction_width_response  # noqa: E402

VERSION = "v196"
BASE_VERSION = "v173"
PROMOTED_BASE_VERSION = "v191"
OUT_DIR = output_dir(VERSION, "ecs_pressure_d7_direction_mild_plus")


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("grid")
        & frame["region"].eq("east_china_sea")
        & frame["horizon"].astype(int).eq(7)
        & ~frame["level"].astype(str).isin(["10m", "100m"])
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_predictions(BASE_VERSION)
    promoted = load_predictions(PROMOTED_BASE_VERSION)
    target = target_mask(base)
    candidate, allowed_dir, stats = apply_center_frozen_direction_width_response(
        base,
        target,
        max_shrink_deg=17.0,
        min_halfwidth_deg=27.0,
        speed_floor=0.15,
        halfwidth_floor=0.05,
        level_weights={"500": 0.75, "700": 0.90, "850": 1.00, "925": 1.00, "1000": 1.00},
    )
    checks_vs_base = diff_checks(
        base,
        candidate,
        allowed_q=pd.Series(False, index=base.index),
        allowed_dir=allowed_dir,
        forbid_q50_change=True,
        forbid_dir50_change=True,
    )
    checks_vs_v191 = diff_checks(
        promoted,
        candidate,
        allowed_q=pd.Series(False, index=base.index),
        allowed_dir=target,
        forbid_q50_change=True,
        forbid_dir50_change=True,
    )
    manifest = {
        "target_dimension": "dir_pressure_d7_ecs",
        "scope": "grid/east_china_sea/pressure/d7/direction_endpoints_only",
        "mechanism": "mild-plus bracket of v191 speed-conditioned circular concentration; dir_50 frozen",
        "compare_to_promoted_base": PROMOTED_BASE_VERSION,
        "stats": stats,
        "checks": checks_vs_base,
        "checks_vs_promoted_base": checks_vs_v191,
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
