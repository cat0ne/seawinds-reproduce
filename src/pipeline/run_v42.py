"""V42: learned-gate Track I ECS d7 station-direction candidate.

V41 used a hard-coded gate (center_shift <= 20, half_width in [35,85]) that
accepted 107 of 224 ECS d7 station rows and improved dir_stations_d7_ecs by
-12.2 cWS. V42 replaces the hand-tuned rule with a learned safety model
trained on the v41 accepted/rejected labels. The learned model is essentially
center_shift <= 19.84, but it is now codified, reusable, and ready for d14.

Scope: identical to v41 — only ECS d7 station direction rows may change.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.pipeline.pipeline_utils import save_submission
from src.scoring.winkler import _circ_dist

GATE_DIR = PROJECT_ROOT / "logs" / "learned_gate_v42"
Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
STATION_KEYS = ["window", "region", "station", "horizon", "hour"]
TARGET_REGION = "east_china_sea"
TARGET_HORIZON = 7
GATE_THRESH = 0.5


def _phase1_path(filename: str) -> Path:
    return PROJECT_ROOT / "starting-kit" / "phase_1" / filename


def _load_predictions_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, low_memory=False)


def _load_learned_gate():
    with open(GATE_DIR / "v41_logreg_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(GATE_DIR / "v41_feature_names.json", "r") as f:
        feature_names = json.load(f)
    return model, feature_names


def _build_gate_features(base: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    """Construct the feature matrix for the learned gate."""
    merged = base.merge(
        candidate[STATION_KEYS + ["dir_05", "dir_50", "dir_95"]],
        on=STATION_KEYS,
        suffixes=["_base", "_cand"],
    )

    merged["center_shift"] = _circ_dist(
        merged["dir_50_base"].to_numpy(float),
        merged["dir_50_cand"].to_numpy(float),
    )
    merged["base_half_width"] = ((merged["dir_95_base"] - merged["dir_05_base"]) % 360.0) / 2.0
    merged["candidate_half_width"] = ((merged["dir_95_cand"] - merged["dir_05_cand"]) % 360.0) / 2.0
    merged["width_delta"] = merged["candidate_half_width"] - merged["base_half_width"]
    merged["shift_over_width"] = merged["center_shift"] / merged["base_half_width"].clip(lower=1.0)

    station_dummies = pd.get_dummies(merged["station"], prefix="st")
    merged = pd.concat([merged, station_dummies], axis=1)

    # Ensure all feature columns exist (missing station dummies -> 0)
    for col in ["center_shift", "candidate_half_width", "base_half_width", "width_delta", "shift_over_width"]:
        if col not in merged.columns:
            merged[col] = 0.0
    for col in [f"st_ECS_0{i}" for i in range(1, 8)]:
        if col not in merged.columns:
            merged[col] = 0

    return merged


def apply_learned_gate(
    base: pd.DataFrame,
    candidate_source: pd.DataFrame,
    gate_model,
    feature_names: list[str],
    thresh: float = GATE_THRESH,
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Copy Track I ECS d7 direction only for rows predicted safe by learned gate."""

    out = base.copy()
    out["horizon"] = out["horizon"].astype(int)
    out["hour"] = out["hour"].astype(int)

    cand = candidate_source.copy()
    cand["horizon"] = cand["horizon"].astype(int)
    cand["hour"] = cand["hour"].astype(int)
    cand_station = cand[cand["type"].eq("station")].copy()
    if cand_station.duplicated(STATION_KEYS).any():
        raise ValueError(f"Candidate source has duplicate station keys: {int(cand_station.duplicated(STATION_KEYS).sum())}")

    donor = cand_station[STATION_KEYS + DIR_COLS].rename(columns={col: f"{col}_cand" for col in DIR_COLS})
    merged = out.merge(donor, on=STATION_KEYS, how="left")

    requested = (
        merged["type"].eq("station")
        & merged["region"].eq(TARGET_REGION)
        & merged["horizon"].eq(TARGET_HORIZON)
    )
    missing = requested & merged["dir_50_cand"].isna()
    if missing.any():
        raise ValueError(f"Candidate source missing for {int(missing.sum())} ECS d7 station rows")

    # Build gate features for requested rows
    req_positions = np.where(requested.to_numpy())[0]
    req_frame = merged.iloc[req_positions][STATION_KEYS + DIR_COLS].copy().reset_index(drop=True)
    gate_frame = _build_gate_features(req_frame, cand_station)
    X = gate_frame[feature_names].fillna(0.0).astype(float)
    proba = gate_model.predict_proba(X)[:, 1]

    # Hard sanity guard: never accept absurdly wide or narrow intervals
    proba[(gate_frame["candidate_half_width"] > 120.0) | (gate_frame["candidate_half_width"] < 10.0)] = 0.0

    safe_positions = req_positions[proba >= thresh]
    gate = pd.Series(False, index=merged.index)
    gate.iloc[safe_positions] = True

    for col in DIR_COLS:
        merged.loc[gate, col] = merged.loc[gate, f"{col}_cand"]

    metrics = {
        "requested_rows": int(requested.sum()),
        "accepted_rows": int(gate.sum()),
        "rejected_rows": int(requested.sum() - gate.sum()),
        "mean_proba": float(proba.mean()),
        "thresh": float(thresh),
    }
    result = merged.drop(columns=[f"{col}_cand" for col in DIR_COLS])
    return result, metrics


