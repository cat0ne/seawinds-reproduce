"""Utilities for the post-v185 breakthrough plan.

The next candidates need the same guardrails repeatedly: parse 36-dimension
names, identify exact target rows, compare scored donors, and copy whole
metric blocks by stable keys instead of positional indices.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.paths import PROJECT_ROOT
from src.experiments._next7_utils import DIR_COLS, Q_COLS

PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
LOG_PATH = PROJECT_ROOT / "submissions" / "log.json"
SURFACE_LEVELS = {"10m", "100m"}


@dataclass(frozen=True)
class DimensionSpec:
    name: str
    problem: str
    group: str
    horizon: int
    region_short: str

    @property
    def region(self) -> str:
        return "north_sea" if self.region_short == "ns" else "east_china_sea"

    @property
    def cols(self) -> list[str]:
        return Q_COLS if self.problem == "speed" else DIR_COLS


def parse_dimension(name: str) -> DimensionSpec:
    parts = name.split("_")
    if len(parts) != 4:
        raise ValueError(f"Unsupported dimension name: {name}")
    return DimensionSpec(
        name=name,
        problem=parts[0],
        group=parts[1],
        horizon=int(parts[2].removeprefix("d")),
        region_short=parts[3],
    )


def dimension_mask(frame: pd.DataFrame, spec: DimensionSpec) -> pd.Series:
    mask = frame["region"].eq(spec.region) & frame["horizon"].astype(int).eq(spec.horizon)
    if spec.group == "stations":
        return mask & frame["type"].eq("station")
    if spec.group == "surface":
        return mask & frame["type"].eq("grid") & frame["level"].astype(str).isin(SURFACE_LEVELS)
    if spec.group == "pressure":
        return mask & frame["type"].eq("grid") & ~frame["level"].astype(str).isin(SURFACE_LEVELS)
    raise ValueError(f"Unsupported group in {spec.name}")


def stable_key_cols(spec: DimensionSpec) -> list[str]:
    if spec.group == "stations":
        return ["type", "window", "region", "station", "horizon", "hour"]
    return ["type", "window", "region", "latitude", "longitude", "horizon", "hour", "level"]


def normalize_keys(frame: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    if "latitude" in key_cols:
        out["latitude"] = out["latitude"].astype(float).round(2)
    if "longitude" in key_cols:
        out["longitude"] = out["longitude"].astype(float).round(2)
    if "horizon" in key_cols:
        out["horizon"] = out["horizon"].astype(int)
    if "hour" in key_cols:
        out["hour"] = out["hour"].astype(int)
    if "level" in key_cols:
        out["level"] = out["level"].astype(str)
    return out


def load_submission_log() -> list[dict]:
    return json.loads(LOG_PATH.read_text(encoding="utf-8"))


def scored_entries_with_predictions() -> list[dict]:
    entries = []
    for entry in load_submission_log():
        if not entry.get("leaderboard_scores"):
            continue
        pred_path = PHASE1 / f"predictions_{entry['id']}.csv"
        if pred_path.exists():
            entries.append(entry)
    return entries


def donor_table(base_version: str, dimensions: list[str]) -> pd.DataFrame:
    entries = scored_entries_with_predictions()
    base = next(entry for entry in entries if entry["id"] == base_version)
    rows = []
    for dim in dimensions:
        base_score = float(base["leaderboard_scores"][dim])
        best_score = base_score
        best_id = base_version
        for entry in entries:
            score = entry["leaderboard_scores"].get(dim)
            if isinstance(score, (int, float)) and float(score) < best_score:
                best_score = float(score)
                best_id = str(entry["id"])
        rows.append(
            {
                "dimension": dim,
                "base_version": base_version,
                "base_score": base_score,
                "best_donor_id": best_id,
                "best_donor_score": best_score,
                "raw_delta": best_score - base_score,
                "has_local_prediction": (PHASE1 / f"predictions_{best_id}.csv").exists(),
            }
        )
    return pd.DataFrame(rows)


def copy_dimension_block(
    *,
    base: pd.DataFrame,
    donor: pd.DataFrame,
    dimension: str,
) -> tuple[pd.DataFrame, pd.Series]:
    spec = parse_dimension(dimension)
    key_cols = stable_key_cols(spec)
    out = base.copy()
    target = dimension_mask(out, spec)
    base_target = normalize_keys(out.loc[target, key_cols].reset_index(), key_cols)
    donor_norm = normalize_keys(donor, key_cols)
    donor_target = donor_norm.loc[dimension_mask(donor_norm, spec), key_cols + spec.cols].copy()
    merged = base_target.merge(donor_target, on=key_cols, how="left", validate="one_to_one")
    if len(merged) != int(target.sum()):
        raise RuntimeError(f"{dimension}: merge row mismatch {len(merged)} vs {int(target.sum())}")
    if merged[spec.cols].isna().any().any():
        missing = int(merged[spec.cols].isna().any(axis=1).sum())
        raise RuntimeError(f"{dimension}: donor merge produced {missing} missing rows")
    idx = merged["index"].to_numpy(int)
    out.loc[idx, spec.cols] = merged[spec.cols].to_numpy()
    allowed = pd.Series(False, index=out.index)
    allowed.loc[idx] = True
    return out, allowed


def circular_halfwidth(frame: pd.DataFrame) -> np.ndarray:
    return ((frame["dir_95"].astype(float).to_numpy() - frame["dir_05"].astype(float).to_numpy()) % 360.0) / 2.0


def apply_center_frozen_direction_width_response(
    frame: pd.DataFrame,
    target: pd.Series,
    *,
    max_shrink_deg: float,
    min_halfwidth_deg: float,
    speed_floor: float = 0.45,
    halfwidth_floor: float = 0.30,
    level_weights: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    out = frame.copy()
    idx = out.index[target]
    sub = out.loc[idx].copy()
    hw = circular_halfwidth(sub)
    speed = sub["q50"].astype(float).to_numpy()
    speed_rank = sub.groupby(["level", "hour"])["q50"].rank(pct=True).to_numpy()
    hw_rank = pd.Series(hw, index=sub.index).groupby([sub["level"].astype(str), sub["hour"].astype(int)]).rank(pct=True).to_numpy()
    strength = np.clip((speed_rank - speed_floor) / max(1.0 - speed_floor, 1e-6), 0.0, 1.0) * np.clip(
        (hw_rank - halfwidth_floor) / max(1.0 - halfwidth_floor, 1e-6),
        0.0,
        1.0,
    )
    if level_weights:
        weights = sub["level"].astype(str).map(level_weights).fillna(1.0).to_numpy(float)
        strength *= weights
    # Keep calm/low-confidence rows unchanged; direction shrink is only for the
    # over-wide, high-wind concentration regime.
    shrink = np.minimum(max_shrink_deg * np.clip(strength, 0.0, 1.0), np.maximum(hw - min_halfwidth_deg, 0.0))
    changed = shrink > 0.05
    new_hw = hw - shrink
    centers = sub["dir_50"].astype(float).to_numpy()
    changed_idx = idx[changed]
    out.loc[changed_idx, "dir_05"] = np.round((centers[changed] - new_hw[changed]) % 360.0, 1)
    out.loc[changed_idx, "dir_95"] = np.round((centers[changed] + new_hw[changed]) % 360.0, 1)
    allowed = pd.Series(False, index=out.index)
    allowed.loc[changed_idx] = True
    stats = {
        "target_rows": int(target.sum()),
        "changed_rows": int(changed.sum()),
        "mean_halfwidth_before": float(np.mean(hw)),
        "mean_halfwidth_after_on_target": float(np.mean(new_hw)),
        "mean_shrink_changed_rows": float(np.mean(shrink[changed])) if changed.any() else 0.0,
        "max_shrink_deg": float(max_shrink_deg),
        "min_halfwidth_deg": float(min_halfwidth_deg),
        "speed_floor": float(speed_floor),
        "halfwidth_floor": float(halfwidth_floor),
    }
    return out, allowed, stats
