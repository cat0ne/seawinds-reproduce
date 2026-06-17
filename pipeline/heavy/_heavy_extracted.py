#!/usr/bin/env python
# coding: utf-8

# # Phase 1 -- Heavy Starting Kit (Per-Level Models)
# 
# This notebook train separate wind speed models for each of the 7 vertical levels .
# 
# **Prerequisites**: Run `1_feature_engineering.ipynb` first.
# 
# **Runtime**: ~???.

# ## 1. Setup

# In[ ]:


import os, sys
# Ensure we're in the notebook's directory (participant_kit/phase1/)
_this_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else None
if _this_dir is None:
    for _candidate in [os.getcwd(), os.path.join(os.getcwd(), "participant_kit", "phase1")]:
        if os.path.exists(os.path.join(_candidate, "utils.py")):
            os.chdir(_candidate)
            break
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import warnings
import time as _time
import json

import numpy as np
import pandas as pd
import lightgbm as lgb
from pathlib import Path
from catboost import CatBoostRegressor

from utils import (
    REGIONS, HORIZONS, HOURS, QUANTILES_DEFAULT, PRESSURE_LEVELS,
    load_train_data, load_vertical_ratios, load_inference_features,
    exclude_worldwide_features, load_or_compute_selection,
    winkler_score, circular_mae,
    predict_direction, merge_speed_direction,
    attach_station_predictions,
)

warnings.filterwarnings("ignore")

DATA_DIR = Path("phase1_dataset")
FEATURES_DIR = DATA_DIR / "features"
TRAIN_DIR = DATA_DIR / "train"
INFERENCE_DIR = DATA_DIR / "inference"
SCORING_DIR = DATA_DIR / "scoring"
RECOMPUTE_SELECTION = False  # Set True to recompute feature importance (~2 min)

ALL_LEVELS = ["10m", "100m", "1000", "925", "850", "700", "500"]

assert FEATURES_DIR.exists(), (
    f"Features directory not found: {FEATURES_DIR}\n"
    "Run 1_feature_engineering.ipynb first."
)
assert TRAIN_DIR.exists(), f"Train directory not found: {TRAIN_DIR}"
print("Setup OK")


# ## 2. Load Training Features
# 
# Load pre-computed training features for both regions.

# In[ ]:


# Load training data for both regions
data = {}  # {region: (df, feature_cols, speed_targets, dir_targets)}

for region in REGIONS:
    df, feature_cols, speed_targets, dir_targets = load_train_data(FEATURES_DIR, region)
    data[region] = (df, feature_cols, speed_targets, dir_targets)
    print(f"\n{region}:")
    print(f"  Shape: {df.shape}")
    print(f"  Time range: {df['time'].min().date()} to {df['time'].max().date()}")
    print(f"  Features: {len(feature_cols)}, Speed targets: {len(speed_targets)}, Dir targets: {len(dir_targets)}")
    print(f"  Grid points: {df.groupby(['latitude', 'longitude']).ngroups}")


# ## 3. Build Level-Specific Targets
# 
# The training features already contain 10m speed targets (`speed_d{h}_h{hr}`). For other levels
# we need to compute targets from raw reanalysis data:
# 
# - **100m**: `ws100 = sqrt(u100^2 + v100^2)` from the 6-hourly surface data
# - **Pressure levels (1000-500 hPa)**: `ws_{lev} = sqrt(u_{lev}^2 + v_{lev}^2)` from reanalysis pressure data
# 
# For each training row at context date D and grid point (lat, lon), the target at horizon h and
# hour hr is the wind speed at that level at time `D + h days + hr hours`.
# 
# We compute a lookup table of wind speeds at each level and future timestamp, then merge onto
# the training features by (time + offset, lat, lon).
# 

# In[ ]:


