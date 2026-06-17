"""V10: Enhanced physical + temporal features + residual speed + v7 direction + CQR.

New features added:
1. Physical: stability index (sst - t2m), forecast error proxy (ws10 - fcst_speed_d1)
2. Forecast spread: |fcst_speed_d1 - fcst_speed_d7|, |fcst_dir_d1 - fcst_dir_d7|
3. Temporal: wind acceleration (ws10 - ws10_lag1d), volatility (ws10_rstd3d/ws10_rmean3d)
4. Cross-level shear: computed from HRES pressure forecasts at different levels
5. Geospatial: dist_to_coast_km, lsm (land-sea mask)
6. Month cyclical encodings (in addition to week-of-year)

Retrains both speed (residual) and direction models with these features.
Then applies CQR calibration.

Requires: run_v7.py direction models (for reference, but retrained here).

Usage: python src/pipeline/run_v10.py
"""
from __future__ import annotations

import pickle
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.paths import (
    ALPHA,
    FEATURES_DIR,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    REGIONS,
    SURFACE_LEVELS,
)
from src.io.dataset import load_features, load_inference_features
from src.models.direction import DirectionModel
from src.pipeline.pipeline_utils import (
    ALL_LEVELS,
    add_time_encodings,
    align_columns,
    apply_height_correction,
    direction_df_from_dict,
    direction_from_uv,
    fix_crossing,
    generate_hybrid_direction,
    get_base_feature_cols,
    load_baseline,
    load_geospatial,
    load_geospatial_inference,
    load_reanalysis_level,
    save_submission,
    split_by_time,
    speed_from_uv,
)
from src.scoring.winkler import _circ_dist, circular_winkler_score

SAVE_DIR_SPEED = LOGS_DIR / "speed_models_v10"
SAVE_DIR_DIR = LOGS_DIR / "direction_models_v10"
CQR_DIR = LOGS_DIR / "cqr_v10"

LGBM_PARAMS = {
    "n_estimators": 800,
    "max_depth": 7,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 50,
    "verbose": -1,
    "n_jobs": -1,
}


