"""Phase A WS1 — heavy starting-kit, ECS-only, with checkpointing + replay output.

Wave 1A scaffold (do NOT launch full training from this commit).

Adapted from `starting-kit/phase_1/_heavy_extracted.py` for two purposes:

  1. Reconstruct a faithful v59 replay base on val/tune/holdout for the
     ECS surface cell (10m + 100m) at horizons d1/d7/d14, by re-running
     the same heavy pipeline that produced `predictions_heavy.csv` —
     v59's surface grid was byte-equal to predictions_heavy.csv.

  2. Side-by-side schema-sanity check via the original 8 hidden-2022
     inference windows (NOT byte-equal under default --train-end; see
     --byteequal flag for the hidden-byte-equal mode).

Key differences vs. the original heavy notebook:

  * REGIONS = ["north_sea"] only (cuts cost in half).
  * Model checkpointing under logs/heavy_ns/{region}/...:
      - speed/{level}/{target}_q{quantile}.cbm  (CatBoost native)
      - dir/{horizon}/{sin|cos}_{tgt}.pkl       (LightGBM pickle)
      - selected_features_per_level.json
    Re-runs skip retraining if the file already exists.
  * Default train cutoff = 2020-09-30 (replay-safe). Eval set carved from
    the last month of train (2020-09) so early stopping doesn't touch
    val/tune/holdout. --byteequal switches to year==2021 eval (leakage
    against val/tune/holdout, but reproduces the notebook).
  * Two inference modes: --infer-hidden (8 windows → outputs/heavy_ecs_hidden.csv)
    and --infer-replay (val/tune/holdout dates from train features →
    replay_base/v59_surface_d7_ns.parquet, keyed by target_time).
  * Standalone Python script — no notebook chdir hack; uses absolute
    PROJECT_ROOT-relative paths.

CLI:
  --dry-run        load data, report shapes, stop (no training, no inference).
  --estimate       train one CatBoost (700hPa, 10m target, q=0.5), report wall-clock.
  --train          train all CatBoost speed + LGBM direction models (idempotent).
  --infer-hidden   run hidden-2022 8-window inference (writes ECS rows only).
  --infer-replay   run val/tune/holdout inference (writes replay parquet).
  --all            --train + --infer-hidden + --infer-replay.
  --byteequal      use 2019-2020 train + year==2021 eval (notebook-faithful;
                   leaks for replay use). Default is leakage-safe.
"""

from __future__ import annotations

import json
import os
import pickle
import sys
import time as _time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STARTING_KIT_DIR = PROJECT_ROOT / "starting-kit" / "phase_1"

# Ensure starting-kit utils.py is importable
if str(STARTING_KIT_DIR) not in sys.path:
    sys.path.insert(0, str(STARTING_KIT_DIR))

import lightgbm as lgb  # noqa: E402
from catboost import CatBoostRegressor  # noqa: E402

from utils import (  # noqa: E402
    HORIZONS,
    HOURS,
    PRESSURE_LEVELS,
    QUANTILES_DEFAULT,
    add_direction_intervals,
    attach_station_predictions,
    circular_mae,
    compute_direction_intervals,
    compute_feature_selection,
    exclude_worldwide_features,
    load_inference_features,
    load_train_data,
    load_vertical_ratios,
    merge_speed_direction,
    predict_direction,
    winkler_score,
)

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REGIONS = ["north_sea"]
DATA_DIR = PROJECT_ROOT / "data" / "phase1_dataset"
FEATURES_DIR = DATA_DIR / "features"
TRAIN_DIR = DATA_DIR / "train"
INFERENCE_DIR = DATA_DIR / "inference"
SCORING_DIR = DATA_DIR / "scoring"
CHECKPOINT_ROOT = PROJECT_ROOT / "logs" / "heavy_ecs"
OUTPUT_HIDDEN_CSV_REPLAY = PROJECT_ROOT / "outputs" / "heavy_ns_hidden_replay.csv"
OUTPUT_HIDDEN_CSV_BYTEEQUAL = PROJECT_ROOT / "outputs" / "heavy_ns_hidden_byteequal.csv"
REPLAY_PARQUET = PROJECT_ROOT / "replay_base" / "v59_surface_d7_ns.parquet"
# Filename promises d7-only; only horizon=7 rows are written. d1/d14 models are
# still trained and can be reused via the same checkpoints if a wider replay
# parquet is needed later (drop REPLAY_HORIZON_FILTER and re-run --infer-replay).
REPLAY_HORIZON_FILTER = 7

