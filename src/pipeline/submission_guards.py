"""Guardrails for scoped submission variants.

These helpers protect against the v47 class of error: building a candidate on
the wrong base file or silently changing dimensions outside the intended
experiment scope.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from src.data.paths import PROJECT_ROOT


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
PRED_COLS = Q_COLS + DIR_COLS


def file_sha256(path: Path) -> str:
    """Return SHA-256 for a file without loading it into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_base_file(path: Path, expected_name: str) -> str:
    """Validate the base filename and return its content hash."""

    if path.name != expected_name:
        raise ValueError(f"Wrong base file: expected {expected_name}, got {path.name}")
    if not path.exists():
        raise FileNotFoundError(f"Missing base file: {path}")
    return file_sha256(path)


def assert_prediction_scope(
    base: pd.DataFrame,
    candidate: pd.DataFrame,
    allowed_mask: pd.Series,
    *,
    expect_speed_changes: bool = False,
    expect_direction_changes: bool = True,
) -> dict[str, int]:
    """Assert that prediction changes are limited to the allowed rows."""

    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")
    if len(allowed_mask) != len(candidate):
        raise ValueError("Allowed mask length does not match candidate rows")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)
    allowed = allowed_mask.reset_index(drop=True).astype(bool)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)

    unexpected_speed = q_changed & ~allowed
    unexpected_dir = dir_changed & ~allowed
    if unexpected_speed.any():
        raise ValueError(f"Unexpected speed changes outside scope: {int(unexpected_speed.sum())}")
    if unexpected_dir.any():
        raise ValueError(f"Unexpected direction changes outside scope: {int(unexpected_dir.sum())}")
    if q_changed.any() and not expect_speed_changes:
        raise ValueError(f"Unexpected speed changes in scoped variant: {int(q_changed.sum())}")
    if dir_changed.any() and not expect_direction_changes:
        raise ValueError(f"Unexpected direction changes in scoped variant: {int(dir_changed.sum())}")
    if expect_speed_changes and not q_changed.any():
        raise ValueError("Expected speed changes, found none")
    if expect_direction_changes and not dir_changed.any():
        raise ValueError("Expected direction changes, found none")

    nans = int(cand_aligned[PRED_COLS].isna().sum().sum())
    if nans:
        raise ValueError(f"NaNs in prediction columns: {nans}")

    return {
        "rows": int(len(candidate)),
        "allowed_rows": int(allowed.sum()),
        "speed_changed_rows": int(q_changed.sum()),
        "direction_changed_rows": int(dir_changed.sum()),
        "changed_rows_in_scope": int(((q_changed | dir_changed) & allowed).sum()),
        "nan_prediction_values": nans,
    }


def write_manifest(
    out_dir: Path,
    *,
    version: str,
    base_version: str,
    base_path: Path,
    base_hash: str,
    donor_versions: list[str],
    scope: str,
    metrics: dict,
) -> Path:
    """Write a small machine-readable manifest for a generated submission."""

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": version,
        "base_version": base_version,
        "base_path": str(base_path.relative_to(PROJECT_ROOT)),
        "base_sha256": base_hash,
        "donor_versions": donor_versions,
        "scope": scope,
        "metrics": metrics,
    }
    path = out_dir / f"{version}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def mask_grid_direction_scope(
    frame: pd.DataFrame,
    predicate: Callable[[pd.DataFrame], pd.Series],
) -> pd.Series:
    """Build a normalized grid-direction scope mask."""

    normalized = frame.copy()
    normalized["horizon"] = normalized["horizon"].astype(int)
    return normalized["type"].eq("grid") & predicate(normalized)
