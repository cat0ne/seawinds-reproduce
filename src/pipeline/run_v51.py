"""V51: corrected v47 copula donor scoped onto the v46 base.

V47 tested per-horizon copula damping but accidentally loaded v41 as the base.
Its raw scores still showed small improvements on ECS pressure d7/d14
direction. V51 starts from v46 and copies only those ECS pressure d7/d14
direction rows from v47, with base-hash and scope guards.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission
from src.pipeline.submission_guards import (
    DIR_COLS,
    assert_base_file,
    assert_prediction_scope,
    mask_grid_direction_scope,
    write_manifest,
)


VERSION = "v51"
BASE_VERSION = "v46"
DONOR_VERSION = "v47"
EXPECTED_BASE_FILE = "predictions_v46.csv"
OUT_DIR = PROJECT_ROOT / "logs" / "v51_corrected_copula"


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def _target_mask(frame: pd.DataFrame) -> pd.Series:
    return mask_grid_direction_scope(
        frame,
        lambda df: (
            df["region"].eq("east_china_sea")
            & df["level"].isin(["1000", "925", "850", "700", "500"])
            & df["horizon"].isin([7, 14])
        ),
    )


def apply_v47_ecs_pressure_donor(base: pd.DataFrame, donor: pd.DataFrame) -> pd.DataFrame:
    """Copy ECS pressure d7/d14 direction intervals from v47 onto v46."""

    if len(base) != len(donor):
        raise ValueError(f"Base/donor row count mismatch: {len(base)} != {len(donor)}")
    out = base.copy()
    target = _target_mask(out)
    out.loc[target, DIR_COLS] = donor.loc[target, DIR_COLS].to_numpy()
    return out


def assert_v51_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, int]:
    """Validate that v51 changes only ECS pressure d7/d14 grid direction."""

    return assert_prediction_scope(
        base,
        candidate,
        _target_mask(candidate),
        expect_speed_changes=False,
        expect_direction_changes=True,
    )


def generate_v51() -> None:
    print("\n" + "=" * 60)
    print("Generating V51 submission (v46 + scoped v47 ECS pressure d7/d14 direction)")
    print("=" * 60)

    base_path = _phase1_path(EXPECTED_BASE_FILE)
    base_hash = assert_base_file(base_path, EXPECTED_BASE_FILE)
    donor_path = _phase1_path(f"predictions_{DONOR_VERSION}.csv")

    base = _load_predictions_csv(base_path)
    donor = _load_predictions_csv(donor_path)
    submission = apply_v47_ecs_pressure_donor(base, donor)
    metrics = assert_v51_scope(base, submission)

    print(f"  Base: {EXPECTED_BASE_FILE}")
    print(f"  Base SHA-256: {base_hash[:16]}...")
    print(f"  Donor: predictions_{DONOR_VERSION}.csv")
    print(f"  Allowed rows: {metrics['allowed_rows']:,}")
    print(f"  Direction rows changed: {metrics['direction_changed_rows']:,}")
    print(f"  Speed rows changed: {metrics['speed_changed_rows']:,}")

    manifest_path = write_manifest(
        OUT_DIR,
        version=VERSION,
        base_version=BASE_VERSION,
        base_path=base_path,
        base_hash=base_hash,
        donor_versions=[DONOR_VERSION],
        scope="grid/east_china_sea/pressure/d7+d14/direction_only",
        metrics=metrics,
    )
    print(f"  Manifest: {manifest_path}")
    save_submission(submission, VERSION)


if __name__ == "__main__":
    generate_v51()
