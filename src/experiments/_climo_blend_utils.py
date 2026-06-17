"""Lane D climatology-blend utilities.

Mirrors the pattern of ``apply_center_frozen_direction_width_response`` from
``_post_v185_utils`` but uses TRAIN-period circular climatology halfwidths as
the widening target instead of a fixed deg cap.

Hard rules enforced:
    - ``dir_50`` never changes.
    - widths only WIDEN (never shrink) when climatology is wider than model.
    - widening is symmetric around ``dir_50`` (we cannot move centers).

The blend operates on station rows only (one target dimension at a time). The
8 windows of the leaderboard each map to a single calendar month at d14, so we
derive each row's ``month`` from a window -> date table built from inference
feature files.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import FEATURES_DIR, HOURS  # noqa: E402

CLIMO_PATH = FEATURES_DIR / "climo_stations_direction_m_h.parquet"


def load_station_climatology(path: Path | str = CLIMO_PATH) -> pd.DataFrame:
    """Load the climatology table produced by ``lane_d_aggregate_station_climatology``."""
    df = pd.read_parquet(path)
    required = {"region", "station", "month", "hour", "circ_mean_dir", "p05", "p95", "halfwidth", "level"}
    missing = required.difference(df.columns)
    if missing:
        raise RuntimeError(f"Climatology file missing columns: {missing}")
    df["month"] = df["month"].astype(int)
    df["hour"] = df["hour"].astype(int)
    return df


def window_month_table(regions: tuple[str, ...] = ("north_sea", "east_china_sea"), horizon: int = 14) -> pd.DataFrame:
    """Build a (window, hour, month) lookup from inference feature files.

    Each window file has a single ``time`` value (the forecast issue date). At
    horizon ``h`` and offset ``hour``, the target month is computed by adding
    ``timedelta(days=h, hours=hour)``. The lookup is identical across regions
    in practice but we accept ``regions`` for robustness and verify equality.
    """
    rows: list[dict] = []
    for window in range(1, 9):
        per_region_dates: list[pd.Timestamp] = []
        for region in regions:
            path = FEATURES_DIR / f"inference_window_{window}_{region}.parquet"
            df = pd.read_parquet(path, columns=["time"])
            issue_date = pd.Timestamp(df["time"].iloc[0])
            per_region_dates.append(issue_date)
        if len(set(per_region_dates)) != 1:
            raise RuntimeError(f"Inference window {window} dates differ across regions: {per_region_dates}")
        issue_date = per_region_dates[0]
        for hour in HOURS:
            target_time = issue_date + pd.Timedelta(days=int(horizon), hours=int(hour))
            rows.append(
                {
                    "window": int(window),
                    "hour": int(hour),
                    "month": int(target_time.month),
                    "issue_date": issue_date,
                    "target_time": target_time,
                }
            )
    return pd.DataFrame(rows)


def _lookup_climo_halfwidth(
    sub: pd.DataFrame,
    climo: pd.DataFrame,
    month_col: str = "month",
) -> tuple[np.ndarray, np.ndarray]:
    """Resolve climatology halfwidth for each row via sm_h -> sh -> rh fallback.

    Returns ``(halfwidth, level_code)`` arrays aligned with ``sub.index``.
    ``level_code`` is 2 for ``sm_h``, 1 for ``sh``, 0 for ``rh``, -1 if missing.
    """
    sm_h = climo[climo["level"] == "sm_h"].copy()
    sh = climo[climo["level"] == "sh"].copy()
    rh = climo[climo["level"] == "rh"].copy()

    sm_h_map = sm_h.set_index(["region", "station", "month", "hour"])["halfwidth"].to_dict()
    sh_map = sh.set_index(["region", "station", "hour"])["halfwidth"].to_dict()
    rh_map = rh.set_index(["region", "hour"])["halfwidth"].to_dict()

    regions = sub["region"].astype(str).to_numpy()
    stations = sub["station"].astype(str).to_numpy()
    months = sub[month_col].astype(int).to_numpy()
    hours = sub["hour"].astype(int).to_numpy()

    hw = np.full(len(sub), np.nan, dtype=float)
    lvl = np.full(len(sub), -1, dtype=int)

    for i in range(len(sub)):
        key_sm = (regions[i], stations[i], int(months[i]), int(hours[i]))
        val = sm_h_map.get(key_sm)
        if val is not None and np.isfinite(val):
            hw[i] = float(val)
            lvl[i] = 2
            continue
        key_sh = (regions[i], stations[i], int(hours[i]))
        val = sh_map.get(key_sh)
        if val is not None and np.isfinite(val):
            hw[i] = float(val)
            lvl[i] = 1
            continue
        key_rh = (regions[i], int(hours[i]))
        val = rh_map.get(key_rh)
        if val is not None and np.isfinite(val):
            hw[i] = float(val)
            lvl[i] = 0
            continue
    return hw, lvl


def apply_speed_conditioned_climatology_width_blend(
    frame: pd.DataFrame,
    target: pd.Series,
    climo: pd.DataFrame,
    *,
    speed_floor: float = 0.15,
    halfwidth_floor: float = 0.05,
    max_widen_deg: float = 20.0,
    max_halfwidth_deg: float = 179.0,
    window_month: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Widen ``dir_05/dir_95`` toward climatology when climo is wider.

    Mirrors ``apply_center_frozen_direction_width_response`` but in the
    *widening* direction. Strength gate is the product of speed rank and
    halfwidth rank within ``(hour,)`` groups of the target rows (stations have
    no level dimension).

    Parameters
    ----------
    frame : pd.DataFrame
        Full predictions frame (untouched outside ``target``).
    target : pd.Series of bool
        Mask selecting which rows of ``frame`` to potentially modify.
    climo : pd.DataFrame
        Output of :func:`load_station_climatology`.
    speed_floor, halfwidth_floor : float
        Lower percentile thresholds (in [0, 1]) below which the gate is zero.
    max_widen_deg : float
        Cap on the per-row widening in degrees (single-sided halfwidth).
    max_halfwidth_deg : float
        Absolute cap on the resulting halfwidth (so we never reach full circle).
    window_month : pd.DataFrame, optional
        Pre-built (window, hour, month) table. If None, derived on the fly.
    """
    out = frame.copy()
    idx = out.index[target]
    sub = out.loc[idx].copy()

    if window_month is None:
        window_month = window_month_table()
    wm = window_month[["window", "hour", "month"]].astype({"window": int, "hour": int, "month": int})
    sub_keys = sub[["window", "hour"]].astype({"window": int, "hour": int}).reset_index()
    merged = sub_keys.merge(wm, on=["window", "hour"], how="left", validate="many_to_one")
    if merged["month"].isna().any():
        raise RuntimeError("window/hour month lookup produced NaN entries")
    merged = merged.set_index("index")
    sub["month"] = merged.loc[sub.index, "month"].astype(int).to_numpy()

    # Current model halfwidth (model dir_05->dir_95 arc).
    model_hw = ((sub["dir_95"].astype(float).to_numpy() - sub["dir_05"].astype(float).to_numpy()) % 360.0) / 2.0

    # Climatology halfwidth lookup with fallback chain.
    climo_hw, climo_level = _lookup_climo_halfwidth(sub, climo, month_col="month")
    if np.isnan(climo_hw).any():
        n_missing = int(np.isnan(climo_hw).sum())
        raise RuntimeError(f"Climatology lookup missing for {n_missing} rows after fallback")

    # Gate: speed rank x halfwidth rank within each hour of target rows.
    speed_rank = sub.groupby("hour")["q50"].rank(pct=True).to_numpy(float)
    hw_series = pd.Series(model_hw, index=sub.index)
    hw_rank = hw_series.groupby(sub["hour"].astype(int)).rank(pct=True).to_numpy(float)
    strength = np.clip((speed_rank - speed_floor) / max(1.0 - speed_floor, 1e-6), 0.0, 1.0) * np.clip(
        (hw_rank - halfwidth_floor) / max(1.0 - halfwidth_floor, 1e-6),
        0.0,
        1.0,
    )

    # Desired widen is positive only where climo is wider than model.
    raw_gap = climo_hw - model_hw
    raw_widen = np.where(raw_gap > 0.0, raw_gap, 0.0)
    widen = np.minimum(raw_widen * strength, max_widen_deg)
    # Respect absolute halfwidth cap (never go past max_halfwidth_deg).
    widen = np.minimum(widen, np.maximum(max_halfwidth_deg - model_hw, 0.0))

    changed = widen > 0.05
    new_hw = model_hw + widen
    centers = sub["dir_50"].astype(float).to_numpy()
    changed_idx = idx[changed]

    out.loc[changed_idx, "dir_05"] = np.round((centers[changed] - new_hw[changed]) % 360.0, 1)
    out.loc[changed_idx, "dir_95"] = np.round((centers[changed] + new_hw[changed]) % 360.0, 1)

    allowed = pd.Series(False, index=out.index)
    allowed.loc[changed_idx] = True

    stats = {
        "target_rows": int(target.sum()),
        "changed_rows": int(changed.sum()),
        "mean_model_halfwidth": float(np.mean(model_hw)),
        "mean_climo_halfwidth": float(np.mean(climo_hw)),
        "mean_climo_minus_model_halfwidth": float(np.mean(climo_hw - model_hw)),
        "frac_rows_climo_wider": float(np.mean(raw_gap > 0.0)),
        "mean_widen_changed_rows": float(np.mean(widen[changed])) if changed.any() else 0.0,
        "max_widen_changed_rows": float(np.max(widen[changed])) if changed.any() else 0.0,
        "mean_halfwidth_after_on_target": float(np.mean(new_hw)),
        "max_widen_deg": float(max_widen_deg),
        "max_halfwidth_deg": float(max_halfwidth_deg),
        "speed_floor": float(speed_floor),
        "halfwidth_floor": float(halfwidth_floor),
        "climo_level_counts": {
            "sm_h": int((climo_level == 2).sum()),
            "sh": int((climo_level == 1).sum()),
            "rh": int((climo_level == 0).sum()),
        },
    }
    return out, allowed, stats
