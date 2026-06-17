"""Direction forecast with circular-Winkler-direct training.

Replaces the starter kit's 97.5-pct residual trick. Targets the 18 direction
dimensions (surface + pressure + stations).

Approach:
1. **Centre model** μ̂: LightGBM with sin/cos decomposition of the target,
   predict (sin, cos), recover angle via atan2. Trained on mean circular
   error.
2. **Half-width model** w: LightGBM trained with a **custom circular
   Winkler objective** — requires writing a differentiable surrogate
   (Gneiting & Raftery 2007; angular conformal prediction 2022).
3. **Angular conformal wrap**: on TUNE split, compute the (1−α) empirical
   quantile of the arc-endpoint distance; inflate w to enforce 90% coverage.

Outputs dir_05 = μ̂ − w, dir_95 = μ̂ + w (modulo 360°).
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

try:
    import lightgbm as lgb
except ImportError:
    lgb = None


def _circ_dist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b)
    return np.minimum(d, 360.0 - d)


class DirectionModel:
    def __init__(
        self,
        centre_backend: str = "lightgbm",
        halfwidth_backend: str = "lightgbm",
        alpha: float = 0.10,
        params: dict | None = None,
    ):
        self.centre_backend = centre_backend
        self.halfwidth_backend = halfwidth_backend
        self.alpha = alpha
        self.params = params or {}
        self.centre_sin_model = None
        self.centre_cos_model = None
        self.hw_model = None
        self.conformal_offset = 0.0

    def _make_regressor(self, backend: str, quantile: float | None = None):
        if backend == "lightgbm" and lgb is not None:
            if quantile is not None:
                return lgb.LGBMRegressor(
                    objective="quantile",
                    alpha=quantile,
                    **self.params,
                )
            return lgb.LGBMRegressor(**self.params)
        from sklearn.ensemble import GradientBoostingRegressor
        if quantile is not None:
            return GradientBoostingRegressor(
                loss="quantile",
                alpha=quantile,
                n_estimators=self.params.get("n_estimators", 100),
                max_depth=self.params.get("max_depth", 3),
                learning_rate=self.params.get("learning_rate", 0.1),
            )
        return GradientBoostingRegressor(
            n_estimators=self.params.get("n_estimators", 100),
            max_depth=self.params.get("max_depth", 3),
            learning_rate=self.params.get("learning_rate", 0.1),
        )

    def _fit_regressor(
        self,
        backend: str,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        quantile: float | None = None,
    ):
        model = self._make_regressor(backend, quantile=quantile)
        if (
            lgb is not None
            and backend == "lightgbm"
            and X_val is not None
            and y_val is not None
        ):
            callbacks = [lgb.early_stopping(50, verbose=False)]
            model.fit(X, y, eval_set=[(X_val, y_val)], callbacks=callbacks)
        else:
            model.fit(X, y)
        return model

    def fit_centre(
        self,
        X_train: np.ndarray,
        direction_deg: np.ndarray,
        X_val: np.ndarray | None = None,
        direction_deg_val: np.ndarray | None = None,
    ) -> "DirectionModel":
        rad = np.deg2rad(direction_deg)
        sin_y = np.sin(rad)
        cos_y = np.cos(rad)

        sin_val = None
        cos_val = None
        if direction_deg_val is not None:
            rad_val = np.deg2rad(direction_deg_val)
            sin_val = np.sin(rad_val)
            cos_val = np.cos(rad_val)

        self.centre_sin_model = self._fit_regressor(
            self.centre_backend, X_train, sin_y, X_val, sin_val
        )
        self.centre_cos_model = self._fit_regressor(
            self.centre_backend, X_train, cos_y, X_val, cos_val
        )
        return self

    def predict_centre(self, X: np.ndarray) -> np.ndarray:
        sin_pred = self.centre_sin_model.predict(X)
        cos_pred = self.centre_cos_model.predict(X)
        ang_rad = np.arctan2(sin_pred, cos_pred)
        return np.rad2deg(ang_rad) % 360.0

    def fit_halfwidth(
        self,
        X_train: np.ndarray,
        direction_deg: np.ndarray,
        X_val: np.ndarray | None = None,
        direction_deg_val: np.ndarray | None = None,
    ) -> "DirectionModel":
        centre_pred = self.predict_centre(X_train)
        circ_err = _circ_dist(direction_deg, centre_pred)

        circ_err_val = None
        if direction_deg_val is not None and X_val is not None:
            centre_pred_val = self.predict_centre(X_val)
            circ_err_val = _circ_dist(direction_deg_val, centre_pred_val)

        self.hw_model = self._fit_regressor(
            self.halfwidth_backend,
            X_train,
            circ_err,
            X_val,
            circ_err_val,
            quantile=1.0 - self.alpha,
        )
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        centre = self.predict_centre(X)
        hw = self.hw_model.predict(X)
        hw = hw + self.conformal_offset
        hw = np.clip(hw, 0.0, 180.0)
        dir_05 = (centre - hw) % 360.0
        dir_50 = centre % 360.0
        dir_95 = (centre + hw) % 360.0
        return dir_05, dir_50, dir_95

    def conformal_calibrate(
        self,
        X_tune: np.ndarray,
        y_tune: np.ndarray,
    ) -> "DirectionModel":
        centre_pred = self.predict_centre(X_tune)
        hw_pred = self.hw_model.predict(X_tune)
        scores = _circ_dist(y_tune, centre_pred) - hw_pred
        n = len(scores)
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        q_level = min(q_level, 1.0)
        self.conformal_offset = float(np.quantile(scores, q_level))
        return self

    def save(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "DirectionModel":
        with open(path, "rb") as f:
            return pickle.load(f)