ALL_LEVELS = ["10m", "100m"] + [str(lev) for lev in PRESSURE_LEVELS]
SURFACE_LEVELS = ["10m", "100m"]
QUANTILES = QUANTILES_DEFAULT  # [0.05, 0.5, 0.95]
TOP_K_HEAVY = {1: 15, 7: 20, 14: 25}
MAX_TRAIN_SAMPLES = 500_000

# Replay window (val + tune + holdout)
REPLAY_START = pd.Timestamp("2020-10-01")
REPLAY_END = pd.Timestamp("2021-12-31")

# Default leakage-safe train cutoff (matches src/data/paths.TRAIN_END)
DEFAULT_TRAIN_END = pd.Timestamp("2020-09-30")
# Replay-mode eval set: last month of training. 2020-09 keeps signal close to val.
REPLAY_EVAL_START = pd.Timestamp("2020-09-01")
REPLAY_EVAL_END = pd.Timestamp("2020-09-30")

# Byte-equal mode (notebook-faithful): train years 2019+2020 fully, eval=year 2021
BYTEEQUAL_TRAIN_YEARS = [2019, 2020]
BYTEEQUAL_EVAL_YEAR = 2021


# ---------------------------------------------------------------------------
# Small CLI
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> dict:
    flags = {
        "dry_run": "--dry-run" in argv,
        "estimate": "--estimate" in argv,
        "train": "--train" in argv or "--all" in argv,
        "infer_hidden": "--infer-hidden" in argv or "--all" in argv,
        "infer_replay": "--infer-replay" in argv or "--all" in argv,
        "byteequal": "--byteequal" in argv,
    }
    if not any(flags.values()):
        # default = dry-run
        flags["dry_run"] = True
    return flags


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(regions: list[str]) -> dict:
    data = {}
    for region in regions:
        df, feature_cols, speed_targets, dir_targets = load_train_data(FEATURES_DIR, region)
        data[region] = (df, feature_cols, speed_targets, dir_targets)
        print(f"[load] {region}: shape={df.shape}  "
              f"time {df['time'].min().date()} → {df['time'].max().date()}  "
              f"feats={len(feature_cols)}  speed_t={len(speed_targets)}  "
              f"dir_t={len(dir_targets)}  grid_pts={df.groupby(['latitude','longitude']).ngroups}")
    return data


def build_level_targets(region: str, data: dict) -> dict:
    """Build wind speed targets at non-10m levels for one region. Same as notebook."""
    print(f"[lvl] Building level targets for {region}...")
    t0 = _time.time()

    surface_cols = ["time", "latitude", "longitude", "u100", "v100"]
    reanalysis_surf = pd.read_parquet(
        TRAIN_DIR / f"reanalysis_{region}_6h.parquet", columns=surface_cols
    )
    reanalysis_surf["time"] = pd.to_datetime(reanalysis_surf["time"])
    reanalysis_surf["ws_100m"] = np.sqrt(
        reanalysis_surf["u100"] ** 2 + reanalysis_surf["v100"] ** 2
    )
    reanalysis_surf.drop(columns=["u100", "v100"], inplace=True)
    print(f"[lvl]   surface 6h: {len(reanalysis_surf):,} rows")

    reanalysis_pres = pd.read_parquet(TRAIN_DIR / f"reanalysis_pressure_{region}.parquet")
    reanalysis_pres["time"] = pd.to_datetime(reanalysis_pres["time"])
    for lev in PRESSURE_LEVELS:
        reanalysis_pres[f"ws_{lev}"] = np.sqrt(
            reanalysis_pres[f"u_{lev}"] ** 2 + reanalysis_pres[f"v_{lev}"] ** 2
        )
    ws_cols = ["time", "latitude", "longitude"] + [f"ws_{lev}" for lev in PRESSURE_LEVELS]
    reanalysis_pres = reanalysis_pres[ws_cols]
    print(f"[lvl]   pressure: {len(reanalysis_pres):,} rows")

    ws_all = reanalysis_surf.merge(
        reanalysis_pres, on=["time", "latitude", "longitude"], how="inner"
    )

    df_feat = data[region][0]
    context_dates = df_feat[["time", "latitude", "longitude"]].copy()
    context_dates["latitude"] = context_dates["latitude"].round(2)
    context_dates["longitude"] = context_dates["longitude"].round(2)

    ws_all["latitude"] = ws_all["latitude"].round(2)
    ws_all["longitude"] = ws_all["longitude"].round(2)
    ws_all = ws_all.set_index(["time", "latitude", "longitude"]).sort_index()

    level_targets = {}
    for level_str in ["100m"] + [str(lev) for lev in PRESSURE_LEVELS]:
        ws_col = f"ws_{level_str}" if level_str != "100m" else "ws_100m"
        target_rows = []
        for h in HORIZONS:
            for hr in HOURS:
                tgt_name = f"speed_d{h}_h{hr}"
                offset = pd.Timedelta(days=h, hours=hr)
                future_times = context_dates["time"] + offset
                keys = pd.DataFrame({
                    "time": future_times,
                    "latitude": context_dates["latitude"].values,
                    "longitude": context_dates["longitude"].values,
                })
                keys_idx = pd.MultiIndex.from_frame(keys)
                ws_vals = ws_all[ws_col].reindex(keys_idx).values
                target_rows.append((tgt_name, ws_vals))

        tgt_df = context_dates[["time", "latitude", "longitude"]].copy()
        for tgt_name, vals in target_rows:
            tgt_df[tgt_name] = vals

        n_valid = tgt_df.iloc[:, 3:].notna().sum().sum()
        n_total = tgt_df.iloc[:, 3:].size
        print(f"[lvl]   {level_str}: {n_valid:,}/{n_total:,} valid "
              f"({100*n_valid/n_total:.1f}%)")
        level_targets[level_str] = tgt_df

    print(f"[lvl]   done in {_time.time()-t0:.0f}s")
    return level_targets


