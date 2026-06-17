"""V34: Track E station-speed residual overlay only.

This submission starts from v31 and replaces only station speed intervals
with Track E residual-distribution predictions. Direction and all grid rows
must remain unchanged.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.experiments.track_e_station_speed_residual import fit_production_models, predict_inference_overrides
from src.pipeline.pipeline_utils import save_submission


def _cached_models(cache_path: Path, fit_fn, label: str):
    """repro: deterministic model cache — load frozen models if present, else fit + save.

    Track E has no training seed, so its freshly-fit models vary run to run. Caching the
    first fit and reloading it makes every subsequent run byte-identical. Failures are
    non-fatal (falls back to fitting), so this never breaks the pipeline.
    """
    if cache_path.exists():
        try:
            with cache_path.open("rb") as fh:
                models = pickle.load(fh)
            print(f"  [cache] loaded {label} from {cache_path}")
            return models
        except Exception as exc:  # noqa: BLE001
            print(f"  [cache] load failed ({exc}); refitting {label}")
    models = fit_fn()
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as fh:
            pickle.dump(models, fh)
        print(f"  [cache] saved {label} -> {cache_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [cache] save failed ({exc}); continuing un-cached")
    return models


Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def apply_track_e_station_speed(base: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Return base predictions with station speed columns replaced."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    overrides = overrides.copy()
    overrides["horizon"] = overrides["horizon"].astype(int)
    overrides["hour"] = overrides["hour"].astype(int)

    donor = overrides[STATION_KEYS + Q_COLS].rename(
        columns={col: f"{col}_track_e" for col in Q_COLS}
    )
    merged = out.merge(donor, on=STATION_KEYS, how="left")
    target = merged["type"].eq("station") & merged["q50_track_e"].notna()
    for col in Q_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_track_e"]
    return merged.drop(columns=[f"{col}_track_e" for col in Q_COLS])


def assert_track_e_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    """Fail if v34 changed anything outside station speed columns."""

    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    if dir_changed.any():
        raise ValueError(f"Unexpected direction changes: {int(dir_changed.sum())}")

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    unexpected_q = q_changed & ~cand_aligned["type"].eq("station")
    if unexpected_q.any():
        raise ValueError(f"Unexpected non-station speed changes: {int(unexpected_q.sum())}")

    station_rows = int(cand_aligned["type"].eq("station").sum())
    changed_station = int((q_changed & cand_aligned["type"].eq("station")).sum())
    if changed_station != station_rows:
        raise ValueError(f"Expected all station speed rows to change, got {changed_station}/{station_rows}")


def generate_v34() -> None:
    print("\n" + "=" * 60)
    print("Generating V34 submission (Track E station-speed overlay)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v31.csv"))
    print(f"  Base rows: {len(base):,}")

    print("\n[1/3] Training Track E production models (cached for determinism)...")
    models = _cached_models(PROJECT_ROOT / "logs" / "track_e_v34" / "models.pkl",
                            fit_production_models, "Track E v34")
    print(f"  Models: {len(models)}")

    print("\n[2/3] Predicting station speed overrides...")
    overrides = predict_inference_overrides(models)
    print(f"  Override rows: {len(overrides):,}")

    print("\n[3/3] Applying guarded station-speed overlay...")
    submission = apply_track_e_station_speed(base, overrides)
    assert_track_e_scope(base, submission)

    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    crossings = (
        (submission["q05"] > submission["q50"]).sum()
        + (submission["q50"] > submission["q95"]).sum()
    )
    print(f"  NaNs in prediction columns: {int(nans)}")
    print(f"  Quantile crossings: {int(crossings)}")
    print(f"  Station speed rows changed: {int(submission['type'].eq('station').sum()):,}")
    save_submission(submission, "v34")


if __name__ == "__main__":
    generate_v34()