def build_level_targets(region):
    """Build wind speed targets at all non-10m levels for one region.

    Returns a dict: {level_str: DataFrame} where each DataFrame has columns
    [time, latitude, longitude, speed_d1_h0, speed_d1_h6, ..., speed_d14_h18]
    aligned with the training features (one row per day at hour 0, per grid point).
    """
    print(f"Building level targets for {region}...")
    t0 = _time.time()

    # ── Wind speed lookup tables at each level ──────────────────────────
    # Surface 6h data has u100/v100 for the 100m level
    surface_cols = ["time", "latitude", "longitude", "u100", "v100"]
    reanalysis_surf = pd.read_parquet(TRAIN_DIR / f"reanalysis_{region}_6h.parquet",
                                columns=surface_cols)
    reanalysis_surf["time"] = pd.to_datetime(reanalysis_surf["time"])
    reanalysis_surf["ws_100m"] = np.sqrt(reanalysis_surf["u100"]**2 + reanalysis_surf["v100"]**2)
    reanalysis_surf.drop(columns=["u100", "v100"], inplace=True)
    print(f"  Loaded surface 6h: {len(reanalysis_surf):,} rows")

    # Pressure data has u/v at 1000/925/850/700/500 hPa
    reanalysis_pres = pd.read_parquet(TRAIN_DIR / f"reanalysis_pressure_{region}.parquet")
    reanalysis_pres["time"] = pd.to_datetime(reanalysis_pres["time"])
    for lev in PRESSURE_LEVELS:
        reanalysis_pres[f"ws_{lev}"] = np.sqrt(
            reanalysis_pres[f"u_{lev}"]**2 + reanalysis_pres[f"v_{lev}"]**2
        )
    # Keep only time, lat, lon, and ws columns
    ws_cols = ["time", "latitude", "longitude"] + [f"ws_{lev}" for lev in PRESSURE_LEVELS]
    reanalysis_pres = reanalysis_pres[ws_cols]
    print(f"  Loaded pressure: {len(reanalysis_pres):,} rows")

    # ── Merge lookup tables ─────────────────────────────────────────────
    # Combine 100m wind speed with pressure-level wind speeds
    ws_all = reanalysis_surf.merge(reanalysis_pres, on=["time", "latitude", "longitude"], how="inner")
    print(f"  Combined lookup: {len(ws_all):,} rows, "
          f"time range {ws_all['time'].min()} to {ws_all['time'].max()}")

    # ── Build targets by looking up future timestamps ───────────────────
    # Training features have time at hour 0 (daily). For each (time, lat, lon),
    # the target speed_d{h}_h{hr} at level L = ws_L at (time + h days + hr hours).
    df_feat = data[region][0]
    context_dates = df_feat[["time", "latitude", "longitude"]].copy()
    context_dates["latitude"] = context_dates["latitude"].round(2)
    context_dates["longitude"] = context_dates["longitude"].round(2)

    # Round lookup coords to match
    ws_all["latitude"] = ws_all["latitude"].round(2)
    ws_all["longitude"] = ws_all["longitude"].round(2)

    # Index the lookup for fast access
    ws_all = ws_all.set_index(["time", "latitude", "longitude"]).sort_index()

    level_targets = {}  # {level_str: DataFrame with target columns}

    for level_str in ["100m"] + [str(lev) for lev in PRESSURE_LEVELS]:
        ws_col = f"ws_{level_str}" if level_str != "100m" else "ws_100m"
        target_rows = []

        for h in HORIZONS:
            for hr in HOURS:
                tgt_name = f"speed_d{h}_h{hr}"
                offset = pd.Timedelta(days=h, hours=hr)
                # Compute future timestamps for all context dates
                future_times = context_dates["time"] + offset
                # Build lookup keys
                keys = pd.DataFrame({
                    "time": future_times,
                    "latitude": context_dates["latitude"].values,
                    "longitude": context_dates["longitude"].values,
                })
                # Look up wind speed at future time
                keys_idx = pd.MultiIndex.from_frame(keys)
                # Use reindex to align
                ws_vals = ws_all[ws_col].reindex(keys_idx).values
                target_rows.append((tgt_name, ws_vals))

        # Assemble into a DataFrame
        tgt_df = context_dates[["time", "latitude", "longitude"]].copy()
        for tgt_name, vals in target_rows:
            tgt_df[tgt_name] = vals

        n_valid = tgt_df.iloc[:, 3:].notna().sum().sum()
        n_total = tgt_df.iloc[:, 3:].size
        print(f"  {level_str}: {n_valid:,}/{n_total:,} valid targets "
              f"({100*n_valid/n_total:.1f}%)")
        level_targets[level_str] = tgt_df

    elapsed = _time.time() - t0
    print(f"  Done in {elapsed:.0f}s")
    return level_targets