def add_enhanced_features(df: pd.DataFrame, region: str = None, window_id: int = None) -> pd.DataFrame:
    df = df.copy()

    if "sst" in df.columns and "t2m" in df.columns:
        df["stability"] = df["sst"] - df["t2m"]

    if "ws10" in df.columns and "ws10_lag1d" in df.columns:
        df["ws10_accel"] = df["ws10"] - df["ws10_lag1d"]
    if "ws10_rstd3d" in df.columns and "ws10_rmean3d" in df.columns:
        df["ws10_cv"] = df["ws10_rstd3d"] / (df["ws10_rmean3d"] + 0.1)

    for h in [0, 6, 12, 18]:
        d1_col = f"speed_d1_h{h}"
        if "ws10" in df.columns and d1_col in df.columns:
            df[f"fcst_error_proxy_h{h}"] = df["ws10"] - df[d1_col]

    if "fcst_speed_d1_h0" in df.columns and "fcst_speed_d7_h0" in df.columns:
        df["fcst_spread_d1d7"] = np.abs(df["fcst_speed_d1_h0"] - df["fcst_speed_d7_h0"])
    if "fcst_speed_d1_h0" in df.columns and "fcst_speed_d14_h0" in df.columns:
        df["fcst_spread_d1d14"] = np.abs(df["fcst_speed_d1_h0"] - df["fcst_speed_d14_h0"])

    if "fcst_dir_d1_h0" in df.columns and "fcst_dir_d7_h0" in df.columns:
        diff = df["fcst_dir_d1_h0"] - df["fcst_dir_d7_h0"]
        df["fcst_dir_change_d1d7"] = np.minimum(np.abs(diff), 360 - np.abs(diff))
    if "fcst_dir_d1_h0" in df.columns and "fcst_dir_d14_h0" in df.columns:
        diff = df["fcst_dir_d1_h0"] - df["fcst_dir_d14_h0"]
        df["fcst_dir_change_d1d14"] = np.minimum(np.abs(diff), 360 - np.abs(diff))

    for lev_a, lev_b in [("850", "1000"), ("700", "850"), ("500", "700")]:
        for hr in [0, 6, 12, 18]:
            for d in [1, 7]:
                ua = f"fcst_u_{lev_a}_d{d}_h{hr}"
                va = f"fcst_v_{lev_a}_d{d}_h{hr}"
                ub = f"fcst_u_{lev_b}_d{d}_h{hr}"
                vb = f"fcst_v_{lev_b}_d{d}_h{hr}"
                if all(c in df.columns for c in [ua, va, ub, vb]):
                    sa = speed_from_uv(df[ua].values, df[va].values)
                    sb = speed_from_uv(df[ub].values, df[vb].values)
                    df[f"shear_{lev_a}_{lev_b}_d{d}_h{hr}"] = sa - sb

    if "msl" in df.columns and "msl_lag1d" in df.columns:
        df["msl_tendency"] = df["msl"] - df["msl_lag1d"]

    geo_df = None
    if window_id is not None and region is not None:
        geo_df = load_geospatial_inference(window_id, region)
    elif region is not None:
        geo_df = load_geospatial(region)

    if geo_df is not None and not geo_df.empty and "latitude" in geo_df.columns:
        geo_df["latitude"] = geo_df["latitude"].astype(float).round(2)
        geo_df["longitude"] = geo_df["longitude"].astype(float).round(2)
        geo_cols = [c for c in geo_df.columns if c not in ("latitude", "longitude")]
        if geo_cols:
            lat_key = "latitude" if "latitude" in df.columns else None
            lon_key = "longitude" if "longitude" in df.columns else None
            if lat_key and lon_key:
                df[lk] = df[lk].astype(float).round(2) if (lk := lat_key) else None
                df[lk] = df[lk].astype(float).round(2) if (lk := lon_key) else None
                df = df.merge(geo_df, on=["latitude", "longitude"], how="left", suffixes=("", "_geo"))
                for c in geo_cols:
                    if f"{c}_geo" in df.columns:
                        df[c] = df[c].fillna(df[f"{c}_geo"])
                        df = df.drop(columns=[f"{c}_geo"])

    return df


def get_feature_cols_enhanced(columns):
    base = get_base_feature_cols(columns)
    extra = [
        "stability", "ws10_accel", "ws10_cv",
        "fcst_spread_d1d7", "fcst_spread_d1d14",
        "fcst_dir_change_d1d7", "fcst_dir_change_d1d14",
        "msl_tendency",
        "dist_to_coast_km", "lsm",
    ]
    extra += [c for c in columns if c.startswith("fcst_error_proxy")]
    extra += [c for c in columns if c.startswith("shear_")]
    return sorted(set(base) | {c for c in extra if c in columns})


