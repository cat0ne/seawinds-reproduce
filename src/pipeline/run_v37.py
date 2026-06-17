"""V37: Track F pressure-direction overlay.

This is an intentionally isolated high-upside experiment. It starts from v35
and replaces only pressure-level grid direction intervals for d1/d7 using
Track F circular direction models. All station rows, surface rows, speed
columns, and d14 pressure direction remain unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PRESSURE_LEVELS, PROJECT_ROOT
from src.experiments.track_f_pressure_direction import fit_production_models, predict_inference_overrides
from src.pipeline.pipeline_utils import save_submission


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
MERGE_KEYS = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
TARGET_HORIZONS = {1, 7}
PRESSURE_LEVEL_STRS = {str(level) for level in PRESSURE_LEVELS}


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def apply_track_f_pressure_direction(base: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Return base with only Track F pressure d1/d7 direction copied in."""

    out = base.copy()
    out["latitude"] = out["latitude"].astype(float).round(2)
    out["longitude"] = out["longitude"].astype(float).round(2)
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    out["level"] = out["level"].astype(str)

    overrides = overrides.copy()
    overrides["latitude"] = overrides["latitude"].astype(float).round(2)
    overrides["longitude"] = overrides["longitude"].astype(float).round(2)
    overrides["horizon"] = overrides["horizon"].astype(int)
    overrides["hour"] = overrides["hour"].astype(int)
    overrides["level"] = overrides["level"].astype(str)

    donor = overrides[MERGE_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_track_f" for col in DIR_COLS}
    )
    merged = out.merge(donor, on=MERGE_KEYS, how="left")
    target = (
        merged["dir_50_track_f"].notna()
        & merged["type"].eq("grid")
        & merged["level"].astype(str).isin(PRESSURE_LEVEL_STRS)
        & merged["horizon"].astype(int).isin(TARGET_HORIZONS)
    )
    for col in DIR_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_track_f"]
    return merged.drop(columns=[f"{col}_track_f" for col in DIR_COLS])


def assert_v37_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    allowed = (
        cand_aligned["type"].eq("grid")
        & cand_aligned["level"].astype(str).isin(PRESSURE_LEVEL_STRS)
        & cand_aligned["horizon"].astype(int).isin(TARGET_HORIZONS)
    )
    unexpected = dir_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected direction changes outside pressure d1/d7 scope: {int(unexpected.sum())}")

    changed = int((dir_changed & allowed).sum())
    if changed == 0:
        raise ValueError("Expected pressure d1/d7 direction rows to change")


def generate_v37() -> None:
    print("\n" + "=" * 60)
    print("Generating V37 submission (Track F pressure d1/d7 direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v35.csv"))

    print("\n[1/3] Training Track F production models...")
    models = fit_production_models()
    print(f"  Models: {len(models)}")

    print("\n[2/3] Predicting pressure direction overrides...")
    overrides = predict_inference_overrides(models)
    print(f"  Override rows: {len(overrides):,}")

    print("\n[3/3] Applying guarded pressure-direction overlay...")
    submission = apply_track_f_pressure_direction(base, overrides)
    assert_v37_scope(base, submission)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  NaNs in prediction columns: {int(nans)}")
    save_submission(submission, "v37")


if __name__ == "__main__":
    generate_v37()