# In[ ]:


# Build level-specific targets for both regions
# This reads the raw reanalysis 6h surface + pressure data (~2 GB per region)
level_targets = {}  # {region: {level_str: DataFrame}}
for region in REGIONS:
    level_targets[region] = build_level_targets(region)


# ## 4. Feature Selection
# 
# Select important features **per level** using LightGBM importance on each level-specific
# target. Since the drivers of 500 hPa wind differ from 10 m wind (boundary-layer vs. upper-
# air flow), computing a distinct feature set per level is worth the extra cost on a heavy
# kit. The result is cached to a single JSON file per region.
# 

# In[ ]:


from utils import compute_feature_selection

ALL_LEVELS = ["10m", "100m"] + [str(lev) for lev in PRESSURE_LEVELS]

selected_features = {}  # {region: {level: {target: [feature_names]}}}

TOP_K_HEAVY = {1: 15, 7: 20, 14: 25}

for region in REGIONS:
    df, feature_cols, speed_targets, _ = data[region]
    feature_cols_speed = exclude_worldwide_features(feature_cols)

    cache_path = FEATURES_DIR / f"selected_features_heavy_per_level_{region}.json"
    if cache_path.exists() and not RECOMPUTE_SELECTION:
        print(f"Loading cached per-level feature selection: {cache_path.name}")
        selected_features[region] = json.loads(cache_path.read_text())
        continue

    print(f"\n{'='*60}\nComputing per-level feature selection: {region}\n{'='*60}")
    selected_features[region] = {}

    for level_str in ALL_LEVELS:
        # Assemble a df holding features + the level's targets as columns
        if level_str == "10m":
            df_for_sel = df  # 10m targets already in df
        else:
            lev_tgt = level_targets[region][level_str]
            # df has the features, lev_tgt has the level-specific targets
            tgt_cols = [c for c in lev_tgt.columns if c.startswith("speed_d")]
            df_for_sel = df[[c for c in df.columns if c not in tgt_cols]].copy()
            df_for_sel = df_for_sel.join(lev_tgt[tgt_cols], how="left")

        sel_level = compute_feature_selection(
            df_for_sel, feature_cols_speed, speed_targets,
            model_type="lgbm", top_k=TOP_K_HEAVY,
        )
        selected_features[region][level_str] = sel_level
        print(f"  {level_str}: selected features for {len(sel_level)} targets "
              f"(top-k d1/d7/d14={TOP_K_HEAVY[1]}/{TOP_K_HEAVY[7]}/{TOP_K_HEAVY[14]})")

    cache_path.write_text(json.dumps(selected_features[region], indent=2))
    print(f"  Saved: {cache_path.name}")

# Show a sample: which pressure-level features got picked for 500 hPa d7_h0
r = REGIONS[0]
feats_500 = selected_features[r]["500"]["speed_d7_h0"]
feats_10m = selected_features[r]["10m"]["speed_d7_h0"]
print(f"\nExample ({r} / speed_d7_h0):")
print(f"  10m  ({len(feats_10m)} feats): {feats_10m[:6]}...")
print(f"  500  ({len(feats_500)} feats): {feats_500[:6]}...")
overlap = set(feats_10m) & set(feats_500)
print(f"  overlap between 10m and 500: {len(overlap)}/{len(feats_10m)}")


# ## 5. Train/Val Split
# 
# - **Train**: 2019--2020 (2 years)
# - **Validation**: full 2021 (held out for early stopping and evaluation)
# - **Subsample**: 500K rows max per region to keep training fast
# - **Speed models**: exclude worldwide features
# - **Direction models**: keep all features
# 

# In[ ]:


MAX_TRAIN_SAMPLES = 500_000

splits = {}  # {region: (df_train, df_val, feature_cols_speed, feature_cols_dir, train_idx, val_idx)}

