"""Lane A: von Mises kappa-MLE direction width utilities.

Per-(level, hour) cell flow for the ECS pressure d7 pilot:

  1. Pool circular residuals ``actual_dir - HRES_dir`` over TRAIN window.
  2. Bin by HRES forecast speed using empirical quantiles (6 bins, coarsen
     downward until every bin has >= 200 obs).
  3. Fit kappa via MLE (R_bar formula with R_bar clamp) per bin.
  4. Fit isotonic regression on (bin_midpoint_speed, kappa) to enforce
     monotone-increasing kappa (high speed = tight direction).
  5. At inference, look up kappa from the isotonic curve given the inference
     speed, derive a half-width from the precomputed kappa -> hw lookup, and
     apply ``dir_05/dir_95 = wrap(dir_50 +/- hw)`` only where the regime gate
     allows.

The estimator is dir_50 frozen by construction: only dir_05/dir_95 move.

Speed scale: HRES sqrt(u^2 + v^2) at both train and inference, so the
isotonic curve is queried in the same units it was fit on. This avoids the
scale mismatch from using v207's calibrated q50 (which is reanalysis-anchored).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import vonmises
from sklearn.isotonic import IsotonicRegression


# --- Half-width lookup (kappa -> half-width in degrees at alpha=0.05/0.95) ---

_KAPPA_GRID = np.concatenate([
    np.array([1e-3]),
    np.logspace(-2, 3, 401),  # 0.01 .. 1000
])


def _build_hw_lookup(quantile: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
    """Half-width in degrees as a function of kappa.

    vonmises.ppf(q, kappa) returns radians measured from the mean direction.
    Half-width = ppf(q) for the upper tail with q=0.95. (Equivalently
    (ppf(0.95) - ppf(0.05)) / 2 by symmetry of the distribution.)
    """
    hw_rad = vonmises.ppf(quantile, _KAPPA_GRID)
    hw_deg = np.degrees(hw_rad)
    # Numerical noise: as kappa -> 0, hw_deg -> ~171 (95% of 180); clip to safe.
    hw_deg = np.clip(hw_deg, 0.0, 180.0)
    return _KAPPA_GRID.copy(), hw_deg


KAPPA_GRID, HW_GRID_DEG = _build_hw_lookup(0.95)


def vm_hw_fast(kappa: np.ndarray | float) -> np.ndarray:
    """Vectorized kappa -> half-width (degrees) using precomputed lookup."""
    k = np.atleast_1d(np.asarray(kappa, dtype=float))
    k_clipped = np.clip(k, KAPPA_GRID[0], KAPPA_GRID[-1])
    # Lookup is monotone decreasing in kappa, but np.interp requires increasing xp;
    # since KAPPA_GRID is increasing and HW_GRID_DEG is monotone decreasing,
    # np.interp(k, KAPPA_GRID, HW_GRID_DEG) works correctly.
    return np.interp(k_clipped, KAPPA_GRID, HW_GRID_DEG)


# --- Circular math (kappa estimation) ---

def _wrap_180(deg: np.ndarray) -> np.ndarray:
    """Wrap to (-180, 180]."""
    return ((np.asarray(deg, dtype=float) + 180.0) % 360.0) - 180.0


def signed_delta(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """Smallest signed angular difference, in degrees, in (-180, 180]."""
    return _wrap_180(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float))


def compute_kappa(residual_deg: np.ndarray) -> float:
    """MLE-style kappa from circular residuals.

    Uses the closed-form approximation
        kappa_hat = R_bar (2 - R_bar^2) / (1 - R_bar^2)
    with R_bar clamped away from {0, 1} to avoid singularities.

    NOTE: We do NOT subtract a mean residual first. The bias-induced spread
    is part of the predictive uncertainty we want to capture, since dir_50
    is frozen at the (uncorrected) HRES/v207 center.
    """
    arr = np.asarray(residual_deg, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return float("nan")
    rad = np.deg2rad(arr)
    c_bar = float(np.mean(np.cos(rad)))
    s_bar = float(np.mean(np.sin(rad)))
    r_bar = float(np.sqrt(c_bar * c_bar + s_bar * s_bar))
    # Clamp to avoid 0 (uniform) and 1 (degenerate Dirac) edge cases.
    eps = 1e-3
    r_clip = float(np.clip(r_bar, eps, 1.0 - eps))
    kappa = r_clip * (2.0 - r_clip * r_clip) / (1.0 - r_clip * r_clip)
    return float(kappa)


# --- Estimator (per cell) ---

@dataclass
class VonMisesKappaEstimator:
    """Fit kappa as a monotone-increasing function of speed for one cell.

    Each (level, hour) ECS pressure d7 cell gets its own estimator.

    fit() takes paired (speed, residual_deg) arrays from TRAIN. predict() takes
    speeds and returns kappa values (interpolated, monotone in speed).
    """

    n_bins: int = 6
    min_obs_per_bin: int = 200
    min_bins: int = 3
    # Filled after fit():
    bin_edges: np.ndarray = field(default_factory=lambda: np.array([]))
    bin_midpoints: np.ndarray = field(default_factory=lambda: np.array([]))
    bin_kappas: np.ndarray = field(default_factory=lambda: np.array([]))
    bin_counts: np.ndarray = field(default_factory=lambda: np.array([]))
    isotonic: IsotonicRegression | None = None
    n_train: int = 0
    global_kappa: float = float("nan")
    fit_status: str = "unfit"

    def fit(self, speed: np.ndarray, residual_deg: np.ndarray) -> "VonMisesKappaEstimator":
        speed = np.asarray(speed, dtype=float)
        residual_deg = np.asarray(residual_deg, dtype=float)
        mask = np.isfinite(speed) & np.isfinite(residual_deg)
        speed = speed[mask]
        residual_deg = residual_deg[mask]
        self.n_train = int(speed.size)

        # Always compute a global kappa as fallback.
        self.global_kappa = compute_kappa(residual_deg)

        # Find max bin count satisfying min_obs_per_bin floor.
        chosen_bins = 0
        for n in range(self.n_bins, self.min_bins - 1, -1):
            quantiles = np.linspace(0.0, 1.0, n + 1)
            edges = np.quantile(speed, quantiles)
            # Coalesce duplicate edges (low-variance speed) by uniqueness.
            edges = np.unique(edges)
            if len(edges) < self.min_bins + 1:
                continue
            # Use bin assignment per row
            assign = np.clip(np.searchsorted(edges[1:-1], speed, side="right"), 0, len(edges) - 2)
            counts = np.bincount(assign, minlength=len(edges) - 1)
            if (counts >= self.min_obs_per_bin).all():
                chosen_bins = len(edges) - 1
                self.bin_edges = edges
                self.bin_counts = counts.astype(int)
                break

        if chosen_bins == 0:
            # No binning achievable; degrade to a constant kappa = global.
            self.bin_edges = np.array([speed.min(), speed.max()]) if speed.size else np.array([0.0, 1.0])
            self.bin_midpoints = np.array([float(np.median(speed)) if speed.size else 0.0])
            self.bin_kappas = np.array([self.global_kappa])
            self.bin_counts = np.array([self.n_train], dtype=int)
            self.isotonic = None
            self.fit_status = "global_only"
            return self

        # Compute per-bin kappa & midpoints
        assign = np.clip(np.searchsorted(self.bin_edges[1:-1], speed, side="right"), 0, chosen_bins - 1)
        midpoints = []
        kappas = []
        for b in range(chosen_bins):
            sel = assign == b
            mid = float(np.median(speed[sel]))
            k = compute_kappa(residual_deg[sel])
            midpoints.append(mid)
            kappas.append(k)
        self.bin_midpoints = np.array(midpoints, dtype=float)
        self.bin_kappas = np.array(kappas, dtype=float)

        # Fit isotonic regression: speed midpoint -> kappa (monotone increasing).
        valid = np.isfinite(self.bin_midpoints) & np.isfinite(self.bin_kappas)
        if valid.sum() < 2:
            self.isotonic = None
            self.fit_status = "global_only"
            return self

        # Ensure strictly increasing x for isotonic (jitter ties if necessary).
        x = self.bin_midpoints[valid].copy()
        y = self.bin_kappas[valid].copy()
        order = np.argsort(x)
        x = x[order]
        y = y[order]
        # Add tiny perturbation for duplicate x.
        for i in range(1, len(x)):
            if x[i] <= x[i - 1]:
                x[i] = x[i - 1] + 1e-6

        iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
        iso.fit(x, y)
        self.isotonic = iso
        self.fit_status = f"bins={chosen_bins}"
        return self

    def predict_kappa(self, speed: np.ndarray) -> np.ndarray:
        s = np.asarray(speed, dtype=float)
        out = np.full_like(s, self.global_kappa, dtype=float)
        if self.isotonic is not None:
            mask = np.isfinite(s)
            out[mask] = self.isotonic.predict(s[mask])
        # Replace any non-finite with global kappa fallback.
        bad = ~np.isfinite(out)
        if bad.any():
            out[bad] = self.global_kappa
        return out

    def to_dict(self) -> dict:
        return {
            "fit_status": self.fit_status,
            "n_train": int(self.n_train),
            "n_bins": int(len(self.bin_midpoints)),
            "bin_edges": [float(x) for x in self.bin_edges.tolist()],
            "bin_midpoints": [float(x) for x in self.bin_midpoints.tolist()],
            "bin_kappas": [float(x) for x in self.bin_kappas.tolist()],
            "bin_counts": [int(x) for x in self.bin_counts.tolist()],
            "global_kappa": float(self.global_kappa) if np.isfinite(self.global_kappa) else None,
        }


# --- Width-response application (matching apply_center_frozen pattern) ---

def _circular_halfwidth(dir_05: np.ndarray, dir_95: np.ndarray) -> np.ndarray:
    return ((np.asarray(dir_95, dtype=float) - np.asarray(dir_05, dtype=float)) % 360.0) / 2.0


@dataclass(frozen=True)
class RegimeGate:
    hw_ratio_lo: float = 0.70
    hw_ratio_hi: float = 1.50
    min_movement_deg: float = 2.0
    speed_rank_floor: float = 0.15
    wrap_zone_deg: float = 30.0


def apply_vm_width_response(
    frame: pd.DataFrame,
    target: pd.Series,
    *,
    speed_by_row: np.ndarray,  # same length as frame, used for kappa lookup
    kappa_by_cell: dict[tuple[str, int], VonMisesKappaEstimator],
    regime: RegimeGate = RegimeGate(),
    speed_floor_value: float = 5.0,
    halfwidth_floor: float = 5.0,
    halfwidth_ceiling: float = 175.0,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Apply per-cell kappa-derived half-widths to direction endpoints.

    Args:
        frame: base predictions DataFrame.
        target: boolean Series, True for rows in the ECS / pressure / d7 / grid scope.
        speed_by_row: HRES forecast speed (or whichever) for kappa lookup. Length == len(frame).
            Values outside target rows are ignored.
        kappa_by_cell: dict mapping (level_str, hour_int) -> fitted VonMisesKappaEstimator.
        regime: RegimeGate config.
        speed_floor_value: skip rows below this absolute speed (m/s).
        halfwidth_floor / halfwidth_ceiling: hard clip for derived hw, deg.

    Returns:
        out: candidate DataFrame (dir_05/dir_95 modified on accepted rows).
        allowed: boolean Series, True for rows actually changed.
        stats: diagnostics dict.
    """
    out = frame.copy()
    idx = out.index[target]
    if len(idx) == 0:
        return out, pd.Series(False, index=out.index), {"target_rows": 0, "changed_rows": 0}

    sub = out.loc[idx].copy()
    sub_levels = sub["level"].astype(str).to_numpy()
    sub_hours = sub["hour"].astype(int).to_numpy()
    sub_speed = np.asarray(speed_by_row, dtype=float)[target.values]
    sub_dir50 = sub["dir_50"].astype(float).to_numpy()
    v207_hw = _circular_halfwidth(sub["dir_05"].astype(float).to_numpy(), sub["dir_95"].astype(float).to_numpy())

    # Speed rank within (level, hour), matching v191/v196 convention.
    speed_rank = (
        pd.Series(sub_speed, index=sub.index)
        .groupby([sub["level"].astype(str), sub["hour"].astype(int)])
        .rank(pct=True)
        .to_numpy()
    )

    # Distance from 0/360 boundary
    dir50_wrap = np.minimum(sub_dir50, 360.0 - sub_dir50)

    # Compute candidate kappa & hw per row.
    candidate_kappa = np.full(len(sub), np.nan, dtype=float)
    cells_covered = 0
    cells_missing: list[tuple[str, int]] = []
    unique_pairs = pd.unique(list(zip(sub_levels.tolist(), sub_hours.tolist())))
    seen = set()
    for level_val, hour_val in zip(sub_levels, sub_hours):
        key = (str(level_val), int(hour_val))
        if key in seen:
            continue
        seen.add(key)
        if key not in kappa_by_cell:
            cells_missing.append(key)
            continue
        cells_covered += 1
    for key, estimator in kappa_by_cell.items():
        level_val, hour_val = key
        mask = (sub_levels == str(level_val)) & (sub_hours == int(hour_val))
        if mask.any():
            candidate_kappa[mask] = estimator.predict_kappa(sub_speed[mask])

    finite_kappa = np.isfinite(candidate_kappa)
    candidate_hw = np.full(len(sub), np.nan, dtype=float)
    if finite_kappa.any():
        candidate_hw[finite_kappa] = vm_hw_fast(candidate_kappa[finite_kappa])

    # Clip to safe range, but track which rows were clipped.
    valid_hw = np.isfinite(candidate_hw)
    clipped_low = valid_hw & (candidate_hw < halfwidth_floor)
    clipped_high = valid_hw & (candidate_hw > halfwidth_ceiling)
    candidate_hw_clipped = candidate_hw.copy()
    candidate_hw_clipped[clipped_low] = halfwidth_floor
    candidate_hw_clipped[clipped_high] = halfwidth_ceiling

    # Regime gate.
    movement = np.abs(candidate_hw_clipped - v207_hw)
    ratio = np.where(v207_hw > 0, candidate_hw_clipped / np.maximum(v207_hw, 1e-6), 1.0)

    gate = (
        valid_hw
        & np.isfinite(sub_speed)
        & (sub_speed >= speed_floor_value)
        & (ratio >= regime.hw_ratio_lo)
        & (ratio <= regime.hw_ratio_hi)
        & (movement > regime.min_movement_deg)
        & (speed_rank > regime.speed_rank_floor)
        & (dir50_wrap > regime.wrap_zone_deg)
    )

    # Apply changes.
    new_hw = candidate_hw_clipped[gate]
    centers = sub_dir50[gate]
    changed_idx = idx[gate]
    out.loc[changed_idx, "dir_05"] = np.round(((centers - new_hw) % 360.0), 1)
    out.loc[changed_idx, "dir_95"] = np.round(((centers + new_hw) % 360.0), 1)
    allowed = pd.Series(False, index=out.index)
    allowed.loc[changed_idx] = True

    # Failure reason counts (for diagnostics).
    fail_invalid_hw = int((~valid_hw).sum())
    fail_low_speed = int((valid_hw & (sub_speed < speed_floor_value)).sum())
    fail_ratio = int((valid_hw & ((ratio < regime.hw_ratio_lo) | (ratio > regime.hw_ratio_hi))).sum())
    fail_movement = int((valid_hw & (movement <= regime.min_movement_deg)).sum())
    fail_speed_rank = int((valid_hw & (speed_rank <= regime.speed_rank_floor)).sum())
    fail_wrap = int((valid_hw & (dir50_wrap <= regime.wrap_zone_deg)).sum())

    stats = {
        "target_rows": int(target.sum()),
        "changed_rows": int(gate.sum()),
        "activation_rate": float(gate.mean()) if len(gate) > 0 else 0.0,
        "cells_with_estimator": cells_covered,
        "cells_missing_estimator": [list(x) for x in cells_missing],
        "speed_floor_value": float(speed_floor_value),
        "halfwidth_floor_deg": float(halfwidth_floor),
        "halfwidth_ceiling_deg": float(halfwidth_ceiling),
        "regime": {
            "hw_ratio_lo": regime.hw_ratio_lo,
            "hw_ratio_hi": regime.hw_ratio_hi,
            "min_movement_deg": regime.min_movement_deg,
            "speed_rank_floor": regime.speed_rank_floor,
            "wrap_zone_deg": regime.wrap_zone_deg,
        },
        "candidate_hw_deg": {
            "mean_all_valid": float(np.nanmean(candidate_hw)) if valid_hw.any() else None,
            "median_all_valid": float(np.nanmedian(candidate_hw)) if valid_hw.any() else None,
            "clipped_low_rows": int(clipped_low.sum()),
            "clipped_high_rows": int(clipped_high.sum()),
        },
        "v207_hw_deg": {
            "mean": float(np.mean(v207_hw)),
            "median": float(np.median(v207_hw)),
        },
        "movement_deg_on_changed": {
            "mean": float(np.mean(movement[gate])) if gate.any() else 0.0,
            "median": float(np.median(movement[gate])) if gate.any() else 0.0,
            "max": float(np.max(movement[gate])) if gate.any() else 0.0,
        },
        "mean_shrink_on_changed": float(np.mean(v207_hw[gate] - new_hw)) if gate.any() else 0.0,
        "frac_widened_rows": float(np.mean(new_hw > v207_hw[gate])) if gate.any() else 0.0,
        "gate_failure_counts": {
            "invalid_hw": fail_invalid_hw,
            "below_speed_floor": fail_low_speed,
            "ratio_out_of_band": fail_ratio,
            "movement_too_small": fail_movement,
            "speed_rank_too_low": fail_speed_rank,
            "in_wrap_zone": fail_wrap,
        },
    }
    return out, allowed, stats
