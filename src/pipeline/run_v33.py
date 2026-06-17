"""V33: Track D station-direction overlay only.

This submission starts from v31 and replaces only station direction intervals
with the Track D circular direction model:
- one model per region / horizon,
- center predicted through sin/cos components,
- half-width predicted as a calibrated circular-error quantile.

No grid rows and no speed columns are allowed to change.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.experiments.track_d_direction_proto import fit_production_models, predict_inference_overrides
from src.pipeline.pipeline_utils import save_submission


DIR_COLS = ["dir_05", "dir_50", "dir_95"]
Q_COLS = ["q05", "q50", "q95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def apply_track_d_station_direction(base: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Return base predictions with station direction columns replaced."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    overrides = overrides.copy()
    overrides["horizon"] = overrides["horizon"].astype(int)
    overrides["hour"] = overrides["hour"].astype(int)

    donor = overrides[STATION_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_track_d" for col in DIR_COLS}
    )
    merged = out.merge(donor, on=STATION_KEYS, how="left")
    target = merged["type"].eq("station") & merged["dir_50_track_d"].notna()

    for col in DIR_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_track_d"]

    return merged.drop(columns=[f"{col}_track_d" for col in DIR_COLS])


def assert_track_d_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    """Fail if v33 changed anything outside station direction columns."""

    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    unexpected_dir = dir_changed & ~cand_aligned["type"].eq("station")
    if unexpected_dir.any():
        raise ValueError(f"Unexpected non-station direction changes: {int(unexpected_dir.sum())}")

    station_rows = int(cand_aligned["type"].eq("station").sum())
    changed_station = int((dir_changed & cand_aligned["type"].eq("station")).sum())
    if changed_station != station_rows:
        raise ValueError(f"Expected all station direction rows to change, got {changed_station}/{station_rows}")


def generate_v33() -> None:
    print("\n" + "=" * 60)
    print("Generating V33 submission (Track D station-direction overlay)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v31.csv"))
    print(f"  Base rows: {len(base):,}")

    print("\n[1/3] Training Track D production models...")
    models = fit_production_models(calibration_days=30)
    print(f"  Models: {len(models)}")

    print("\n[2/3] Predicting station direction overrides...")
    overrides = predict_inference_overrides(models)
    print(f"  Override rows: {len(overrides):,}")

    print("\n[3/3] Applying guarded station-direction overlay...")
    submission = apply_track_d_station_direction(base, overrides)
    assert_track_d_scope(base, submission)

    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"  NaNs in prediction columns: {int(nans)}")
    print(f"  Station direction rows changed: {int(submission['type'].eq('station').sum()):,}")
    save_submission(submission, "v33")


if __name__ == "__main__":
    generate_v33()