for region in REGIONS:
    df, feature_cols, speed_targets, dir_targets = data[region]

    # Train: 2019-2020, Val: full 2021
    train_mask = df["time"].dt.year.isin([2019, 2020])
    val_mask = df["time"].dt.year == 2021

    train_idx = df.index[train_mask]
    val_idx = df.index[val_mask]

    # Subsample training data (keep index for level target alignment)
    if len(train_idx) > MAX_TRAIN_SAMPLES:
        rng = np.random.RandomState(42)
        train_idx = rng.choice(train_idx, size=MAX_TRAIN_SAMPLES, replace=False)
        train_idx = np.sort(train_idx)

    df_train = df.loc[train_idx]
    df_val = df.loc[val_idx]

    # Speed models: exclude worldwide features
    feature_cols_speed = exclude_worldwide_features(feature_cols)
    # Direction models: keep all features
    feature_cols_dir = feature_cols

    splits[region] = (df_train, df_val, feature_cols_speed, feature_cols_dir, train_idx, val_idx)
    print(f"{region}: train={len(df_train):,}, val={len(df_val):,}, "
          f"speed_feats={len(feature_cols_speed)}, dir_feats={len(feature_cols_dir)}")


# ## 6. Train Per-Level Speed Models -- CatBoost Quantile Regression
# 
# For each of the 7 vertical levels, train CatBoost quantile models for all 12 speed targets
# and 3 quantiles (q05, q50, q95). 
# 
# Total: 7 levels x 12 targets x 3 quantiles x 2 regions = **504 speed models**.

# In[ ]:


QUANTILES = QUANTILES_DEFAULT  # [0.05, 0.5, 0.95]

# {region: {level: {target: {quantile: model}}}}
speed_models_all_levels = {}

t0_global = _time.time()

for region in REGIONS:
    df_train, df_val, feature_cols_speed, _, train_idx, val_idx = splits[region]
    _, _, speed_targets, _ = data[region]
    sel_per_level = selected_features[region]

    speed_models_all_levels[region] = {}

    for level_str in ALL_LEVELS:
        print(f"\n{'='*60}")
        print(f"{region} / {level_str}: Training {len(speed_targets)} targets x {len(QUANTILES)} quantiles")
        print(f"{'='*60}")

        sel = sel_per_level[level_str]

        # Get target values for this level
        if level_str == "10m":
            # 10m targets are already in the training features
            y_source_train = df_train
            y_source_val = df_val
        else:
            # Use level-specific targets, aligned by index
            lev_tgt = level_targets[region][level_str]
            y_source_train = lev_tgt.loc[train_idx]
            y_source_val = lev_tgt.loc[val_idx]

        level_models = {}
        for tgt in speed_targets:
            feats = sel.get(tgt, feature_cols_speed)

            # Prepare data, drop rows where target is NaN
            y_tr = y_source_train[tgt]
            y_vl = y_source_val[tgt]
            mask_tr = y_tr.notna()
            mask_vl = y_vl.notna()

            if mask_tr.sum() < 100:
                print(f"  {tgt}: skipped (only {mask_tr.sum()} valid rows)")
                continue

            X_tr = df_train.loc[mask_tr.values, feats].fillna(0)
            y_tr = y_tr[mask_tr]
            X_vl = df_val.loc[mask_vl.values, feats].fillna(0)
            y_vl = y_vl[mask_vl]

            models_q = {}
            for q in QUANTILES:
                m = CatBoostRegressor(
                    loss_function=f"Quantile:alpha={q}",
                    iterations=500, depth=7, learning_rate=0.05,
                    l2_leaf_reg=3, random_seed=42, verbose=0,
                )
                m.fit(X_tr, y_tr, eval_set=(X_vl, y_vl), early_stopping_rounds=50)
                models_q[q] = m
            level_models[tgt] = models_q

            # Quick validation metrics
            q05 = np.maximum(models_q[0.05].predict(X_vl), 0)
            q50 = models_q[0.5].predict(X_vl)
            q95 = models_q[0.95].predict(X_vl)
            rmse = float(np.sqrt(np.nanmean((y_vl.values - q50) ** 2)))
            ws = winkler_score(y_vl.values, q05, q95, alpha=0.1)
            print(f"  {tgt}: RMSE={rmse:.3f}, WS={ws:.3f}")

        speed_models_all_levels[region][level_str] = level_models

elapsed = _time.time() - t0_global
print(f"\nAll speed models trained in {elapsed:.0f}s "
      f"({sum(len(m) for r in speed_models_all_levels.values() for m in r.values())} target-level combos)")


