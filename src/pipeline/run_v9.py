"""V9: CQR calibration on v8 speed intervals + hybrid direction + height correction.

Optimized: pre-computes HRES speed during data construction, samples to 200k rows.

Usage: python src/pipeline/run_v9.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd

from src.data.paths import (
    ALPHA,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SURFACE_LEVELS,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    align_columns,
    apply_height_correction,
    direction_df_from_dict,
    fix_crossing,
    generate_hybrid_direction,
    get_base_feature_cols,
    load_baseline,
    load_reanalysis_level,
    merge_direction_onto_grid,
    save_submission,
    split_by_time,
    speed_from_uv,
)
from src.pipeline.run_v8 import build_speed_features, compute_hres_speed

SPEED_MODEL_DIR = LOGS_DIR / "speed_models_v8"
CQR_DIR = LOGS_DIR / "cqr_v9"


def _build_cqr_data(region, level, horizon, features, feat_cols_base, rean):
    val_frames = []
    for hour in HOURS:
        sub = features[["time", "latitude", "longitude"] + feat_cols_base].copy()
        sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
        sub["hour"] = hour
        sub["horizon"] = horizon

        merged = sub.merge(
            rean.rename(columns={"time": "target_time", "speed": "target_speed"}),
            on=["target_time", "latitude", "longitude"],
            how="inner",
        ).dropna(subset=["target_speed"])
        if len(merged) == 0:
            continue

        # compute_hres_speed needs the HRES columns from the original features
        # For surface: needs speed_d{h}_h{hr} (not in feat_cols_base)
        # For pressure: needs fcst_u/v_{level}_d{h}_h{hr} (in feat_cols_base)
        if level in ("10m", "100m"):
            hres_col = f"speed_d{horizon}_h{hour}"
            # Re-merge to get the HRES speed column
            lat_lon_time = merged[["latitude", "longitude", "time"]].copy()
            hres_lookup = features[["time", "latitude", "longitude", hres_col]].copy()
            hres_lookup["latitude"] = hres_lookup["latitude"].astype(float).round(2)
            hres_lookup["longitude"] = hres_lookup["longitude"].astype(float).round(2)
            lat_lon_time["latitude"] = lat_lon_time["latitude"].astype(float).round(2)
            lat_lon_time["longitude"] = lat_lon_time["longitude"].astype(float).round(2)
            with_hres = lat_lon_time.merge(hres_lookup, on=["time", "latitude", "longitude"], how="left")
            hres_spd = with_hres[hres_col].values
            if np.any(np.isnan(hres_spd)):
                continue
        else:
            u_col = f"fcst_u_{level}_d{horizon}_h{hour}"
            v_col = f"fcst_v_{level}_d{horizon}_h{hour}"
            if u_col not in merged.columns or v_col not in merged.columns:
                continue
            hres_spd = speed_from_uv(merged[u_col].values, merged[v_col].values)

        merged["residual"] = merged["target_speed"].values - hres_spd
        merged["hres_speed"] = hres_spd
        val_frames.append(merged)

    if not val_frames:
        return None
    return pd.concat(val_frames, ignore_index=True)


def train_cqr_calibration():
    print("=" * 60)
    print("V9: Computing CQR calibration offsets")
    print("=" * 60)
    t0 = time.time()
    CQR_DIR.mkdir(parents=True, exist_ok=True)

    offsets = {}
    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        feat_cols_base = get_base_feature_cols(features.columns)

        if len(features) > 200_000:
            features = features.sample(n=200_000, random_state=42).reset_index(drop=True)

        for level in ALL_LEVELS:
            rean = load_reanalysis_level(region, level)
            t_level = time.time()

            for horizon in HORIZONS:
                model_path = SPEED_MODEL_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                model_feat_cols = art["feature_cols"]

                df = _build_cqr_data(region, level, horizon, features, feat_cols_base, rean)
                if df is None or len(df) < 50:
                    offsets[(region, level, horizon)] = 0.0
                    continue

                if len(df) > 15_000:
                    df = df.sample(n=15_000, random_state=42)

                tr, vl, tu, ho = split_by_time(df)
                val_data = vl if len(vl) > 50 else tu
                if len(val_data) < 30:
                    offsets[(region, level, horizon)] = 0.0
                    continue

                X_val = build_speed_features(val_data, feat_cols_base, horizon, 0, level)
                X_val = align_columns(X_val, model_feat_cols)

                pred_05 = models[0.05].predict(X_val)
                pred_95 = models[0.95].predict(X_val)
                actual = val_data["target_speed"].values
                hres_val = val_data["hres_speed"].values

                q05f = np.maximum(hres_val + pred_05, 0)
                q95f = hres_val + pred_95
                E = np.maximum(q05f - actual, actual - q95f)

                n = len(E)
                q_idx = min(int(np.ceil((1 - ALPHA) * (n + 1))) - 1, n - 1)
                offset = float(np.sort(E)[q_idx])

                offsets[(region, level, horizon)] = offset
                print(f"  {level}/d{horizon}: offset={offset:.2f} ({len(val_data):,} val)", flush=True)

            elapsed = time.time() - t_level
            print(f"  {level}: done in {elapsed:.0f}s")

    with open(CQR_DIR / "offsets.pkl", "wb") as f:
        pickle.dump(offsets, f)

    print(f"\nCQR offsets computed in {time.time()-t0:.0f}s")
    print(f"  Total offsets: {len(offsets)}, non-zero: {sum(1 for v in offsets.values() if v > 0)}")
    return offsets


def generate_v9():
    print("\n" + "=" * 60)
    print("Generating V9 submission (CQR-calibrated)")
    print("=" * 60)

    with open(CQR_DIR / "offsets.pkl", "rb") as f:
        offsets = pickle.load(f)

    all_rows = []
    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                model_path = SPEED_MODEL_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not model_path.exists():
                    continue

                with open(model_path, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                feat_cols = art["feature_cols"]
                offset = offsets.get((region, level, horizon), 0.0)

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue

                    for hour in HOURS:
                        X = build_speed_features(inf, feat_cols, horizon, hour, level)
                        hres_spd = compute_hres_speed(inf, level, horizon, hour)
                        if hres_spd is None:
                            continue

                        r05 = models[0.05].predict(X)
                        r50 = models[0.50].predict(X)
                        r95 = models[0.95].predict(X)

                        q05 = np.maximum(hres_spd + r05 - offset, 0)
                        q50 = hres_spd + r50
                        q95 = hres_spd + r95 + offset

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            all_rows.append({
                                "type": "grid", "window": wid, "region": region,
                                "latitude": float(lats[i]), "longitude": float(lons[i]),
                                "station": "", "horizon": int(horizon), "hour": int(hour),
                                "level": str(level),
                                "q05": q05[i], "q50": q50[i], "q95": q95[i],
                            })

    speed_df = pd.DataFrame(all_rows)
    print(f"  CQR speed rows: {len(speed_df):,}")

    baseline = load_baseline()
    bl_grid = baseline[baseline["type"] == "grid"].copy()
    for c in ["latitude", "longitude"]:
        bl_grid[c] = bl_grid[c].astype(float).round(2)
        speed_df[c] = speed_df[c].astype(float).round(2)
    bl_grid["horizon"] = bl_grid["horizon"].astype(int)
    bl_grid["hour"] = bl_grid["hour"].astype(int)
    speed_df["horizon"] = speed_df["horizon"].astype(int)
    speed_df["hour"] = speed_df["hour"].astype(int)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    bl_with_new = bl_grid.merge(
        speed_df[merge_keys + ["q05", "q50", "q95"]],
        on=merge_keys, how="left", suffixes=("_bl", "_new"),
    )
    for q in ["q05", "q50", "q95"]:
        nc, bc = f"{q}_new", f"{q}_bl"
        if nc in bl_with_new.columns:
            bl_with_new[q] = bl_with_new[nc].fillna(bl_with_new[bc])
            bl_with_new = bl_with_new.drop(columns=[nc, bc])

    print("  Generating hybrid direction (pooled d1/d7 + per-horizon d14)...")
    all_dir = generate_hybrid_direction()
    dir_df = direction_df_from_dict(all_dir)
    grid = merge_direction_onto_grid(bl_with_new, dir_df)
    grid = fix_crossing(grid)

    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())
    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    save_submission(submission, "v9")


if __name__ == "__main__":
    train_cqr_calibration()
    generate_v9()