# ---------------------------------------------------------------------------
# Feature selection (per-level)
# ---------------------------------------------------------------------------
def compute_or_load_selection(
    region: str,
    data: dict,
    level_targets: dict,
    train_end: pd.Timestamp,
    *,
    byteequal: bool,
) -> dict:
    """Per-level feature selection. Reuses notebook cache only in byteequal
    mode (since the project cache was computed on full 2019-2020, which leaks
    val under our replay-mode train_end of 2020-09-30). In replay mode, computes
    on the truncated window and caches under logs/heavy_ns/."""
    project_cache = FEATURES_DIR / f"selected_features_heavy_per_level_{region}.json"
    local_cache = CHECKPOINT_ROOT / region / "selected_features_per_level.json"

    if local_cache.exists():
        print(f"[sel] Loading cached per-level selection: {local_cache}")
        return json.loads(local_cache.read_text())

    if byteequal and project_cache.exists():
        print(f"[sel] byteequal mode: reusing project cache {project_cache.name}")
        sel = json.loads(project_cache.read_text())
        local_cache.parent.mkdir(parents=True, exist_ok=True)
        local_cache.write_text(json.dumps(sel, indent=2))
        return sel

    print(f"[sel] Computing per-level feature selection (train ≤ {train_end.date()})...")
    df, feature_cols, speed_targets, _ = data[region]
    feature_cols_speed = exclude_worldwide_features(feature_cols)

    sel_per_level = {}
    for level_str in ALL_LEVELS:
        if level_str == "10m":
            df_for_sel = df
        else:
            lev_tgt = level_targets[region][level_str]
            tgt_cols = [c for c in lev_tgt.columns if c.startswith("speed_d")]
            df_for_sel = df[[c for c in df.columns if c not in tgt_cols]].copy()
            df_for_sel = df_for_sel.join(lev_tgt[tgt_cols], how="left")

        # Restrict to training window before selection
        df_for_sel = df_for_sel[df_for_sel["time"] <= train_end]

        sel_level = compute_feature_selection(
            df_for_sel, feature_cols_speed, speed_targets,
            model_type="lgbm", top_k=TOP_K_HEAVY,
        )
        sel_per_level[level_str] = sel_level
        print(f"[sel]   {level_str}: {len(sel_level)} target selections")

    local_cache.parent.mkdir(parents=True, exist_ok=True)
    local_cache.write_text(json.dumps(sel_per_level, indent=2))
    print(f"[sel] Saved: {local_cache}")
    return sel_per_level


