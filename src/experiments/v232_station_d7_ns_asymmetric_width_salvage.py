"""v232: salvage the d7-only part of v183 on the current v222 base.

v183 should not be submitted as built because it includes a station d14 NS
direction component contradicted by v179's hidden score. The d7 part is still
the only center-frozen station-direction candidate with enough replay magnitude
to plausibly clear the current ``dir_stations_d7_ns`` rank boundary, so this
artifact copies only those d7 endpoints onto v222 and holds it behind the
existing speed gates.
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

VERSION = "v232"
BASE_VERSION = "v222"
SOURCE_VERSION = "v183"
OUT_DIR = LOGS_DIR / f"{VERSION}_station_d7_ns_asymmetric_width_salvage"

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


def load_predictions(version: str) -> pd.DataFrame:
    path = SUBMISSIONS_DIR / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, low_memory=False)


def target_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["type"].eq("station")
        & frame["region"].eq("north_sea")
        & frame["horizon"].astype(int).eq(7)
    )


def circular_width(frame: pd.DataFrame, mask: pd.Series) -> pd.Series:
    return (
        pd.to_numeric(frame.loc[mask, "dir_95"], errors="coerce")
        - pd.to_numeric(frame.loc[mask, "dir_05"], errors="coerce")
    ) % 360.0


def validate(base: pd.DataFrame, source: pd.DataFrame, candidate: pd.DataFrame, target: pd.Series) -> dict[str, object]:
    if len(base) != len(candidate) or len(base) != len(source):
        raise RuntimeError(f"Row count mismatch: base={len(base)} source={len(source)} candidate={len(candidate)}")

    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    dir50_changed = candidate["dir_50"].round(9).ne(base["dir_50"].round(9))
    non_target_dir = dir_changed & ~target

    base_width = circular_width(base, target)
    candidate_width = circular_width(candidate, target)
    width_delta = candidate_width - base_width

    station_rows = (
        pd.DataFrame(
            {
                "station": base.loc[target, "station"].to_numpy(),
                "width_delta": width_delta.to_numpy(float),
                "changed": dir_changed.loc[target].to_numpy(bool),
            }
        )
        .groupby("station")
        .agg(rows=("station", "size"), changed=("changed", "sum"), mean_width_delta=("width_delta", "mean"))
        .reset_index()
    )

    checks: dict[str, object] = {
        "changed_rows": int((q_changed | dir_changed).sum()),
        "speed_changed_rows": int(q_changed.sum()),
        "direction_changed_rows": int(dir_changed.sum()),
        "non_target_q_rows": int(q_changed.sum()),
        "non_target_dir_rows": int(non_target_dir.sum()),
        "q50_changed_rows": int(candidate["q50"].round(9).ne(base["q50"].round(9)).sum()),
        "dir50_changed_rows": int(dir50_changed.sum()),
        "target_rows": int(target.sum()),
        "mean_width_delta_target": float(width_delta.mean()),
        "min_width_delta_target": float(width_delta.min()),
        "max_width_delta_target": float(width_delta.max()),
        "station_width_delta": station_rows.to_dict(orient="records"),
    }
    q = candidate[Q_COLS].to_numpy(dtype=float)
    checks["quantile_crossing_rows"] = int(
        ((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum()
    )
    checks["nan_prediction_values"] = int(candidate[PRED_COLS].isna().sum().sum())

    source_diff = candidate.loc[target, DIR_COLS].round(9).ne(source.loc[target, DIR_COLS].round(9)).any(axis=1)
    checks["target_rows_not_matching_source"] = int(source_diff.sum())

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
            "target_rows_not_matching_source",
        }
        and value
    }
    if bad:
        raise RuntimeError(f"Validation failed: {bad}")
    if checks["direction_changed_rows"] != checks["target_rows"]:
        raise RuntimeError(
            f"Expected every target row to change: {checks['direction_changed_rows']} / {checks['target_rows']}"
        )
    if not np.isclose(float(checks["mean_width_delta_target"]), 0.166796875, atol=1e-9):
        raise RuntimeError(f"Unexpected mean width delta: {checks['mean_width_delta_target']}")
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
    source = load_predictions(SOURCE_VERSION)
    target = target_mask(base)

    candidate = base.copy()
    candidate.loc[target, DIR_COLS] = source.loc[target, DIR_COLS].to_numpy()
    checks = validate(base, source, candidate, target)
    zip_path = save_submission(candidate)

    manifest = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "source_version": SOURCE_VERSION,
        "target_dimension": "dir_stations_d7_ns",
        "scope": "station/north_sea/d7/direction endpoints only",
        "mechanism": "d7-only salvage of v183 center-frozen asymmetric station/hour endpoint calibration",
        "upload_posture": (
            "HOLD; do not upload ahead of v225, the guarded v222_plus_v225 path, "
            "the held speed probes, or v227. Use only after a live-board refresh and "
            "explicit decision to spend a station-d7 direction diagnostic."
        ),
        "leaderboard_boundary_2026_06_04": {
            "current_score": 310.9467,
            "next_rank_score": 301.54,
            "gap_to_next_rank": 9.4067,
            "rank_1_score": 266.49,
            "gap_to_rank_1": 44.4567,
        },
        "replay_evidence": {
            "v183_d7_asym_0p50_mean_delta_cws": -42.20939449983782,
            "v183_d7_asym_0p50_worst_delta_cws": -17.024705167426532,
            "warning": (
                "v183 as built is blocked because it also includes a failed d14 station-direction family; "
                "this artifact isolates only the d7 piece."
            ),
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
