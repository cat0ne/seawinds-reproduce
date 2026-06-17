"""v227: tiny center-frozen NS station d1 direction width shrink.

The current public snapshot shows ``dir_stations_d1_ns`` rank 2, only about
0.158 cWS behind rank 1. The cell is already a hidden-proven v35 cherry-pick
from v32, so this candidate does not move centers or import a new model. It
shrinks only the two direction endpoints by 0.10 degrees per side on the NS
station d1 rows, enough to cross the visible boundary if hidden coverage is
unchanged.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS_DIR = ROOT / "submissions"
LOGS_DIR = ROOT / "logs"

VERSION = "v227"
BASE_VERSION = "v222"
OUT_DIR = LOGS_DIR / f"{VERSION}_station_d1_ns_direction_micro_shrink"

SHRINK_PER_SIDE_DEG = 0.10
MIN_HALFWIDTH_DEG = 0.25

Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
PRED_COLS = Q_COLS + DIR_COLS
SUB_COLS = [
    "type",
    "window",
    "region",
    "latitude",
    "longitude",
    "station",
    "horizon",
    "hour",
    "level",
    "q05",
    "q50",
    "q95",
    "dir_05",
    "dir_50",
    "dir_95",
]


def circular_distance_forward(start: pd.Series, end: pd.Series) -> pd.Series:
    """Return clockwise distance in degrees from start to end."""

    return (pd.to_numeric(end, errors="coerce") - pd.to_numeric(start, errors="coerce")) % 360.0


def shrink_direction_interval(
    frame: pd.DataFrame,
    mask: pd.Series,
    *,
    shrink_per_side_deg: float = SHRINK_PER_SIDE_DEG,
    min_halfwidth_deg: float = MIN_HALFWIDTH_DEG,
) -> pd.DataFrame:
    """Shrink direction endpoints toward dir_50 for selected rows."""

    out = frame.copy()
    center = pd.to_numeric(out.loc[mask, "dir_50"], errors="coerce")
    lower = circular_distance_forward(out.loc[mask, "dir_05"], center)
    upper = circular_distance_forward(center, out.loc[mask, "dir_95"])

    lower_shrink = np.minimum(shrink_per_side_deg, np.maximum(lower - min_halfwidth_deg, 0.0))
    upper_shrink = np.minimum(shrink_per_side_deg, np.maximum(upper - min_halfwidth_deg, 0.0))

    out.loc[mask, "dir_05"] = (center - (lower - lower_shrink)) % 360.0
    out.loc[mask, "dir_95"] = (center + (upper - upper_shrink)) % 360.0
    return out


def load_predictions(version: str) -> pd.DataFrame:
    path = SUBMISSIONS_DIR / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, low_memory=False)


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("station")
        & frame["region"].eq("north_sea")
        & frame["horizon"].astype(int).eq(1)
    )


def interval_width(frame: pd.DataFrame, mask: pd.Series) -> pd.Series:
    return circular_distance_forward(frame.loc[mask, "dir_05"], frame.loc[mask, "dir_95"])


def validate(base: pd.DataFrame, candidate: pd.DataFrame, target: pd.Series) -> dict[str, int | float]:
    if len(base) != len(candidate):
        raise RuntimeError(f"Row count changed: {len(base)} -> {len(candidate)}")

    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    dir50_changed = candidate["dir_50"].round(9).ne(base["dir_50"].round(9))
    non_target_dir = dir_changed & ~target

    base_width = interval_width(base, target)
    candidate_width = interval_width(candidate, target)
    checks: dict[str, int | float] = {
        "changed_rows": int((q_changed | dir_changed).sum()),
        "speed_changed_rows": int(q_changed.sum()),
        "direction_changed_rows": int(dir_changed.sum()),
        "non_target_q_rows": int(q_changed.sum()),
        "non_target_dir_rows": int(non_target_dir.sum()),
        "q50_changed_rows": int(candidate["q50"].round(9).ne(base["q50"].round(9)).sum()),
        "dir50_changed_rows": int(dir50_changed.sum()),
        "target_rows": int(target.sum()),
        "mean_width_delta_target": float((candidate_width - base_width).mean()),
        "min_width_delta_target": float((candidate_width - base_width).min()),
        "max_width_delta_target": float((candidate_width - base_width).max()),
    }

    q = candidate[Q_COLS].to_numpy(dtype=float)
    checks["quantile_crossing_rows"] = int(
        ((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum()
    )
    checks["nan_prediction_values"] = int(candidate[PRED_COLS].isna().sum().sum())

    bad = {
        key: value
        for key, value in checks.items()
        if key
        in {
            "speed_changed_rows",
            "non_target_q_rows",
            "non_target_dir_rows",
            "q50_changed_rows",
            "dir50_changed_rows",
            "quantile_crossing_rows",
            "nan_prediction_values",
        }
        and value
    }
    if bad:
        raise RuntimeError(f"Validation failed: {bad}")
    if checks["direction_changed_rows"] != checks["target_rows"]:
        raise RuntimeError(
            f"Expected every target row to change: {checks['direction_changed_rows']} / {checks['target_rows']}"
        )
    return checks


def save_submission(frame: pd.DataFrame) -> Path:
    csv_path = SUBMISSIONS_DIR / f"predictions_{VERSION}.csv"
    zip_path = SUBMISSIONS_DIR / f"submission_{VERSION}.zip"
    frame[SUB_COLS].to_csv(csv_path, index=False)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(csv_path, arcname="predictions.csv")
    return zip_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_predictions(BASE_VERSION)
    target = target_mask(base)
    candidate = shrink_direction_interval(base, target)
    checks = validate(base, candidate, target)
    zip_path = save_submission(candidate)

    manifest = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "target_dimension": "dir_stations_d1_ns",
        "scope": "station/north_sea/d1/direction endpoints only",
        "mechanism": "center-frozen 0.10 degree per-side circular interval shrink",
        "upload_posture": "HOLD; do not upload ahead of v225 or the guarded v225 compound path.",
        "leaderboard_boundary_2026_06_04": {
            "current_score": 170.7878,
            "rank_1_score": 170.63,
            "gap_to_rank_1": 0.1578,
            "expected_delta_if_coverage_unchanged": checks["mean_width_delta_target"],
        },
        "parameters": {
            "shrink_per_side_deg": SHRINK_PER_SIDE_DEG,
            "min_halfwidth_deg": MIN_HALFWIDTH_DEG,
        },
        "checks": checks,
        "zip_path": str(zip_path),
        "zip_sha256": sha256_file(zip_path),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