# ---------------------------------------------------------------------------
# Train/eval index split
# ---------------------------------------------------------------------------
def build_splits(
    region: str,
    data: dict,
    *,
    byteequal: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str], np.ndarray, np.ndarray]:
    """Return (df_train, df_eval, feat_speed, feat_dir, train_idx, eval_idx).

    Replay mode (default):
      train: time <= 2020-09-30  (excluding REPLAY_EVAL_START..REPLAY_EVAL_END)
      eval:  2020-09-01..2020-09-30  (last month, used only for early stopping)

    Byte-equal mode:
      train: year in [2019, 2020]
      eval:  year == 2021  (matches the notebook; leaks against val/tune/holdout)
    """
    df, feature_cols, _, _ = data[region]

    if byteequal:
        train_mask = df["time"].dt.year.isin(BYTEEQUAL_TRAIN_YEARS)
        eval_mask = df["time"].dt.year == BYTEEQUAL_EVAL_YEAR
    else:
        train_mask = (df["time"] <= DEFAULT_TRAIN_END) & ~(
            (df["time"] >= REPLAY_EVAL_START) & (df["time"] <= REPLAY_EVAL_END)
        )
        eval_mask = (df["time"] >= REPLAY_EVAL_START) & (df["time"] <= REPLAY_EVAL_END)

    train_idx = df.index[train_mask].to_numpy()
    eval_idx = df.index[eval_mask].to_numpy()

    if len(train_idx) > MAX_TRAIN_SAMPLES:
        rng = np.random.RandomState(42)
        train_idx = np.sort(rng.choice(train_idx, size=MAX_TRAIN_SAMPLES, replace=False))

    df_train = df.loc[train_idx]
    df_eval = df.loc[eval_idx]

    feat_speed = exclude_worldwide_features(feature_cols)
    feat_dir = feature_cols

    print(f"[split] {region} ({'byteequal' if byteequal else 'replay'}): "
          f"train={len(df_train):,}  eval={len(df_eval):,}  "
          f"speed_feats={len(feat_speed)}  dir_feats={len(feat_dir)}")
    return df_train, df_eval, feat_speed, feat_dir, train_idx, eval_idx


# ---------------------------------------------------------------------------
# CatBoost speed training (with checkpointing)
# ---------------------------------------------------------------------------
def _cbm_path(region: str, level_str: str, tgt: str, q: float) -> Path:
    return CHECKPOINT_ROOT / region / "speed" / level_str / f"{tgt}_q{q:.2f}.cbm"


def _train_one_cb(
    X_tr: pd.DataFrame, y_tr: pd.Series,
    X_vl: pd.DataFrame, y_vl: pd.Series,
    quantile: float,
) -> CatBoostRegressor:
    m = CatBoostRegressor(
        loss_function=f"Quantile:alpha={quantile}",
        iterations=500,
        depth=7,
        learning_rate=0.05,
        l2_leaf_reg=3,
        random_seed=42,
        verbose=0,
    )
    m.fit(X_tr, y_tr, eval_set=(X_vl, y_vl), early_stopping_rounds=50)
    return m


def train_speed_models(
    region: str,
    data: dict,
    level_targets: dict,
    splits: tuple,
    sel_per_level: dict,
) -> dict:
    """Train + checkpoint all CatBoost quantile models for one region.

    Returns {level: {target: {q: model}}}.
    """
    df_train, df_eval, feat_speed, _, train_idx, eval_idx = splits
    _, _, speed_targets, _ = data[region]

    speed_models = {}
    t0_global = _time.time()

    for level_str in ALL_LEVELS:
        print(f"\n[cb] {region} / {level_str}: {len(speed_targets)} targets × {len(QUANTILES)} q")
        sel = sel_per_level[level_str]

        if level_str == "10m":
            y_src_tr = df_train
            y_src_vl = df_eval
        else:
            lev_tgt = level_targets[region][level_str]
            y_src_tr = lev_tgt.loc[train_idx]
            y_src_vl = lev_tgt.loc[eval_idx]

        level_models = {}
        for tgt in speed_targets:
            feats = sel.get(tgt, feat_speed)

            y_tr = y_src_tr[tgt]
            y_vl = y_src_vl[tgt]
            mask_tr = y_tr.notna()
            mask_vl = y_vl.notna()
            if mask_tr.sum() < 100:
                print(f"[cb]   {tgt}: skipped (n={mask_tr.sum()})")
                continue

            X_tr = df_train.loc[mask_tr.values, feats].fillna(0)
            y_tr = y_tr[mask_tr]
            X_vl = df_eval.loc[mask_vl.values, feats].fillna(0)
            y_vl = y_vl[mask_vl]

            models_q = {}
            for q in QUANTILES:
                ckpt = _cbm_path(region, level_str, tgt, q)
                ckpt.parent.mkdir(parents=True, exist_ok=True)
                if ckpt.exists():
                    m = CatBoostRegressor()
                    m.load_model(str(ckpt))
                else:
                    m = _train_one_cb(X_tr, y_tr, X_vl, y_vl, q)
                    m.save_model(str(ckpt))
                models_q[q] = m

            level_models[tgt] = models_q

            q05 = np.maximum(models_q[0.05].predict(X_vl), 0)
            q50 = models_q[0.5].predict(X_vl)
            q95 = models_q[0.95].predict(X_vl)
            rmse = float(np.sqrt(np.nanmean((y_vl.values - q50) ** 2)))
            ws = winkler_score(y_vl.values, q05, q95, alpha=0.1)
            print(f"[cb]   {tgt}: RMSE={rmse:.3f}  WS={ws:.3f}")

        speed_models[level_str] = level_models

    print(f"[cb] all levels done in {_time.time()-t0_global:.0f}s")
    return speed_models


