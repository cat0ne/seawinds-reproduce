from __future__ import annotations

import numpy as np


def winkler_score(
    actual: np.ndarray,
    q_lo: np.ndarray,
    q_hi: np.ndarray,
    alpha: float = 0.1,
) -> float:
    width = q_hi - q_lo
    below = actual < q_lo
    above = actual > q_hi
    penalty = np.where(
        below,
        (2 / alpha) * (q_lo - actual),
        np.where(above, (2 / alpha) * (actual - q_hi), 0.0),
    )
    return float(np.nanmean(width + penalty))


def winkler_score_per_sample(
    actual: np.ndarray,
    q_lo: np.ndarray,
    q_hi: np.ndarray,
    alpha: float = 0.1,
) -> np.ndarray:
    width = q_hi - q_lo
    below = actual < q_lo
    above = actual > q_hi
    penalty = np.where(
        below,
        (2 / alpha) * (q_lo - actual),
        np.where(above, (2 / alpha) * (actual - q_hi), 0.0),
    )
    return width + penalty


def _circ_dist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b)
    return np.minimum(d, 360.0 - d)


def _is_in_arc(
    actual: np.ndarray,
    dir_lo: np.ndarray,
    dir_hi: np.ndarray,
    w: np.ndarray,
) -> np.ndarray:
    return (actual - dir_lo) % 360 <= w


def circular_winkler_score(
    actual: np.ndarray,
    dir_lo: np.ndarray,
    dir_hi: np.ndarray,
    alpha: float = 0.1,
) -> float:
    w = (dir_hi - dir_lo) % 360.0
    in_arc = _is_in_arc(actual, dir_lo, dir_hi, w)
    d_lo = _circ_dist(actual, dir_lo)
    d_hi = _circ_dist(actual, dir_hi)
    d_miss = np.minimum(d_lo, d_hi)
    penalty = (2 / alpha) * d_miss * (~in_arc)
    return float(np.nanmean(w + penalty))


def circular_winkler_per_sample(
    actual: np.ndarray,
    dir_lo: np.ndarray,
    dir_hi: np.ndarray,
    alpha: float = 0.1,
) -> np.ndarray:
    w = (dir_hi - dir_lo) % 360.0
    in_arc = _is_in_arc(actual, dir_lo, dir_hi, w)
    d_lo = _circ_dist(actual, dir_lo)
    d_hi = _circ_dist(actual, dir_hi)
    d_miss = np.minimum(d_lo, d_hi)
    penalty = (2 / alpha) * d_miss * (~in_arc)
    return w + penalty