def train_direction_v10():
    print("=" * 60)
    print("V10: Training per-horizon direction models (enhanced features)")
    print("=" * 60)
    SAVE_DIR_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for region in REGIONS:
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features = add_enhanced_features(features, region=region)
        feat_cols = get_feature_cols_enhanced(features.columns)

        for level in ALL_LEVELS:
            rean = load_reanalysis_level(region, level)
            rean = rean.rename(columns={"time": "target_time", "direction": "target_direction"})

            for horizon in HORIZONS:
                label = f"{region}/{level}/d{horizon}"
                print(f"\n--- {label} ---")

                frames = []
                for hour in HOURS:
                    sub = features[["time", "latitude", "longitude"] + feat_cols].copy()
                    sub = sub.sample(n=min(100_000, len(sub)), random_state=42)
                    sub["target_time"] = sub["time"] + pd.Timedelta(days=horizon, hours=hour)
                    sub["latitude"] = sub["latitude"].astype(float).round(2)
                    sub["longitude"] = sub["longitude"].astype(float).round(2)
                    sub["hour"] = hour

                    merged = sub.merge(
                        rean[["target_time", "latitude", "longitude", "target_direction"]],
                        on=["target_time", "latitude", "longitude"],
                        how="inner",
                    ).dropna(subset=["target_direction"])
                    if len(merged) > 0:
                        frames.append(merged)

                if not frames:
                    continue
                df = pd.concat(frames, ignore_index=True)
                df["horizon"] = horizon
                tr, vl, tu, ho = split_by_time(df)
                if len(tr) < 300 or len(tu) < 50:
                    continue

                X_tr = add_time_encodings(tr[feat_cols + ["time", "hour"]].copy())
                for hr in HOURS:
                    X_tr[f"hour_{hr}"] = (tr["hour"] == hr).astype(int)
                X_tr = X_tr.drop(columns=["time", "hour"], errors="ignore")
                y_tr = tr["target_direction"].values

                X_vl = add_time_encodings(vl[feat_cols + ["time", "hour"]].copy()) if len(vl) > 0 else None
                if X_vl is not None:
                    for hr in HOURS:
                        X_vl[f"hour_{hr}"] = (vl["hour"] == hr).astype(int)
                    X_vl = X_vl.drop(columns=["time", "hour"], errors="ignore")
                y_vl = vl["target_direction"].values if len(vl) > 0 else None

                X_tu = add_time_encodings(tu[feat_cols + ["time", "hour"]].copy())
                for hr in HOURS:
                    X_tu[f"hour_{hr}"] = (tu["hour"] == hr).astype(int)
                X_tu = X_tu.drop(columns=["time", "hour"], errors="ignore")
                y_tu = tu["target_direction"].values

                all_cols = sorted(set(X_tr.columns) | set(X_tu.columns) | (set(X_vl.columns) if X_vl is not None else set()))
                X_tr = align_columns(X_tr, all_cols)
                X_vl = align_columns(X_vl, all_cols) if X_vl is not None else None
                X_tu = align_columns(X_tu, all_cols)

                model = DirectionModel(centre_backend="lightgbm", halfwidth_backend="lightgbm")
                model.fit_centre(X_tr, y_tr, X_vl, y_vl)
                model.fit_halfwidth(X_tr, y_tr, X_vl, y_vl)
                model.conformal_calibrate(X_tu, y_tu)

                lo, mid, hi = model.predict(X_tu)
                cws = circular_winkler_score(y_tu, lo, hi, alpha=0.1)
                print(f"  tune cWS={cws:.1f}")

                sp = SAVE_DIR_DIR / region / level / f"d{horizon}"
                sp.mkdir(parents=True, exist_ok=True)
                with open(sp / "model.pkl", "wb") as f:
                    pickle.dump({
                        "model": model, "feature_cols": all_cols,
                        "region": region, "level": level, "horizon": horizon,
                    }, f)
                results.append({"region": region, "level": level, "horizon": horizon, "cws": round(cws, 1)})

    pd.DataFrame(results).to_csv(SAVE_DIR_DIR / "summary.csv", index=False)
    print(f"Direction training done: {len(results)} models")