# ---------------------------------------------------------------------------
# Direction training
# ---------------------------------------------------------------------------
def _dir_path(region: str, tgt: str, kind: str) -> Path:
    horizon = int(tgt.split("_")[1][1:])
    return CHECKPOINT_ROOT / region / "dir" / f"d{horizon}" / f"{kind}_{tgt}.pkl"


def train_dir_models(
    region: str,
    data: dict,
    splits: tuple,
) -> dict:
    """Train + checkpoint LightGBM sin/cos direction models. Returns
    {target: (m_sin, m_cos, dir_feats)}."""
    df_train, _, _, feat_dir, _, _ = splits
    _, _, _, dir_targets = data[region]

    out = {}
    for tgt in dir_targets:
        sin_path = _dir_path(region, tgt, "sin")
        cos_path = _dir_path(region, tgt, "cos")
        feats_path = _dir_path(region, tgt, "feats")

        if sin_path.exists() and cos_path.exists() and feats_path.exists():
            with sin_path.open("rb") as f:
                m_sin = pickle.load(f)
            with cos_path.open("rb") as f:
                m_cos = pickle.load(f)
            with feats_path.open("rb") as f:
                dir_feats = pickle.load(f)
            out[tgt] = (m_sin, m_cos, dir_feats)
            print(f"[dir]   {tgt}: loaded checkpoint")
            continue

        mask_tr = df_train[tgt].notna()
        if mask_tr.sum() < 100:
            continue

        X_sub = df_train.loc[mask_tr, feat_dir].fillna(0).sample(
            n=min(100_000, mask_tr.sum()), random_state=42
        )
        y_sub = df_train.loc[X_sub.index, tgt]
        m_imp = lgb.LGBMRegressor(n_estimators=50, max_depth=4, verbose=-1, n_jobs=-1)
        m_imp.fit(X_sub, np.sin(np.radians(y_sub)))
        dir_feats = pd.Series(
            m_imp.feature_importances_, index=feat_dir
        ).nlargest(25).index.tolist()

        X_tr = df_train.loc[mask_tr, dir_feats].fillna(0)
        y_tr_sin = np.sin(np.radians(df_train.loc[mask_tr, tgt]))
        y_tr_cos = np.cos(np.radians(df_train.loc[mask_tr, tgt]))

        params = dict(
            n_estimators=200, max_depth=7, learning_rate=0.05,
            subsample=0.8, verbose=-1, n_jobs=-1,
        )
        m_sin = lgb.LGBMRegressor(**params)
        m_cos = lgb.LGBMRegressor(**params)
        m_sin.fit(X_tr, y_tr_sin)
        m_cos.fit(X_tr, y_tr_cos)

        sin_path.parent.mkdir(parents=True, exist_ok=True)
        with sin_path.open("wb") as f:
            pickle.dump(m_sin, f)
        with cos_path.open("wb") as f:
            pickle.dump(m_cos, f)
        with feats_path.open("wb") as f:
            pickle.dump(dir_feats, f)

        out[tgt] = (m_sin, m_cos, dir_feats)
        print(f"[dir]   {tgt}: trained + saved")
    return out


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------
def predict_speed_at_level(features_df, level_models, selected_feats, feature_cols):
    """Same as notebook's predict_speed_at_level — predicts speed at one level."""
    rows = []
    for tgt, models_q in level_models.items():
        horizon = int(tgt.split("_")[1][1:])
        hour = int(tgt.split("_")[2][1:])
        feats = selected_feats.get(tgt, feature_cols)
        for c in feats:
            if c not in features_df.columns:
                features_df[c] = 0.0
        X = features_df[feats].fillna(0)

        q05 = np.maximum(models_q[0.05].predict(X), 0)
        q50 = models_q[0.5].predict(X)
        q95 = models_q[0.95].predict(X)

        for j in range(len(features_df)):
            rows.append({
                "latitude": round(float(features_df.iloc[j]["latitude"]), 2),
                "longitude": round(float(features_df.iloc[j]["longitude"]), 2),
                "horizon": horizon, "hour": hour,
                "q05": round(float(q05[j]), 4),
                "q50": round(float(q50[j]), 4),
                "q95": round(float(q95[j]), 4),
            })
    return pd.DataFrame(rows)


