"""v191: ECS pressure d7 speed-conditioned direction-width response.

The public board now shows a much stronger ECS pressure d7 direction score.
This candidate does not move centers. It applies a von-Mises-inspired
concentration response: high-speed, over-wide ECS pressure d7 rows get narrower
direction intervals while low-speed rows are left untouched.
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

VERSION = "v191"
BASE_VERSION = "v173"
OUT_DIR = output_dir(VERSION, "ecs_pressure_d7_direction_response")


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
    target = target_mask(base)
    candidate, allowed_dir, stats = apply_center_frozen_direction_width_response(
        base,
        target,
        max_shrink_deg=14.0,
        min_halfwidth_deg=28.0,
        speed_floor=0.15,
        halfwidth_floor=0.05,
        level_weights={"500": 0.75, "700": 0.90, "850": 1.00, "925": 1.00, "1000": 1.00},
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
        "target_dimension": "dir_pressure_d7_ecs",
        "scope": "grid/east_china_sea/pressure/d7/direction_endpoints_only",
        "mechanism": "speed-conditioned circular concentration response; dir_50 frozen",
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