def predict_direction_v10():
    all_dir = {}
    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                mp = SAVE_DIR_DIR / region / level / f"d{horizon}" / "model.pkl"
                if not mp.exists():
                    continue
                with open(mp, "rb") as f:
                    art = pickle.load(f)
                dir_model = art["model"]
                feat_cols = art["feature_cols"]

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue
                    inf_enhanced = add_enhanced_features(inf, region=region, window_id=wid)

                    available = [c for c in feat_cols if c in inf_enhanced.columns]
                    missing = set(feat_cols) - set(available) - {
                        c for c in feat_cols if c.startswith(("hour_", "month_", "doy_"))
                    }
                    if missing:
                        for c in missing:
                            inf_enhanced[c] = 0
                        available = list(set(available) | missing)

                    for hour in HOURS:
                        df_pred = inf_enhanced[available].copy()
                        for hr in HOURS:
                            df_pred[f"hour_{hr}"] = int(hr == hour)
                        dt = pd.to_datetime(inf["time"])
                        df_pred["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        df_pred["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
                        df_pred["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values

                        X = align_columns(df_pred, feat_cols)
                        d05, d50, d95 = dir_model.predict(X)

                        lats = inf["latitude"].astype(float).round(2).values
                        lons = inf["longitude"].astype(float).round(2).values
                        for i in range(len(inf)):
                            key = (wid, region, lats[i], lons[i], horizon, hour, str(level))
                            all_dir[key] = (float(d05[i]), float(d50[i]), float(d95[i]))

        print(f"  {region}: {len(all_dir):,} dir entries")
    return all_dir


def train_speed_v10():
    print("\n" + "=" * 60)
    print("V10: Training residual speed models (enhanced features)")
    print("=" * 60)
    SAVE_DIR_SPEED.mkdir(parents=True, exist_ok=True)

    for region in REGIONS:
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        features = add_enhanced_features(features, region=region)
        feat_cols = get_feature_cols_enhanced(features.columns)

        print(f"\n=== {region}: {len(feat_cols)} features ===")

        for level in ALL_LEVELS:
            rean = load_reanalysis_level(region, level)

            for horizon in HORIZONS:
                hour_frames = []
                for hour in HOURS:
                    fm = features.copy()
                    fm["target_time"] = fm["time"] + pd.Timedelta(days=horizon, hours=hour)

                    merged = fm.merge(
                        rean.rename(columns={"time": "target_time", "speed": "target_speed"}),
                        on=["target_time", "latitude", "longitude"],
                        how="inner",
                    ).dropna(subset=["target_speed"])
                    if len(merged) == 0:
                        continue

                    hres_spd = compute_hres_speed(merged, level, horizon, hour)
                    if hres_spd is None:
                        continue

                    merged["residual"] = merged["target_speed"].values - hres_spd
                    merged["hour"] = hour
                    merged["horizon"] = horizon
                    hour_frames.append(merged)

                if not hour_frames:
                    continue

                df = pd.concat(hour_frames, ignore_index=True)
                if len(df) > 200_000:
                    df = df.sample(n=200_000, random_state=42)
                tr, vl, tu, ho = split_by_time(df)
                print(f"  {level}/d{horizon}: train={len(tr):,} val={len(vl):,}")

                if len(tr) < 200:
                    continue

                X_tr = add_time_encodings(tr[feat_cols + ["time"]].copy())
                X_tr["horizon"] = horizon
                for hr in HOURS:
                    X_tr[f"hour_{hr}"] = (tr["hour"] == hr).astype(int)
                for h in HORIZONS:
                    X_tr[f"horizon_{h}"] = int(h == horizon)
                hres_tr = compute_hres_speed(tr, level, horizon, 0)
                if hres_tr is not None:
                    X_tr["hres_speed"] = hres_tr
                X_tr = X_tr.drop(columns=["time"], errors="ignore")
                y_tr = tr["residual"].values.astype(np.float32)

                X_vl = add_time_encodings(vl[feat_cols + ["time"]].copy()) if len(vl) > 0 else None
                if X_vl is not None:
                    X_vl["horizon"] = horizon
                    for hr in HOURS:
                        X_vl[f"hour_{hr}"] = (vl["hour"] == hr).astype(int)
                    for h in HORIZONS:
                        X_vl[f"horizon_{h}"] = int(h == horizon)
                    hres_vl = compute_hres_speed(vl, level, horizon, 0)
                    if hres_vl is not None:
                        X_vl["hres_speed"] = hres_vl
                    X_vl = X_vl.drop(columns=["time"], errors="ignore")
                y_vl = vl["residual"].values.astype(np.float32) if len(vl) > 0 else None

                all_cols = sorted(set(X_tr.columns) | (set(X_vl.columns) if X_vl is not None else set()))
                X_tr = align_columns(X_tr, all_cols)
                X_vl = align_columns(X_vl, all_cols) if X_vl is not None else None

                models = {}
                for q in [0.05, 0.50, 0.95]:
                    m = LGBMRegressor(objective="quantile", alpha=q, **LGBM_PARAMS)
                    if X_vl is not None and len(X_vl) > 50:
                        m.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)],
                              callbacks=[__import__("lightgbm").early_stopping(50, verbose=False)])
                    else:
                        m.fit(X_tr, y_tr)
                    models[q] = m

                sp = SAVE_DIR_SPEED / region / level / f"d{horizon}"
                sp.mkdir(parents=True, exist_ok=True)
                with open(sp / "model.pkl", "wb") as f:
                    pickle.dump({
                        "models": models, "feature_cols": all_cols,
                        "region": region, "level": level, "horizon": horizon,
                    }, f)

                if X_vl is not None and len(X_vl) > 0:
                    r05, r95 = models[0.05].predict(X_vl), models[0.95].predict(X_vl)
                    hres_v = compute_hres_speed(vl, level, horizon, 0)
                    if hres_v is not None:
                        actual = y_vl + hres_v
                        q05f, q95f = np.maximum(hres_v + r05, 0), hres_v + r95
                        cov = ((actual >= q05f) & (actual <= q95f)).mean()
                        print(f"    val coverage={cov:.3f}")

    print("Speed training done")