def infer_hidden(
    speed_models: dict,
    dir_models: dict,
    sel_per_level: dict,
    feature_cols_all: dict,
    vertical_ratios: dict,
    n_windows: int = 8,
) -> pd.DataFrame:
    """Replicate the original heavy submission pipeline on hidden 8 windows,
    ECS only. Outputs a DataFrame with the same column shape as predictions_heavy.csv
    (after attach_station_predictions)."""
    all_preds = []
    for wid in range(1, n_windows + 1):
        for region in REGIONS:
            df_inf = load_inference_features(FEATURES_DIR, wid, region)
            context_month = int(df_inf["time"].max().month)
            fcols = feature_cols_all[region]
            ratios_df = vertical_ratios.get(region)
            dir_preds = predict_direction(df_inf, dir_models[region], fcols)

            for level_str in ALL_LEVELS:
                level_models = speed_models[region].get(level_str, {})
                if not level_models:
                    continue
                sel = sel_per_level[region][level_str]
                preds = predict_speed_at_level(df_inf, level_models, sel, fcols)
                stacked = np.sort(preds[["q05", "q50", "q95"]].values, axis=1)
                preds["q05"] = stacked[:, 0]
                preds["q50"] = stacked[:, 1]
                preds["q95"] = stacked[:, 2]
                preds = merge_speed_direction(preds, dir_preds)

                if level_str != "10m" and ratios_df is not None:
                    if level_str in ratios_df["level"].values:
                        r_dir = ratios_df[
                            (ratios_df["level"] == level_str)
                            & (ratios_df["month"] == context_month)
                        ]
                        if "dir_clim" in r_dir.columns and len(r_dir) > 0:
                            r_dir = r_dir[["latitude", "longitude", "dir_clim"]].copy()
                            r_dir["latitude"] = r_dir["latitude"].astype(float).round(2)
                            r_dir["longitude"] = r_dir["longitude"].astype(float).round(2)
                            preds = preds.merge(
                                r_dir, on=["latitude", "longitude"], how="left"
                            )
                            has_clim = preds["dir_clim"].notna()
                            preds.loc[has_clim, "dir_50"] = preds.loc[
                                has_clim, "dir_clim"
                            ].round(1)
                            preds.drop(columns=["dir_clim"], inplace=True, errors="ignore")

                preds["level"] = level_str
                preds["window"] = wid
                preds["region"] = region
                all_preds.append(preds)

            print(f"[hidden] W{wid} {region}: emitted {len(ALL_LEVELS)} levels")

    sub = pd.concat(all_preds, ignore_index=True)
    sub = sub[
        ["window", "region", "latitude", "longitude", "horizon", "hour", "level",
         "q05", "q50", "q95", "dir_50"]
    ]
    sub["q05"] = sub["q05"].clip(lower=0)
    sub["q95"] = sub[["q50", "q95"]].max(axis=1)
    sub["q05"] = sub[["q05", "q50"]].min(axis=1)
    sub["dir_50"] = sub["dir_50"] % 360
    return sub