def assert_v42_scope(base: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if len(base) != len(candidate):
        raise ValueError(f"Row count changed: {len(base)} -> {len(candidate)}")

    base_aligned = base.reset_index(drop=True)
    cand_aligned = candidate.reset_index(drop=True)

    q_changed = (base_aligned[Q_COLS] != cand_aligned[Q_COLS]).any(axis=1)
    if q_changed.any():
        raise ValueError(f"Unexpected speed changes: {int(q_changed.sum())}")

    allowed = (
        cand_aligned["type"].eq("station")
        & cand_aligned["region"].eq(TARGET_REGION)
        & cand_aligned["horizon"].astype(int).eq(TARGET_HORIZON)
    )
    dir_changed = (base_aligned[DIR_COLS] != cand_aligned[DIR_COLS]).any(axis=1)
    unexpected = dir_changed & ~allowed
    if unexpected.any():
        raise ValueError(f"Unexpected direction changes outside ECS d7 station scope: {int(unexpected.sum())}")

    changed = int((dir_changed & allowed).sum())
    if changed == 0:
        raise ValueError("Expected at least one gated ECS d7 station direction row to change")


def generate_v42() -> None:
    print("\n" + "=" * 60)
    print("Generating V42 submission (learned-gate Track I ECS d7)")
    print("=" * 60)

    base = _load_predictions_csv(_phase1_path("predictions_v39.csv"))
    v40 = _load_predictions_csv(_phase1_path("predictions_v40.csv"))

    gate_model, feature_names = _load_learned_gate()

    submission, metrics = apply_learned_gate(base, v40, gate_model, feature_names)
    assert_v42_scope(base, submission)

    q_changed = (base[Q_COLS].reset_index(drop=True) != submission[Q_COLS].reset_index(drop=True)).any(axis=1)
    dir_changed = (base[DIR_COLS].reset_index(drop=True) != submission[DIR_COLS].reset_index(drop=True)).any(axis=1)
    nans = submission[Q_COLS + DIR_COLS].isna().sum().sum()
    print(f"  Requested ECS d7 rows: {metrics['requested_rows']:,}")
    print(f"  Accepted gated rows:   {metrics['accepted_rows']:,}")
    print(f"  Rejected gated rows:   {metrics['rejected_rows']:,}")
    print(f"  Mean safety proba:     {metrics['mean_proba']:.3f}")
    print(f"  Speed rows changed:    {int(q_changed.sum()):,}")
    print(f"  Direction rows changed:{int(dir_changed.sum()):,}")
    print(f"  NaNs in prediction columns: {int(nans)}")
    save_submission(submission, "v42")


if __name__ == "__main__":
    generate_v42()
