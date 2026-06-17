"""Shared guardrails for the v182-v188 breakthrough candidates.

These late-stage probes are intentionally narrow. This module centralizes the
repeated file loading, scope diffing, and manifest writing so each candidate
script can focus on its modeling hypothesis.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import LOGS_DIR, PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission

PHASE1 = PROJECT_ROOT / "submissions"  # submissions now live here (was starting-kit/phase_1)
_LEGACY_PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"

Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
PRED_COLS = Q_COLS + DIR_COLS
KEY_COLS = ["type", "window", "region", "latitude", "longitude", "station", "horizon", "hour", "level"]


def load_predictions(version: str) -> pd.DataFrame:
    path = PHASE1 / f"predictions_{version}.csv"
    if not path.exists():
        legacy = _LEGACY_PHASE1 / f"predictions_{version}.csv"
        if legacy.exists():
            path = legacy
        else:
            raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, engine="python")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def output_dir(version: str, slug: str) -> Path:
    return LOGS_DIR / f"{version}_{slug}"


def normalize_for_keys(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "latitude" in out.columns:
        out["latitude"] = out["latitude"].astype(float).round(2)
    if "longitude" in out.columns:
        out["longitude"] = out["longitude"].astype(float).round(2)
    if "horizon" in out.columns:
        out["horizon"] = out["horizon"].astype(int)
    if "hour" in out.columns:
        out["hour"] = out["hour"].astype(int)
    if "level" in out.columns:
        out["level"] = out["level"].astype(str)
    return out


def assert_no_prediction_pathology(candidate: pd.DataFrame) -> dict[str, int]:
    q = candidate[Q_COLS].to_numpy(dtype=float)
    crossing = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if crossing:
        raise RuntimeError(f"Quantile crossing/negative q05 rows: {crossing}")
    nans = int(candidate[PRED_COLS].isna().sum().sum())
    if nans:
        raise RuntimeError(f"NaN prediction values: {nans}")
    return {"quantile_crossing_rows": crossing, "nan_prediction_values": nans}


def diff_checks(
    base: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    allowed_q: pd.Series,
    allowed_dir: pd.Series,
    forbid_q50_change: bool = False,
    forbid_dir50_change: bool = False,
) -> dict[str, int]:
    if len(base) != len(candidate):
        raise RuntimeError(f"Row count changed: {len(base)} -> {len(candidate)}")
    allowed_q = allowed_q.reindex(base.index, fill_value=False).astype(bool)
    allowed_dir = allowed_dir.reindex(base.index, fill_value=False).astype(bool)

    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int((q_changed & ~allowed_q).sum())
    non_target_dir = int((dir_changed & ~allowed_dir).sum())
    if non_target_q or non_target_dir:
        raise RuntimeError(f"Non-target prediction changes: q={non_target_q}, dir={non_target_dir}")

    q50_changed = int(candidate["q50"].round(9).ne(base["q50"].round(9)).sum())
    dir50_changed = int(candidate["dir_50"].round(9).ne(base["dir_50"].round(9)).sum())
    if forbid_q50_change and q50_changed:
        raise RuntimeError(f"q50 changed but is frozen: {q50_changed}")
    if forbid_dir50_change and dir50_changed:
        raise RuntimeError(f"dir_50 changed but is frozen: {dir50_changed}")

    checks = assert_no_prediction_pathology(candidate)
    checks.update(
        {
            "changed_rows": int((q_changed | dir_changed).sum()),
            "speed_changed_rows": int(q_changed.sum()),
            "direction_changed_rows": int(dir_changed.sum()),
            "non_target_q_rows": non_target_q,
            "non_target_dir_rows": non_target_dir,
            "q50_changed_rows": q50_changed,
            "dir50_changed_rows": dir50_changed,
        }
    )
    return checks


def write_submission_with_manifest(
    *,
    version: str,
    base_version: str,
    candidate: pd.DataFrame,
    manifest_dir: Path,
    manifest: dict,
) -> Path:
    zip_path = save_submission(candidate, version)
    payload = {
        "version": version,
        "base_version": base_version,
        **manifest,
        "zip_path": str(zip_path),
    }
    write_json(manifest_dir / "manifest.json", payload)
    return zip_path


def speed_from_uv(u: pd.Series | np.ndarray, v: pd.Series | np.ndarray) -> np.ndarray:
    return np.sqrt(np.asarray(u, dtype=float) ** 2 + np.asarray(v, dtype=float) ** 2)


def speed_bins(values: pd.Series, cuts: np.ndarray) -> pd.Series:
    labels = np.asarray(["q1_low", "q2", "q3", "q4_high"], dtype=object)
    idx = np.searchsorted(cuts[1:-1], values.to_numpy(dtype=float), side="right")
    return pd.Series(labels[np.clip(idx, 0, len(labels) - 1)], index=values.index)


def circular_halfwidth(lo: pd.Series, hi: pd.Series) -> np.ndarray:
    return ((hi.astype(float).to_numpy() - lo.astype(float).to_numpy()) % 360.0) / 2.0


def wrap_360(values: np.ndarray | pd.Series | float) -> np.ndarray:
    return np.mod(values, 360.0)