def infer_replay(
    speed_models: dict,
    sel_per_level: dict,
    data: dict,
    feature_cols_all: dict,
) -> pd.DataFrame:
    """Run replay inference on val/tune/holdout dates using the training-period
    reanalysis features (load_features-equivalent — load_train_data already gives
    us those rows). Speed-only output for surface (10m + 100m); direction is
    irrelevant for the speed_surface_d7 cell that this base will validate.

    Output schema (matches replay_base/v59_stations_d1_ns.parquet style):
      [target_time, region, level, horizon, hour, latitude, longitude, q05, q50, q95]
    """
    out_frames = []
    for region in REGIONS:
        df_full, feature_cols, _, _ = data[region]
        fcols = feature_cols_all[region]

        df_replay = df_full[
            (df_full["time"] >= REPLAY_START) & (df_full["time"] <= REPLAY_END)
        ].copy()
        print(f"[replay] {region}: {len(df_replay):,} rows  "
              f"({df_replay['time'].nunique()} unique context dates)")

        # Surface only — saves ~70% of inference work given we only need 10m + 100m
        for level_str in SURFACE_LEVELS:
            level_models = speed_models[region].get(level_str, {})
            if not level_models:
                continue
            sel = sel_per_level[region][level_str]
            for tgt, models_q in level_models.items():
                horizon = int(tgt.split("_")[1][1:])
                hour = int(tgt.split("_")[2][1:])
                feats = sel.get(tgt, fcols)
                for c in feats:
                    if c not in df_replay.columns:
                        df_replay[c] = 0.0
                X = df_replay[feats].fillna(0)
                q05 = np.maximum(models_q[0.05].predict(X), 0)
                q50 = models_q[0.5].predict(X)
                q95 = models_q[0.95].predict(X)
                # Sort q-row-wise to enforce monotonicity
                stacked = np.sort(np.column_stack([q05, q50, q95]), axis=1)
                # Build target_time = context_time + horizon days + hour
                offset = pd.Timedelta(days=horizon, hours=hour)
                target_time = df_replay["time"] + offset
                out_frames.append(pd.DataFrame({
                    "target_time": target_time.values,
                    "region": region,
                    "level": level_str,
                    "horizon": horizon,
                    "hour": hour,
                    "latitude": df_replay["latitude"].astype(float).round(2).values,
                    "longitude": df_replay["longitude"].astype(float).round(2).values,
                    "q05": stacked[:, 0],
                    "q50": stacked[:, 1],
                    "q95": stacked[:, 2],
                }))
                print(f"[replay]   {region} / {level_str} / {tgt}: "
                      f"{len(df_replay):,} preds")

    out = pd.concat(out_frames, ignore_index=True)

    # Tag splits for downstream consumers
    splits = pd.Series("hidden", index=out.index)
    splits.loc[out["target_time"] <= pd.Timestamp("2021-03-31")] = "val"
    splits.loc[
        (out["target_time"] > pd.Timestamp("2021-03-31"))
        & (out["target_time"] <= pd.Timestamp("2021-09-30"))
    ] = "tune"
    splits.loc[
        (out["target_time"] > pd.Timestamp("2021-09-30"))
        & (out["target_time"] <= pd.Timestamp("2021-12-31"))
    ] = "holdout"
    splits.loc[out["target_time"] <= pd.Timestamp("2020-09-30")] = "train"
    out["split"] = splits.values
    return out


