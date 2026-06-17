"""V26: Station cherry-pick on top of v19.

V19 is a station breakthrough, but its station-direction overlay regressed
three region/horizon cells:
- north_sea d14
- east_china_sea d1
- east_china_sea d14

This variant keeps all v19 station speed quantiles, keeps v19 station
direction where it won, and reverts only the losing station-direction cells to
v16. Grid rows are inherited from v19/v16 unchanged.

Usage:
    python -m src.pipeline.run_v26
"""

from __future__ import annotations

import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission


REVERT_STATION_DIRECTION = {
    ("north_sea", 14),
    ("east_china_sea", 1),
    ("east_china_sea", 14),
}


def _load_predictions(version: str) -> pd.DataFrame:
    path = PROJECT_ROOT / "starting-kit" / "phase_1" / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def station_direction_cherry_pick(v19: pd.DataFrame, v16: pd.DataFrame) -> pd.DataFrame:
    """Return v19 with losing station-direction cells reverted to v16."""
    out = v19.copy()

    station_mask = out["type"] == "station"
    out.loc[station_mask, "horizon"] = out.loc[station_mask, "horizon"].astype(int)

    v16_station = v16[v16["type"] == "station"].copy()
    v16_station["horizon"] = v16_station["horizon"].astype(int)

    keys = ["window", "region", "station", "horizon", "hour"]
    dir_cols = ["dir_05", "dir_50", "dir_95"]
    fallback = v16_station[keys + dir_cols].rename(
        columns={col: f"{col}_v16" for col in dir_cols}
    )

    merged = out.merge(fallback, on=keys, how="left")
    revert_mask = merged["type"].eq("station") & (
        ((merged["region"] == "north_sea") & (merged["horizon"].astype(int) == 14))
        | ((merged["region"] == "east_china_sea") & (merged["horizon"].astype(int).isin([1, 14])))
    )

    for col in dir_cols:
        merged.loc[revert_mask, col] = merged.loc[revert_mask, f"{col}_v16"]
    merged = merged.drop(columns=[f"{col}_v16" for col in dir_cols])

    return merged


def generate_v26() -> None:
    print("\n" + "=" * 60)
    print("Generating V26 submission (v19 station speed + cherry-picked station direction)")
    print("=" * 60)

    v19 = _load_predictions("v19")
    v16 = _load_predictions("v16")
    submission = station_direction_cherry_pick(v19, v16)

    n_reverted = submission[
        submission["type"].eq("station")
        & (
            ((submission["region"] == "north_sea") & (submission["horizon"].astype(int) == 14))
            | ((submission["region"] == "east_china_sea") & (submission["horizon"].astype(int).isin([1, 14])))
        )
    ].shape[0]
    print(f"  Reverted station-direction rows: {n_reverted:,}")
    save_submission(submission, "v26")


if __name__ == "__main__":
    generate_v26()
