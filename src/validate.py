from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.paths import (
    HOLDOUT_END,
    HOLDOUT_START,
    HORIZONS,
    HOURS,
    REGIONS,
    TRAIN_END,
    TRAIN_START,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)
from src.scoring.evaluate import (
    build_pressure_gt,
    build_station_gt,
    build_surface_gt,
    evaluate_predictions,
)


SPLITS = {
    "train": (TRAIN_START, TRAIN_END),
    "val": (VAL_START, VAL_END),
    "tune": (TUNE_START, TUNE_END),
    "holdout": (HOLDOUT_START, HOLDOUT_END),
}


def get_split_dates(split: str) -> tuple[str, str]:
    return SPLITS[split]


def filter_predictions_by_split(
    preds: pd.DataFrame,
    split: str,
) -> pd.DataFrame:
    start, end = get_split_dates(split)
    preds = preds.copy()
    preds["time"] = pd.to_datetime(preds["time"])
    max_horizon = max(HORIZONS)
    valid_start = pd.Timestamp(start) + pd.Timedelta(days=max_horizon)
    valid_end = pd.Timestamp(end)
    return preds[
        (preds["time"] >= valid_start)
        & (preds["time"] <= valid_end)
    ].copy()


def score_model(
    preds: pd.DataFrame,
    split: str = "val",
    gt_cache: dict | None = None,
    data_dir=None,
) -> pd.DataFrame:
    start, end = get_split_dates(split)

    if gt_cache is None:
        gt_cache = {}

    gt_surface = gt_cache.get("surface", {})
    gt_pressure = gt_cache.get("pressure", {})
    gt_stations = gt_cache.get("stations", {})

    for region in REGIONS:
        if region not in gt_surface:
            gt_surface[region] = build_surface_gt(region, data_dir, start, end)
        if region not in gt_pressure:
            gt_pressure[region] = build_pressure_gt(region, data_dir, start, end)
        if region not in gt_stations:
            gt_stations[region] = build_station_gt(region, data_dir, start, end)

    gt_cache["surface"] = gt_surface
    gt_cache["pressure"] = gt_pressure
    gt_cache["stations"] = gt_stations

    filtered = filter_predictions_by_split(preds, split)
    if filtered.empty:
        print(f"WARNING: No predictions for split '{split}'")
        return pd.DataFrame(columns=["dimension", "score"])

    scores = evaluate_predictions(
        filtered,
        gt_surface=gt_surface,
        gt_pressure=gt_pressure,
        gt_stations=gt_stations,
        data_dir=data_dir,
    )
    return scores


def format_score_table(
    *score_dfs: tuple[pd.DataFrame, str],
) -> pd.DataFrame:
    merged = None
    for df, label in score_dfs:
        col = df.set_index("dimension")["score"].rename(label)
        if merged is None:
            merged = col.to_frame()
        else:
            merged = merged.join(col, how="outer")

    if merged is None:
        return pd.DataFrame()

    merged = merged.reset_index()
    merged = merged.sort_values("dimension")

    problem_order = {"speed": 0, "dir": 1}
    gt_order = {"stations": 0, "surface": 1, "pressure": 2}
    region_order = {"ns": 0, "ecs": 1}

    def _sort_key(dim):
        parts = dim.split("_")
        prob = parts[0]
        gt = parts[1]
        horizon = int(parts[2][1:])
        reg = parts[3]
        return (problem_order.get(prob, 9), gt_order.get(gt, 9), horizon, region_order.get(reg, 9))

    merged["_sort"] = merged["dimension"].apply(_sort_key)
    merged = merged.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)
    return merged


def print_score_summary(scores: pd.DataFrame, label: str = ""):
    if scores.empty:
        print(f"{'[' + label + '] ' if label else ''}No scores to display")
        return

    header = f"{'[' + label + '] ' if label else ''}36-dim score breakdown"
    print(f"\n{'=' * 70}")
    print(f" {header}")
    print(f"{'=' * 70}")
    print(f" {'Dimension':<35} {'Score':>10}")
    print(f" {'-' * 35} {'-' * 10}")

    for _, row in scores.iterrows():
        dim = row["dimension"]
        score = row["score"]
        if np.isfinite(score):
            print(f" {dim:<35} {score:>10.4f}")
        else:
            print(f" {dim:<35} {'N/A':>10}")

    valid_scores = scores["score"].dropna()
    valid_scores = valid_scores[np.isfinite(valid_scores)]
    if len(valid_scores) > 0:
        print(f" {'-' * 35} {'-' * 10}")
        print(f" {'Mean score (not rank):':<35} {valid_scores.mean():>10.4f}")
        print(f" {'Dimensions scored:':<35} {len(valid_scores):>10}")
    print(f"{'=' * 70}\n")
