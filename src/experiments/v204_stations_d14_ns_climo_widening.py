"""v204: Lane D station climatology width blend on dir_stations_d14_ns.

NS d14 station direction is rank-5 of our 36-dim atlas, with a +9.94 cWS gap
to Breva (305.63 vs 295.69). The model halfwidths are very wide already but
heterogeneous, and TRAIN-period circular climatology (per
``(station, month, hour)``) sometimes has even wider 90% arcs. This candidate
widens model intervals toward climatology halfwidths where:

    - climatology halfwidth > model halfwidth (raw_gap > 0),
    - gated by ``speed_rank * halfwidth_rank`` within ``(hour,)`` groups.

``dir_50`` is FROZEN. ``q05/q50/q95`` are FROZEN. Only ``dir_05/dir_95`` move.
Widening is symmetric around ``dir_50`` (cannot move the center).

Base: v173 (the dir_stations_d14_ns block is identical in v173/v191/v198 so
v173 is the cleanest base and avoids any leakage from physics).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments._climo_blend_utils import (  # noqa: E402
    apply_speed_conditioned_climatology_width_blend,
    load_station_climatology,
    window_month_table,
)
from src.experiments._next7_utils import (  # noqa: E402
    diff_checks,
    load_predictions,
    output_dir,
    write_submission_with_manifest,
)

VERSION = "v204"
BASE_VERSION = "v173"
OUT_DIR = output_dir(VERSION, "stations_d14_ns_climo_widening")

SPEED_FLOOR = 0.15
HALFWIDTH_FLOOR = 0.05
MAX_WIDEN_DEG = 20.0
MAX_HALFWIDTH_DEG = 179.0


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("station")
        & frame["region"].eq("north_sea")
        & frame["horizon"].astype(int).eq(14)
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_predictions(BASE_VERSION)
    climo = load_station_climatology()
    wm = window_month_table()

    target = target_mask(base)
    candidate, allowed_dir, stats = apply_speed_conditioned_climatology_width_blend(
        base,
        target,
        climo,
        speed_floor=SPEED_FLOOR,
        halfwidth_floor=HALFWIDTH_FLOOR,
        max_widen_deg=MAX_WIDEN_DEG,
        max_halfwidth_deg=MAX_HALFWIDTH_DEG,
        window_month=wm,
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
        "target_dimension": "dir_stations_d14_ns",
        "scope": "station/north_sea/d14/direction_endpoints_only",
        "mechanism": (
            "Lane D: speed*halfwidth-rank gated widening toward TRAIN-period "
            "circular climatology p05/p95; dir_50 and q frozen; widen-only."
        ),
        "base_observation": (
            "v173 dir_stations_d14_ns halfwidth is a flat 136.1deg across all "
            "256 rows (single CQR width broadcast over the whole cell). The "
            "blend introduces genuine per-(station,month,hour) variation: "
            "rows where TRAIN circular climatology exceeds 136.1deg are widened, "
            "rows where climo is tighter are untouched."
        ),
        "post_mortem_hints": [
            "If leaderboard regresses, the directional lever to flip is to "
            "gate on LOW hw_rank instead of HIGH (Winkler typically rewards "
            "widening under-covered narrow intervals, not already-wide ones); "
            "however the base here is uniformly wide so 'narrow-rows' isn't a "
            "meaningful cohort -- the right second-shot would instead be to "
            "raise max_widen_deg or lower speed_floor.",
        ],
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
