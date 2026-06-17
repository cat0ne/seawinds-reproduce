"""Custom LightGBM objective for circular Winkler score minimisation.

The DirectionModel half-width regressor works on circular error radii.
This objective keeps the original Winkler trade-off but replaces the hard
hinge with a smooth softplus surrogate so LightGBM gets usable gradients.

Approach:
- Predict half-width ``w`` directly.
- Penalise narrow intervals with the exact circular Winkler hinge.
- Use a softplus relaxation around the miss boundary for stable gradients.
"""
from __future__ import annotations

import numpy as np


def circular_winkler_objective(preds: np.ndarray, train_data) -> tuple[np.ndarray, np.ndarray]:
    alpha = 0.1
    y = train_data.get_label()
    w = np.clip(np.abs(preds), 1.0, 180.0)

    margin = y - w
    sigma = 2.0
    sigmoid = 1.0 / (1.0 + np.exp(-margin / sigma))
    grad = 2.0 - (2.0 / alpha) * sigmoid
    hess = (2.0 / alpha) * sigmoid * (1.0 - sigmoid) / sigma
    hess = np.clip(hess, 1e-6, None)

    return grad, hess


def circular_winkler_eval(preds: np.ndarray, train_data) -> tuple[str, float, bool]:
    alpha = 0.1
    y = train_data.get_label()
    w = np.abs(preds)
    w = np.clip(w, 1.0, 180.0)

    margin = y - w
    miss_dist = np.maximum(margin, 0.0)
    loss = 2.0 * w + (2.0 / alpha) * miss_dist

    return "cws", float(np.mean(loss)), False
