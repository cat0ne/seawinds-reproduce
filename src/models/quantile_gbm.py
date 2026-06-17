"""Gradient-boosted quantile regression with LightGBM and CatBoost.

Separate models for q05 and q95. Pinball loss at alpha/2 and 1-alpha/2
is the direct Winkler minimiser — no CRPS training.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Literal

import numpy as np
import lightgbm as lgb

LGBM_PARAMS = {
    "n_estimators": 1000,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 50,
    "verbose": -1,
    "n_jobs": -1,
}


class QuantileGBM:
    def __init__(
        self,
        quantiles: tuple[float, float, float] = (0.05, 0.50, 0.95),
        backend: Literal["lightgbm", "catboost"] = "lightgbm",
        params: dict | None = None,
    ):
        self.quantiles = quantiles
        self.backend = backend
        self.params = {**LGBM_PARAMS, **(params or {})}
        self.models: dict[float, object] = {}

    def fit(
        self,
        X_train: np.ndarray | pd.DataFrame,
        y_train: np.ndarray | pd.Series,
        X_val: np.ndarray | pd.DataFrame | None = None,
        y_val: np.ndarray | pd.Series | None = None,
        early_stopping_rounds: int = 50,
    ) -> "QuantileGBM":
        if isinstance(y_train, pd.Series):
            y_train = y_train.values
        if isinstance(y_val, pd.Series):
            y_val = y_val.values

        for q in self.quantiles:
            self.models[q] = self._fit_single(
                X_train, y_train, q, X_val, y_val, early_stopping_rounds
            )
        return self

    def _fit_single(self, X, y, quantile, X_val, y_val, stopping_rounds):
        if self.backend == "lightgbm":
            return self._fit_lgbm(X, y, quantile, X_val, y_val, stopping_rounds)
        else:
            return self._fit_catboost(X, y, quantile, X_val, y_val, stopping_rounds)

    def _fit_lgbm(self, X, y, quantile, X_val, y_val, stopping_rounds):
        callbacks = []
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
            callbacks.append(lgb.early_stopping(stopping_rounds, verbose=False))

        model = lgb.LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            **self.params,
        )
        model.fit(X, y, eval_set=eval_set, callbacks=callbacks)
        return model

    def _fit_catboost(self, X, y, quantile, X_val, y_val, stopping_rounds):
        from catboost import CatBoostRegressor, Pool

        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = Pool(X_val, y_val)

        model = CatBoostRegressor(
            loss_function=f"Quantile:alpha={quantile}",
            iterations=self.params.get("n_estimators", 1000),
            depth=self.params.get("max_depth", 6),
            learning_rate=self.params.get("learning_rate", 0.05),
            verbose=0,
            early_stopping_rounds=stopping_rounds,
        )
        model.fit(X, y, eval_set=eval_set, verbose=0)
        return model

    def predict(self, X) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        q_lo, q_mid, q_hi = self.quantiles
        p_lo = self.models[q_lo].predict(X)
        p_mid = self.models[q_mid].predict(X)
        p_hi = self.models[q_hi].predict(X)

        stacked = np.column_stack([p_lo, p_mid, p_hi])
        stacked.sort(axis=1)
        return stacked[:, 0], stacked[:, 1], stacked[:, 2]

    def predict_quantile(self, X, quantile: float) -> np.ndarray:
        if quantile not in self.models:
            raise ValueError(f"Model not fitted for quantile {quantile}")
        return self.models[quantile].predict(X)

    def save(self, path: Path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "model.pkl", "wb") as f:
            pickle.dump(self, f)
        meta = {
            "quantiles": list(self.quantiles),
            "backend": self.backend,
            "params": self.params,
        }
        with open(path / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "QuantileGBM":
        path = Path(path)
        with open(path / "model.pkl", "rb") as f:
            return pickle.load(f)


import pandas as pd