# ## 7. Direction Models -- LightGBM sin/cos (10m only)
# 
# Wind direction is trained at 10m only. For other levels, we apply the same 10m direction
# prediction with optional climatological offsets from the vertical ratio data (wind direction
# veers with height due to the Ekman spiral).

# In[ ]:


import lightgbm as lgb

dir_models = {}
t0 = _time.time() if '_time' in dir() else __import__('time').time()

for region in REGIONS:
    _, feature_cols, _, dir_targets_list = data[region]
    df_train = splits[region][0]

    dir_models[region] = {}
    for tgt in dir_targets_list:
        mask_tr = df_train[tgt].notna()
        if mask_tr.sum() < 100:
            continue

        # Feature selection for direction (top-25)
        X_sub = df_train.loc[mask_tr, feature_cols].fillna(0).sample(
            n=min(100_000, mask_tr.sum()), random_state=42)
        y_sub = df_train.loc[X_sub.index, tgt]
        m_imp = lgb.LGBMRegressor(n_estimators=50, max_depth=4, verbose=-1, n_jobs=-1)
        m_imp.fit(X_sub, np.sin(np.radians(y_sub)))
        dir_feats = pd.Series(m_imp.feature_importances_, index=feature_cols).nlargest(25).index.tolist()

        X_tr = df_train.loc[mask_tr, dir_feats].fillna(0)
        y_tr_sin = np.sin(np.radians(df_train.loc[mask_tr, tgt]))
        y_tr_cos = np.cos(np.radians(df_train.loc[mask_tr, tgt]))

        params = dict(n_estimators=200, max_depth=7, learning_rate=0.05,
                      subsample=0.8, verbose=-1, n_jobs=-1)
        m_sin = lgb.LGBMRegressor(**params)
        m_cos = lgb.LGBMRegressor(**params)
        m_sin.fit(X_tr, y_tr_sin)
        m_cos.fit(X_tr, y_tr_cos)
        dir_models[region][tgt] = (m_sin, m_cos, dir_feats)
        print(f"  {tgt}: trained")

import time as _time_mod
print(f"Direction training complete")


# ## 8. Validation Summary
# 
# Aggregate validation metrics by region, level, and horizon. Compare per-level model performance
# against what the light kit achieves (10m-only with ratio scaling).

# In[ ]:


print(f"{'Region':<18} {'Level':<8} {'Horizon':<9} {'Mean WS':>8} {'Mean RMSE':>10}")
print("-" * 56)

val_metrics = []  # collect for later comparison

for region in REGIONS:
    df_val = splits[region][1]
    _, _, speed_targets, _ = data[region]
    sel_per_level = selected_features[region]
    _, _, _, _, _, val_idx = splits[region]

    for level_str in ALL_LEVELS:
        level_models = speed_models_all_levels[region].get(level_str, {})
        if not level_models:
            continue

        sel = sel_per_level[level_str]

        # Get validation targets for this level
        if level_str == "10m":
            y_source_val = df_val
        else:
            y_source_val = level_targets[region][level_str].loc[val_idx]

        for h in HORIZONS:
            ws_list, rmse_list = [], []
            for tgt in speed_targets:
                if int(tgt.split("_")[1][1:]) != h:
                    continue
                if tgt not in level_models:
                    continue

                feats = sel.get(tgt, [])
                y_vl = y_source_val[tgt]
                mask_vl = y_vl.notna()
                if mask_vl.sum() == 0:
                    continue

                X_vl = df_val.loc[mask_vl.values, feats].fillna(0)
                y_vl = y_vl[mask_vl].values

                mq = level_models[tgt]
                q05 = np.maximum(mq[0.05].predict(X_vl), 0)
                q50 = mq[0.5].predict(X_vl)
                q95 = mq[0.95].predict(X_vl)
                ws_list.append(winkler_score(y_vl, q05, q95, alpha=0.1))
                rmse_list.append(float(np.sqrt(np.nanmean((y_vl - q50) ** 2))))

            if ws_list:
                mean_ws = np.mean(ws_list)
                mean_rmse = np.mean(rmse_list)
                print(f"{region:<18} {level_str:<8} +{h:<7d} {mean_ws:>8.3f} {mean_rmse:>10.3f}")
                val_metrics.append({
                    "region": region, "level": level_str, "horizon": h,
                    "mean_ws": mean_ws, "mean_rmse": mean_rmse,
                })