# ---------------------------------------------------------------------------
# Single-model timing (for cost extrapolation)
# ---------------------------------------------------------------------------
def estimate_single_cb(
    region: str,
    data: dict,
    level_targets: dict,
    splits: tuple,
    sel_per_level: dict,
) -> float:
    """Train one CatBoost model (level=700hPa, target=speed_d1_h0, q=0.5) and
    return wall-clock seconds. Idempotent — uses checkpoint if present, BUT
    still reports timing for the train branch (returns 0.0 if loaded from cache)."""
    df_train, df_eval, feat_speed, _, train_idx, eval_idx = splits
    _, _, speed_targets, _ = data[region]
    level_str = "700"
    tgt = "speed_d1_h0"
    q = 0.5

    sel = sel_per_level[level_str]
    feats = sel.get(tgt, feat_speed)
    lev_tgt = level_targets[region][level_str]
    y_src_tr = lev_tgt.loc[train_idx]
    y_src_vl = lev_tgt.loc[eval_idx]

    y_tr = y_src_tr[tgt]
    y_vl = y_src_vl[tgt]
    mask_tr = y_tr.notna()
    mask_vl = y_vl.notna()
    X_tr = df_train.loc[mask_tr.values, feats].fillna(0)
    y_tr = y_tr[mask_tr]
    X_vl = df_eval.loc[mask_vl.values, feats].fillna(0)
    y_vl = y_vl[mask_vl]

    print(f"[est] X_tr={X_tr.shape}  X_vl={X_vl.shape}  feats={len(feats)}")

    ckpt = _cbm_path(region, level_str, tgt, q)
    if ckpt.exists():
        print(f"[est] checkpoint exists, removing for clean timing: {ckpt}")
        ckpt.unlink()

    t0 = _time.time()
    m = _train_one_cb(X_tr, y_tr, X_vl, y_vl, q)
    elapsed = _time.time() - t0
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    m.save_model(str(ckpt))
    print(f"[est] one CatBoost fit (q=0.5, level=700, tgt={tgt}): {elapsed:.1f}s")

    # Extrapolation: ECS only, 7 levels × 12 targets × 3 quantiles = 252 fits.
    n_total = len(ALL_LEVELS) * len(speed_targets) * len(QUANTILES)
    print(f"[est] extrapolated total CatBoost time: "
          f"{elapsed * n_total:.0f}s = {elapsed * n_total / 3600:.2f}h "
          f"(n={n_total})")
    return elapsed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    flags = _parse_args(argv)
    print(f"[main] flags: {flags}")

    train_end = (
        pd.Timestamp("2020-12-31") if flags["byteequal"] else DEFAULT_TRAIN_END
    )

    # 1. Load data (always)
    data = load_data(REGIONS)

    if flags["dry_run"] and not (
        flags["estimate"] or flags["train"]
        or flags["infer_hidden"] or flags["infer_replay"]
    ):
        print("[main] --dry-run only: data loaded successfully. Exiting.")
        return 0

    # 2. Build level targets (needed for train + replay infer)
    need_level_targets = (
        flags["estimate"] or flags["train"] or flags["infer_replay"]
    )
    level_targets = {}
    if need_level_targets:
        for region in REGIONS:
            level_targets[region] = build_level_targets(region, data)

    # 3. Feature selection
    sel_per_level_all = {}
    for region in REGIONS:
        sel_per_level_all[region] = compute_or_load_selection(
            region, data, level_targets, train_end, byteequal=flags["byteequal"],
        )

    feature_cols_all = {region: data[region][1] for region in REGIONS}

    # 4. Build splits
    splits_all = {
        region: build_splits(region, data, byteequal=flags["byteequal"])
        for region in REGIONS
    }

    # 5. Estimate
    if flags["estimate"]:
        for region in REGIONS:
            estimate_single_cb(
                region, data, level_targets, splits_all[region],
                sel_per_level_all[region],
            )
        if not (flags["train"] or flags["infer_hidden"] or flags["infer_replay"]):
            return 0

    # 6. Train
    speed_models_all = {}
    dir_models_all = {}
    if flags["train"] or flags["infer_hidden"] or flags["infer_replay"]:
        for region in REGIONS:
            speed_models_all[region] = train_speed_models(
                region, data, level_targets, splits_all[region],
                sel_per_level_all[region],
            )
            dir_models_all[region] = train_dir_models(region, data, splits_all[region])

    # 7. Hidden inference
    if flags["infer_hidden"]:
        vertical_ratios = {
            region: load_vertical_ratios(FEATURES_DIR, region) for region in REGIONS
        }
        sub = infer_hidden(
            speed_models_all, dir_models_all, sel_per_level_all,
            feature_cols_all, vertical_ratios,
        )
        out_path = (
            OUTPUT_HIDDEN_CSV_BYTEEQUAL if flags["byteequal"] else OUTPUT_HIDDEN_CSV_REPLAY
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sub.to_csv(out_path, index=False)
        print(f"[main] hidden CSV written: {out_path} ({len(sub):,} rows)")

    # 8. Replay inference (filtered to horizon=d7 to match parquet filename)
    if flags["infer_replay"]:
        replay = infer_replay(
            speed_models_all, sel_per_level_all, data, feature_cols_all,
        )
        replay_d7 = replay[replay["horizon"] == REPLAY_HORIZON_FILTER].reset_index(drop=True)
        REPLAY_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        replay_d7.to_parquet(REPLAY_PARQUET, index=False)
        print(f"[main] replay parquet written: {REPLAY_PARQUET} "
              f"({len(replay_d7):,} d7 rows; sliced from {len(replay):,} total)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
