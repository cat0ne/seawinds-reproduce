"""Analog Ensemble (AnEn) for long-lead wind intervals.

HRES stops at d10, so d14 pressure-speed needs a fallback that is still
flow-dependent. AnEn searches historical states that look like the current
forecast context and uses the verified historical outcomes as an empirical
predictive distribution.

The implementation below is deliberately small and CPU-first:
- standardise predictors from the training archive;
- build nearest-neighbour indexes per optional group, for example
  `(region, level, hour)` or `(lead_days, month)`;
- fall back to a global index when a group has too little history;
- return q05/q50/q95 plus basic diagnostics for cherry-pick decisions.

Only provided competition data should feed the historical archive.
"""

from __future__ import annotations

from dataclasses import dataclass
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree


@dataclass(frozen=True)
class AnalogPrediction:
    """Container for empirical quantiles and neighbour diagnostics."""

    q05: np.ndarray
    q50: np.ndarray
    q95: np.ndarray
    mean_distance: np.ndarray
    n_neighbors: np.ndarray

    def as_tuple(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return the three quantile arrays for legacy callers."""
        return self.q05, self.q50, self.q95


class AnalogEnsemble:
    """Nearest-neighbour empirical interval model.

    Parameters
    ----------
    k:
        Requested number of analogs per prediction row.
    predictors:
        Numeric columns used for nearest-neighbour distance.
    target_col:
        Verified historical outcome used to form empirical quantiles.
    group_cols:
        Optional columns used to build local indexes. Prediction falls back to
        the global index when a group is missing or too small.
    min_group_size:
        Minimum rows required to build a group-specific index.
    quantiles:
        Quantiles returned by :meth:`predict_distribution`.
    """

    def __init__(
        self,
        k: int = 30,
        predictors: tuple[str, ...] = ("msl_anom", "z700", "ws10_recent"),
        target_col: str = "target",
        group_cols: tuple[str, ...] = ("lead_days",),
        min_group_size: int | None = None,
        quantiles: tuple[float, float, float] = (0.05, 0.50, 0.95),
    ):
        if k < 1:
            raise ValueError("k must be >= 1")
        self.k = k
        self.predictors = tuple(predictors)
        self.target_col = target_col
        self.group_cols = tuple(group_cols)
        self.min_group_size = min_group_size or k
        self.quantiles = quantiles
        self.historical_df: pd.DataFrame | None = None
        self.trees: dict[tuple, BallTree] = {}
        self.targets: dict[tuple, np.ndarray] = {}
        self.group_sizes: dict[tuple, int] = {}
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self._pred_cols: list[str] = []

    @property
    def fitted(self) -> bool:
        return self.historical_df is not None and bool(self.trees)

    @staticmethod
    def _global_key() -> tuple[str]:
        return ("__all__",)

    @staticmethod
    def _normalize_group_key(values: object) -> tuple:
        if isinstance(values, tuple):
            return values
        return (values,)

    def fit(self, historical_df: pd.DataFrame) -> "AnalogEnsemble":
        """Fit nearest-neighbour indexes from a historical archive."""
        if historical_df.empty:
            raise ValueError("historical_df must not be empty")
        if self.target_col not in historical_df.columns:
            raise ValueError(f"historical_df must contain a '{self.target_col}' column")

        self.historical_df = historical_df.copy()
        pred_cols = [c for c in self.predictors if c in self.historical_df.columns]
        if not pred_cols:
            raise ValueError("None of the requested predictors are present")
        self._pred_cols = pred_cols

        means = self.historical_df[pred_cols].mean(numeric_only=True).fillna(0.0)
        stds = (
            self.historical_df[pred_cols]
            .std(numeric_only=True)
            .replace(0.0, 1.0)
            .fillna(1.0)
        )
        self.means = means.to_dict()
        self.stds = stds.to_dict()
        scaled = self._prepare_predictors(self.historical_df)

        self.trees.clear()
        self.targets.clear()
        self.group_sizes.clear()

        valid_target = np.isfinite(pd.to_numeric(self.historical_df[self.target_col], errors="coerce"))
        if not valid_target.any():
            raise ValueError(f"'{self.target_col}' has no finite training values")

        self._fit_group(self._global_key(), scaled.loc[valid_target], self.historical_df.loc[valid_target])

        usable_group_cols = [c for c in self.group_cols if c in self.historical_df.columns]
        if usable_group_cols:
            grouped = self.historical_df.loc[valid_target].groupby(usable_group_cols, dropna=False, sort=False)
            for raw_key, group in grouped:
                key = self._normalize_group_key(raw_key)
                if len(group) >= self.min_group_size:
                    self._fit_group(key, scaled.loc[group.index], group)

        return self

    def _fit_group(self, key: tuple, X: pd.DataFrame, group: pd.DataFrame) -> None:
        values = X.to_numpy(dtype=np.float32)
        targets = group[self.target_col].to_numpy(dtype=np.float32)
        self.trees[key] = BallTree(values)
        self.targets[key] = targets
        self.group_sizes[key] = len(group)

    def _prepare_predictors(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._pred_cols:
            raise RuntimeError("AnalogEnsemble is not fitted")
        out = df.reindex(columns=self._pred_cols).copy()
        for col in self._pred_cols:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            mean = self.means[col]
            std = self.stds[col]
            out[col] = (out[col].fillna(mean) - mean) / std
        return out

    def _group_key_for_row(self, row: pd.Series, target_lead_days: int | None) -> tuple:
        values = []
        for col in self.group_cols:
            if col == "lead_days" and col not in row.index:
                values.append(target_lead_days)
            elif col in row.index:
                values.append(row[col])
            else:
                return self._global_key()
        if not values:
            return self._global_key()
        return tuple(values)

    def _query_group(self, key: tuple, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
        tree = self.trees.get(key)
        targets = self.targets.get(key)
        if tree is None or targets is None:
            tree = self.trees[self._global_key()]
            targets = self.targets[self._global_key()]
        k = min(self.k, len(targets))
        distances, indices = tree.query(X, k=k)
        return targets[indices], distances, k

    def predict_distribution(
        self,
        context_df: pd.DataFrame,
        target_lead_days: int | None = None,
    ) -> AnalogPrediction:
        """Predict empirical quantiles and neighbour diagnostics."""
        if not self.fitted:
            raise RuntimeError("AnalogEnsemble must be fitted before prediction")
        if context_df.empty:
            empty = np.array([], dtype=float)
            return AnalogPrediction(empty, empty, empty, empty, empty.astype(int))

        X_all = self._prepare_predictors(context_df)
        q_values = [[] for _ in self.quantiles]
        mean_distances: list[float] = []
        n_neighbors: list[int] = []

        if self.group_cols:
            keys = [
                self._group_key_for_row(row, target_lead_days)
                for _, row in context_df.iterrows()
            ]
        else:
            keys = [self._global_key()] * len(context_df)

        for idx, key in enumerate(keys):
            X = X_all.iloc[[idx]].to_numpy(dtype=np.float32)
            neighbor_targets, distances, k_used = self._query_group(key, X)
            quantile_values = np.nanquantile(neighbor_targets[0], self.quantiles)
            for q_list, value in zip(q_values, quantile_values):
                q_list.append(float(value))
            mean_distances.append(float(np.nanmean(distances[0])))
            n_neighbors.append(int(k_used))

        return AnalogPrediction(
            q05=np.asarray(q_values[0], dtype=float),
            q50=np.asarray(q_values[1], dtype=float),
            q95=np.asarray(q_values[2], dtype=float),
            mean_distance=np.asarray(mean_distances, dtype=float),
            n_neighbors=np.asarray(n_neighbors, dtype=int),
        )

    def predict(
        self,
        context_df: pd.DataFrame,
        target_lead_days: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return q05/q50/q95 arrays for compatibility with existing callers."""
        return self.predict_distribution(context_df, target_lead_days).as_tuple()

    def blend_weight(
        self,
        lead_days: int,
        weights: dict | None = None,
    ) -> float:
        if weights is not None and lead_days in weights:
            return float(weights[lead_days])
        return min(lead_days / 14.0, 1.0)

    @staticmethod
    def blend_quantiles(
        base: tuple[np.ndarray, np.ndarray, np.ndarray],
        analog: tuple[np.ndarray, np.ndarray, np.ndarray],
        analog_weight: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Blend two speed interval forecasts and enforce quantile ordering."""
        w = float(np.clip(analog_weight, 0.0, 1.0))
        arrays = []
        for base_q, analog_q in zip(base, analog):
            arrays.append((1.0 - w) * np.asarray(base_q) + w * np.asarray(analog_q))
        stacked = np.sort(np.column_stack(arrays), axis=1)
        q05 = np.maximum(stacked[:, 0], 0.0)
        q50 = stacked[:, 1]
        q95 = stacked[:, 2]
        return q05, q50, q95

    def save(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "AnalogEnsemble":
        with open(path, "rb") as f:
            return pickle.load(f)