val_metrics_df = pd.DataFrame(val_metrics)
print(f"\nTotal metric entries: {len(val_metrics_df)}")


# ## 9. Generate Submission
# 
# For each inference window, predict wind speed at each level independently using the per-level
# models. Direction is predicted at 10m and applied to all levels (with climatological offsets
# from vertical ratios where available).

# In[ ]:


def predict_speed_at_level(features_df, level_models, selected_feats, feature_cols):
    """Generate speed predictions at one level for all targets.

    Returns DataFrame with columns: latitude, longitude, horizon, hour, q05, q50, q95.
    """
    rows = []
    for tgt, models_q in level_models.items():
        horizon = int(tgt.split("_")[1][1:])
        hour = int(tgt.split("_")[2][1:])
        feats = selected_feats.get(tgt, feature_cols)
        # Ensure all features exist
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


def generate_heavy_submission(speed_models_all, dir_models, selected_features,
                              feature_cols_all, vertical_ratios,
                              features_dir, n_windows=8):
    """Generate a complete submission with per-level speed predictions.

    Instead of predicting at 10m and scaling, predicts independently at each level.
    Direction is from 10m models, applied to all levels with climatological offsets.
    """
    all_preds = []

    for wid in range(1, n_windows + 1):
        for region in REGIONS:
            df_inf = load_inference_features(features_dir, wid, region)
            context_month = int(df_inf["time"].max().month)
            fcols = feature_cols_all[region]
            sel_per_level = selected_features[region]
            ratios_df = vertical_ratios.get(region)

            # Direction at 10m (shared across levels)
            dir_preds = predict_direction(df_inf, dir_models[region], fcols)

            for level_str in ALL_LEVELS:
                level_models = speed_models_all[region].get(level_str, {})
                if not level_models:
                    continue

                # Predict speed at this level
                sel = sel_per_level[level_str]
                preds = predict_speed_at_level(df_inf, level_models, sel, fcols)

                stacked = np.sort(preds[["q05", "q50", "q95"]].values, axis=1)
                preds["q05"] = stacked[:, 0]
                preds["q50"] = stacked[:, 1]
                preds["q95"] = stacked[:, 2]

                # Apply direction
                preds = merge_speed_direction(preds, dir_preds)

                # For non-10m levels, apply climatological direction offset if available
                if level_str != "10m" and ratios_df is not None:
                    lev_key = level_str
                    if lev_key in ratios_df["level"].values:
                        r_dir = ratios_df[
                            (ratios_df["level"] == lev_key) &
                            (ratios_df["month"] == context_month)
                        ]
                        if "dir_clim" in r_dir.columns and len(r_dir) > 0:
                            r_dir = r_dir[["latitude", "longitude", "dir_clim"]].copy()
                            r_dir["latitude"] = r_dir["latitude"].astype(float).round(2)
                            r_dir["longitude"] = r_dir["longitude"].astype(float).round(2)
                            preds = preds.merge(r_dir, on=["latitude", "longitude"], how="left")
                            has_clim = preds["dir_clim"].notna()
                            preds.loc[has_clim, "dir_50"] = preds.loc[has_clim, "dir_clim"].round(1)
                            preds.drop(columns=["dir_clim"], inplace=True, errors="ignore")

                preds["level"] = level_str
                preds["window"] = wid
                preds["region"] = region
                all_preds.append(preds)

            n_rows = sum(len(p) for p in all_preds if p["window"].iloc[0] == wid and p["region"].iloc[0] == region)
            n_levels = sum(1 for p in all_preds if p["window"].iloc[0] == wid and p["region"].iloc[0] == region)
            print(f"  W{wid} {region}: {n_rows:,} rows ({n_levels} levels)")

    sub = pd.concat(all_preds, ignore_index=True)
    sub = sub[["window", "region", "latitude", "longitude", "horizon", "hour",
               "level", "q05", "q50", "q95", "dir_50"]]

    # Enforce constraints
    sub["q05"] = sub["q05"].clip(lower=0)
    sub["q95"] = sub[["q50", "q95"]].max(axis=1)
    sub["q05"] = sub[["q05", "q50"]].min(axis=1)
    sub["dir_50"] = sub["dir_50"] % 360

    return sub


# In[ ]:


# Prepare inputs
feature_cols_all = {}
vertical_ratios = {}

for region in REGIONS:
    _, feature_cols, _, _ = data[region]
    feature_cols_all[region] = feature_cols
    vertical_ratios[region] = load_vertical_ratios(FEATURES_DIR, region)

print("Generating submission with per-level models...")
t0 = _time.time()
sub = generate_heavy_submission(
    speed_models_all=speed_models_all_levels,
    dir_models=dir_models,
    selected_features=selected_features,
    feature_cols_all=feature_cols_all,
    vertical_ratios=vertical_ratios,
    features_dir=FEATURES_DIR,
    n_windows=8,
)
elapsed = _time.time() - t0
print(f"\nSubmission generated in {elapsed:.0f}s")


# In[ ]:


# Compute direction intervals
from utils import compute_direction_intervals
dir_offsets = {}
try:
    for region in REGIONS:
        df_tr_dir, fcols_dir, _, dir_tgts = load_train_data(FEATURES_DIR, region)
        df_tr_dir = df_tr_dir[df_tr_dir["time"].dt.year.isin([2019, 2020])]
        dir_offsets[region] = compute_direction_intervals(
            df_tr_dir, dir_tgts, fcols_dir, dir_models[region], quantile_hi=0.975)
        print(f"  {region}: " + ", ".join(f"+{h}d: +/-{v:.1f} deg" for h, v in dir_offsets[region].items()))
        del df_tr_dir
except Exception as e:
    print(f"Dir interval computation failed: {e}")


# In[ ]:


# Add direction intervals to submission — REQUIRED by the scorer
# (circular Winkler on the 90% PI). Any rows left without calibrated offsets
# get a conservative ±90° fallback arc so the submission still validates.
import numpy as np
from utils import add_direction_intervals
if "dir_05" not in sub.columns:
    sub["dir_05"] = np.nan
if "dir_95" not in sub.columns:
    sub["dir_95"] = np.nan
for region in REGIONS:
    mask = sub["region"] == region
    if region in dir_offsets and dir_offsets[region]:
        region_sub = sub[mask].copy()
        region_sub = add_direction_intervals(region_sub, dir_offsets[region])
        sub.loc[mask, "dir_05"] = region_sub["dir_05"].values
        sub.loc[mask, "dir_95"] = region_sub["dir_95"].values
    else:
        # Fallback: ±90° arc around dir_50
        sub.loc[mask, "dir_05"] = (sub.loc[mask, "dir_50"] - 90.0) % 360
        sub.loc[mask, "dir_95"] = (sub.loc[mask, "dir_50"] + 90.0) % 360
# Last-resort fill for any stragglers
missing = sub["dir_05"].isna() | sub["dir_95"].isna()
if missing.any():
    sub.loc[missing, "dir_05"] = (sub.loc[missing, "dir_50"] - 90.0) % 360
    sub.loc[missing, "dir_95"] = (sub.loc[missing, "dir_50"] + 90.0) % 360
print(f"Direction intervals set on all {len(sub):,} rows. "
      f"Columns: {sub.columns.tolist()}")


# In[ ]:


# Attach station predictions (baseline: inherit from nearest grid point)
sub = attach_station_predictions(sub, FEATURES_DIR)

# Save submission
out_path = Path("predictions_heavy.csv")
sub.to_csv(out_path, index=False)
print(f"Saved: {out_path} ({len(sub):,} rows)")

# --- Package for Codabench upload ---
# Codabench expects a ZIP.
import zipfile
submission_zip = Path("submission_heavy.zip")
with zipfile.ZipFile(submission_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(out_path, arcname="predictions.csv")
print(f"Ready to upload to Codabench: {submission_zip}")

# Breakdown
print(f"\nRows per region:")
for region in REGIONS:
    n = len(sub[sub["region"] == region])
    print(f"  {region}: {n:,}")

print(f"\nRows per level:")
for level in ALL_LEVELS:
    n = len(sub[sub["level"] == level])
    print(f"  {level}: {n:,}")

print(f"\nWindows: {sub['window'].nunique()}, "
      f"Horizons: {sorted(sub['horizon'].unique())}, "
      f"Hours: {sorted(sub['hour'].unique())}")

print(f"\nSample rows:")
sub.head(5)