def compute_cqr_v10():
    print("\n" + "=" * 60)
    print("V10: CQR calibration")
    print("=" * 60)
    CQR_DIR.mkdir(parents=True, exist_ok=True)
    offsets = {}
    t0 = time.time()

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        features = add_enhanced_features(features, region=region)
        feat_cols = get_feature_cols_enhanced(features.columns)

        if len(features) > 200_000:
            features = features.sample(n=200_000, random_state=42).reset_index(drop=True)

        for level in ALL_LEVELS:
            rean = load_reanalysis_level(region, level)
            t_lev = time.time()
            for horizon in HORIZONS:
                mp = SAVE_DIR_SPEED / region / level / f"d{horizon}" / "model.pkl"
                if not mp.exists():
                    continue
                with open(mp, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                model_feat_cols = art["feature_cols"]

                val_frames = []
                for hour in HOURS:
                    sub = features[["time", "latitude", "longitude"] + feat_cols].copy()
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

                    hres_spd = compute_hres_speed(merged, level, horizon, hour)
                    if hres_spd is None:
                        continue
                    merged["residual"] = merged["target_speed"].values - hres_spd
                    merged["hres_speed"] = hres_spd
                    val_frames.append(merged)

                if not val_frames:
                    continue

                df = pd.concat(val_frames, ignore_index=True)
                if len(df) > 15_000:
                    df = df.sample(n=15_000, random_state=42)

                tr, vl, tu, ho = split_by_time(df)
                val_data = vl if len(vl) > 50 else tu
                if len(val_data) < 30:
                    offsets[(region, level, horizon)] = 0.0
                    continue

                X_val = add_time_encodings(val_data[feat_cols + ["time"]].copy())
                X_val["horizon"] = horizon
                for hr in HOURS:
                    X_val[f"hour_{hr}"] = (val_data["hour"] == hr).astype(int)
                for h in HORIZONS:
                    X_val[f"horizon_{h}"] = int(h == horizon)
                hres_v = val_data["hres_speed"].values
                X_val["hres_speed"] = hres_v
                X_val = X_val.drop(columns=["time"], errors="ignore")
                X_val = align_columns(X_val, model_feat_cols)

                pred_05 = models[0.05].predict(X_val)
                pred_95 = models[0.95].predict(X_val)
                actual = val_data["target_speed"].values

                q05f = np.maximum(hres_v + pred_05, 0)
                q95f = hres_v + pred_95
                E = np.maximum(q05f - actual, actual - q95f)
                n = len(E)
                q_idx = min(int(np.ceil((1 - ALPHA) * (n + 1))) - 1, n - 1)
                offset = float(np.sort(E)[q_idx])

                offsets[(region, level, horizon)] = offset
                print(f"  {level}/d{horizon}: CQR offset={offset:.2f}", flush=True)
            print(f"  {level}: done in {time.time()-t_lev:.0f}s")

    with open(CQR_DIR / "offsets.pkl", "wb") as f:
        pickle.dump(offsets, f)
    print(f"\nCQR done in {time.time()-t0:.0f}s")
    print(f"  Non-zero offsets: {sum(1 for v in offsets.values() if v > 0)}")
    return offsets


def compute_hres_speed(df, level, horizon, hour):
    if level in ("10m", "100m"):
        col = f"speed_d{horizon}_h{hour}"
        return df[col].values if col in df.columns else None
    u_col = f"fcst_u_{level}_d{horizon}_h{hour}"
    v_col = f"fcst_v_{level}_d{horizon}_h{hour}"
    if u_col in df.columns and v_col in df.columns:
        return speed_from_uv(df[u_col].values, df[v_col].values)
    return None


def generate_v10():
    print("\n" + "=" * 60)
    print("Generating V10 submission")
    print("=" * 60)

    with open(CQR_DIR / "offsets.pkl", "rb") as f:
        offsets = pickle.load(f)

    all_rows = []
    for region in REGIONS:
        for level in ALL_LEVELS:
            for horizon in HORIZONS:
                mp = SAVE_DIR_SPEED / region / level / f"d{horizon}" / "model.pkl"
                if not mp.exists():
                    continue
                with open(mp, "rb") as f:
                    art = pickle.load(f)
                models = art["models"]
                feat_cols = art["feature_cols"]
                offset = offsets.get((region, level, horizon), 0.0)

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue
                    inf = add_enhanced_features(inf, region=region, window_id=wid)

                    for hour in HOURS:
                        feat_cols_base = get_feature_cols_enhanced(inf.columns)
                        X = add_time_encodings(inf[feat_cols_base + ["time"]].copy())
                        X["horizon"] = horizon
                        for hr in HOURS:
                            X[f"hour_{hr}"] = int(hr == hour)
                        for h in HORIZONS:
                            X[f"horizon_{h}"] = int(h == horizon)
                        hres_spd = compute_hres_speed(inf, level, horizon, hour)
                        if hres_spd is not None:
                            X["hres_speed"] = hres_spd
                        else:
                            continue
                        X = X.drop(columns=["time"], errors="ignore")
                        X = align_columns(X, feat_cols)

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
                                "latitude": lats[i], "longitude": lons[i], "station": "",
                                "horizon": horizon, "hour": hour, "level": str(level),
                                "q05": q05[i], "q50": q50[i], "q95": q95[i],
                            })

    speed_df = pd.DataFrame(all_rows)
    print(f"  Speed rows: {len(speed_df):,}")

    print("  Generating hybrid direction (pooled d1/d7 + per-horizon d14)...")
    all_dir = generate_hybrid_direction(
        perhoriz_dir=SAVE_DIR_DIR,
        d14_only_perhoriz=True,
    )
    dir_df = direction_df_from_dict(all_dir)

    merge_keys = ["window", "region", "latitude", "longitude", "horizon", "hour", "level"]
    for df in [speed_df, dir_df]:
        for c in ["latitude", "longitude"]:
            df[c] = df[c].astype(float).round(2)
        df["horizon"] = df["horizon"].astype(int)
        df["hour"] = df["hour"].astype(int)

    grid = speed_df.merge(dir_df, on=merge_keys, how="left")
    grid = fix_crossing(grid)

    baseline = load_baseline()
    bl_stations = apply_height_correction(baseline[baseline["type"] == "station"].copy())

    submission = pd.concat([grid, bl_stations], ignore_index=True)
    print(f"  Total rows: {len(submission):,}")
    save_submission(submission, "v10")


if __name__ == "__main__":
    t0 = time.time()
    train_direction_v10()
    train_speed_v10()
    compute_cqr_v10()
    generate_v10()
    print(f"\nV10 done in {(time.time()-t0)/60:.1f} min")
