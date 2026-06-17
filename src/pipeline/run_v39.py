"""V39/V40: Track I v38-anchored ECS station-direction residual candidates.

Track I was locally stable for East China Sea station direction and unstable
for North Sea station direction. These candidates start from v38 and replace
only ECS station direction rows:

- v39: ECS d1 station direction only
- v40: ECS d1/d7/d14 station direction
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.experiments.track_i_v38_residual_direction import fit_models, predict_inference_overrides
from src.pipeline.pipeline_utils import save_submission


def _cached_models(cache_path: Path, fit_fn, label: str):
    """repro: deterministic model cache — load frozen models if present, else fit + save.

    Makes repeated runs (and the v39/v40 pair, which would otherwise fit twice)
    byte-identical. Failures are non-fatal (falls back to fitting)."""
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
ECS_D1_TARGETS = {("east_china_sea", 1)}
ECS_ALL_TARGETS = {("east_china_sea", 1), ("east_china_sea", 7), ("east_china_sea", 14)}


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def apply_track_i_station_direction(
    base: pd.DataFrame,
    overrides: pd.DataFrame,
    targets: set[tuple[str, int]],
) -> pd.DataFrame:
    """Return base with Track I direction copied only for requested station cells."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)
    overrides = overrides.copy()
    overrides["horizon"] = overrides["horizon"].astype(int)
    overrides["hour"] = overrides["hour"].astype(int)

    donor = overrides[STATION_KEYS + DIR_COLS].rename(
        columns={col: f"{col}_track_i" for col in DIR_COLS}
    )
    merged = out.merge(donor, on=STATION_KEYS, how="left")
    allowed = pd.Series(False, index=merged.index)
    for region, horizon in targets:
        allowed |= (
            merged["type"].eq("station")
            & merged["region"].eq(region)
            & merged["horizon"].eq(int(horizon))
        )
    target = allowed & merged["dir_50_track_i"].notna()
    missing = allowed & merged["dir_50_track_i"].isna()
    if missing.any():
        raise ValueError(f"Track I overrides missing for {int(missing.sum())} requested station rows")

    for col in DIR_COLS:
        merged.loc[target, col] = merged.loc[target, f"{col}_track_i"]
    return merged.drop(columns=[f"{col}_track_i" for col in DIR_COLS])


def assert_track_i_scope(
    base: pd.DataFrame,
    candidate: pd.DataFrame,
    targets: set[tuple[str, int]],
) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    allowed = pd.Series(False, index=cand_aligned.index)
    for region, horizon in targets:
        allowed |= (
            cand_aligned["type"].eq("station")
            & cand_aligned["region"].eq(region)
            & cand_aligned["horizon"].astype(int).eq(int(horizon))
        )

    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    unexpected = dir_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected direction changes outside Track I scope: {int(unexpected.sum())}")

    changed = int((dir_changed & allowed).sum())
    if changed == 0:
        raise ValueError("Expected at least one requested Track I station direction row to change")


def _generate(version: str, targets: set[tuple[str, int]]) -> None:
    print("\n" + "=" * 60)
    print(f"Generating {version.upper()} submission (Track I ECS station direction)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v38.csv"))
    models = _cached_models(PROJECT_ROOT / "logs" / "track_i_v39" / "models.pkl",
                            fit_models, "Track I v39/v40")
    overrides = predict_inference_overrides(models, targets=targets)
    print(f"  Override rows: {len(overrides):,}")

    submission = apply_track_i_station_direction(base, overrides, targets)
    assert_track_i_scope(base, submission, targets)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"  Speed rows changed: {int(q_changed.sum()):,}")
    print(f"  Direction rows changed: {int(dir_changed.sum()):,}")
    print(f"  NaNs in prediction columns: {int(nans)}")
    save_submission(submission, version)


def generate_v39() -> None:
    _generate("v39", ECS_D1_TARGETS)


def generate_v40() -> None:
    _generate("v40", ECS_ALL_TARGETS)


if __name__ == "__main__":
    generate_v39()
