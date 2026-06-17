"""V32: Targeted compound submission.

Strategy: start from v31, only change cells that we can improve:
1. Station speed d14: blend v32 enriched model + analog ensemble (50/50)
2. Station speed d1/d7: keep v31 values (proven v19 models)
3. Station direction: bias correction where it helps on TUNE, keep v31 otherwise
4. Grid: unchanged from v31

Usage: PYTHONPATH=. python src/pipeline/run_v32.py
"""
from __future__ import annotations

import pickle
import time

import catboost as cb
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.data.paths import (
    ALPHA,
    HORIZONS,
    HOURS,
    LOGS_DIR,
    PRESSURE_LEVELS,
    PROJECT_ROOT,
    REGIONS,
    SCORING_DIR,
    TRAIN_DIR,
    TUNE_END,
    TUNE_START,
    VAL_END,
    VAL_START,
)
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import fix_crossing, save_submission
from src.scoring.winkler import _circ_dist

SAVE_DIR = LOGS_DIR / "station_speed_models_v32"
PERHORIZ_DIR = LOGS_DIR / "direction_models_v7"

_STATION_MAP = {
    "NS_01": 0, "NS_02": 1, "NS_03": 2, "NS_04": 3, "NS_05": 4,
    "NS_06": 5, "NS_07": 6, "NS_08": 7,
    "ECS_01": 10, "ECS_02": 11, "ECS_03": 12, "ECS_04": 13,
    "ECS_05": 14, "ECS_06": 15, "ECS_07": 16,
}


def _build_features(df, hour):
    result = pd.DataFrame(index=df.index)
    for h_key in ["d1", "d7", "d10"]:
        sp = f"fcst_speed_{h_key}_h{hour}"
        dr = f"fcst_dir_{h_key}_h{hour}"
        result[f"fcst_spd_{h_key}"] = df[sp].astype(float) if sp in df.columns else np.nan
        result[f"fcst_dir_{h_key}"] = df[dr].astype(float) if dr in df.columns else np.nan
    for level in ["1000", "850", "500"]:
        for h_key in ["d1", "d7", "d10"]:
            u_col = f"fcst_u_{level}_{h_key}_h{hour}"
            v_col = f"fcst_v_{level}_{h_key}_h{hour}"
            if u_col in df.columns and v_col in df.columns:
                u = df[u_col].astype(float).values
                v = df[v_col].astype(float).values
                result[f"pspd_{level}_{h_key}"] = np.sqrt(u**2 + v**2)
            else:
                result[f"pspd_{level}_{h_key}"] = np.nan
    for lo, hi in [("1000", "850"), ("850", "500")]:
        for h_key in ["d1", "d7", "d10"]:
            lo_c, hi_c = f"pspd_{lo}_{h_key}", f"pspd_{hi}_{h_key}"
            if lo_c in result.columns and hi_c in result.columns:
                result[f"shear_{lo}_{hi}_{h_key}"] = result[lo_c] - result[hi_c]
    simple = [
        "ws10", "ws100", "wind_shear", "wd10", "wd100",
        "t2m", "msl", "blh", "cape", "sst", "z700",
        "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d",
        "msl_lag1d", "msl_lag3d", "msl_lag7d",
        "t2m_lag1d", "t2m_lag3d", "z700_lag1d", "z700_lag3d",
        "nao_proxy", "natl_pc1", "elevation",
    ]
    for c in simple:
        if c in df.columns:
            result[c] = df[c].astype(float)
    if "height_m" in df.columns:
        result["height_m"] = df["height_m"].astype(float)
    if "latitude" in df.columns:
        result["stat_lat"] = df["latitude"].astype(float)
    if "longitude" in df.columns:
        result["stat_lon"] = df["longitude"].astype(float)
    dt = pd.to_datetime(df["time"]) if "time" in df.columns else pd.to_datetime(df["issue_time"])
    result["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
    result["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
    result["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365.0).values
    result["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365.0).values
    if "station" in df.columns:
        result["station_id"] = df["station"].map(_STATION_MAP).fillna(-1).astype(int).values
    result["hour"] = hour
    return result


def _get_feat_cols():
    cols = []
    for h in ["d1", "d7", "d10"]:
        cols += [f"fcst_spd_{h}", f"fcst_dir_{h}"]
    for lv in ["1000", "850", "500"]:
        for h in ["d1", "d7", "d10"]:
            cols.append(f"pspd_{lv}_{h}")
    for lo, hi in [("1000", "850"), ("850", "500")]:
        for h in ["d1", "d7", "d10"]:
            cols.append(f"shear_{lo}_{hi}_{h}")
    cols += [
        "ws10", "ws100", "wind_shear", "wd10", "wd100",
        "t2m", "msl", "blh", "cape", "sst", "z700",
        "ws10_rmean3d", "ws10_rstd3d", "ws10_rmean7d",
        "msl_lag1d", "msl_lag3d", "msl_lag7d",
        "t2m_lag1d", "t2m_lag3d", "z700_lag1d", "z700_lag3d",
        "nao_proxy", "natl_pc1", "elevation",
        "height_m", "stat_lat", "stat_lon",
        "month_sin", "month_cos", "doy_sin", "doy_cos", "station_id", "hour",
    ]
    return cols


def _finalize(X, fc):
    for c in fc:
        if c not in X.columns:
            X[c] = 0.0
    return X[fc].fillna(0)


def train_d14_models():
    print("=" * 60)
    print("V32: Training d14 station speed (LGB + analog)")
    print("=" * 60)
    t0 = time.time()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    fc = _get_feat_cols()

    for region in REGIONS:
        print(f"\n=== {region} ===")
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)

        obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
        obs["time"] = pd.to_datetime(obs["time"])
        obs = obs.dropna(subset=["speed"])

        region_meta = meta[meta["region"] == region]

        all_rows = []
        for _, mrow in region_meta.iterrows():
            sid = mrow["station"]
            nlat = round(float(mrow["nearest_grid_lat"]), 2)
            nlon = round(float(mrow["nearest_grid_lon"]), 2)
            stat_obs = obs[obs["station"] == sid]
            if len(stat_obs) == 0:
                continue
            gf = features[(features["latitude"] == nlat) & (features["longitude"] == nlon)]
            if len(gf) == 0:
                continue
            for hour in HOURS:
                g = gf.copy()
                g["target_time"] = g["time"] + pd.Timedelta(days=14, hours=hour)
                m = g.merge(
                    stat_obs[["time", "speed"]].rename(columns={"time": "target_time", "speed": "obs_speed"}),
                    on="target_time", how="inner",
                ).dropna(subset=["obs_speed"])
                if len(m) < 5:
                    continue
                m["station"] = sid
                m["height_m"] = float(mrow["height_m"])
                m["latitude"] = float(mrow["latitude"])
                m["longitude"] = float(mrow["longitude"])
                m["hour"] = hour
                all_rows.append(m)

        if not all_rows:
            continue
        df = pd.concat(all_rows, ignore_index=True)
        print(f"  Total d14 samples: {len(df):,}")

        all_X, all_y, all_t, all_s = [], [], [], []
        for hour in HOURS:
            hr = df[df["hour"] == hour]
            if len(hr) == 0:
                continue
            all_X.append(_build_features(hr, hour))
            all_y.append(hr["obs_speed"].values.astype(float))
            all_t.append(hr["time"])
            all_s.append(hr["station"].values)

        X = pd.concat(all_X, ignore_index=True)
        y = np.concatenate(all_y)
        times = pd.concat(all_t, ignore_index=True)
        stations_arr = np.concatenate(all_s)
        X = _finalize(X, fc)

        tr_m = times < VAL_START
        vl_m = (times >= VAL_START) & (times <= VAL_END)
        tu_m = (times >= TUNE_START) & (times <= TUNE_END)

        X_tr, y_tr = X[tr_m].values.astype(np.float32), y[tr_m]
        X_vl = X[vl_m].values.astype(np.float32) if vl_m.sum() > 0 else None
        y_vl = y[vl_m] if vl_m.sum() > 0 else None
        X_tu = X[tu_m].values.astype(np.float32) if tu_m.sum() > 0 else None
        y_tu = y[tu_m] if tu_m.sum() > 0 else None
        print(f"  Train: {len(X_tr):,}, Val: {vl_m.sum():,}, TUNE: {tu_m.sum():,}")

        models = {}
        for q in [0.05, 0.50, 0.95]:
            params = {
                "objective": "quantile", "alpha": q,
                "learning_rate": 0.05, "num_leaves": 63,
                "min_child_samples": 30, "feature_fraction": 0.7,
                "bagging_fraction": 0.8, "bagging_freq": 1,
                "verbose": -1, "n_jobs": -1,
            }
            dtrain = lgb.Dataset(X_tr, label=y_tr)
            cbs = [lgb.log_evaluation(0)]
            if X_vl is not None and len(X_vl) > 20:
                dval = lgb.Dataset(X_vl, label=y_vl, reference=dtrain)
                cbs.append(lgb.early_stopping(30, verbose=False))
                m = lgb.train(params, dtrain, 500, valid_sets=[dval], callbacks=cbs)
            else:
                m = lgb.train(params, dtrain, 300, callbacks=cbs)
            models[q] = m

        cqr = {}
        s_tu = stations_arr[tu_m.values] if tu_m.sum() > 0 else []
        for sid in np.unique(s_tu) if len(s_tu) > 0 else []:
            sm = s_tu == sid
            Xs, ys = X_tu[sm], y_tu[sm]
            if len(ys) < 5:
                cqr[sid] = 0.0
                continue
            p05, p95 = models[0.05].predict(Xs), models[0.95].predict(Xs)
            E = np.maximum(p05 - ys, ys - p95)
            n = len(E)
            qi = min(int(np.ceil((1 - ALPHA) * (n + 1))) - 1, n - 1)
            cqr[sid] = float(np.sort(E)[max(qi, 0)])
        for sid in region_meta["station"].values:
            if sid not in cqr:
                cqr[sid] = 0.0

        save_dir = SAVE_DIR / region / "d14"
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(save_dir / "model_lgb.pkl", "wb") as f:
            pickle.dump({"models": models, "feature_cols": fc, "cqr": cqr}, f)

        if X_tu is not None and len(X_tu) > 0:
            p05 = models[0.05].predict(X_tu)
            p50 = models[0.50].predict(X_tu)
            p95 = models[0.95].predict(X_tu)
            cov = np.mean((y_tu >= p05) & (y_tu <= p95))
            print(f"  LGB d14: cov={cov:.3f} width={np.mean(p95-p05):.2f}")

        # Analog ensemble
        analog_cols = ["ws10", "ws100", "wind_shear", "msl", "t2m", "z700", "blh",
                       "ws10_rmean3d", "ws10_rstd3d", "msl_lag1d", "msl_lag3d", "nao_proxy"]
        dt = pd.to_datetime(df["time"])
        df["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
        df["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
        acols = analog_cols + ["month_sin", "month_cos"]

        for _, mrow in region_meta.iterrows():
            sid = mrow["station"]
            nlat = round(float(mrow["nearest_grid_lat"]), 2)
            nlon = round(float(mrow["nearest_grid_lon"]), 2)
            stat_obs = obs[obs["station"] == sid]
            if len(stat_obs) < 50:
                continue
            gf = features[(features["latitude"] == nlat) & (features["longitude"] == nlon)]
            if len(gf) == 0:
                continue
            rows = []
            for hour in HOURS:
                g = gf.copy()
                g["target_time"] = g["time"] + pd.Timedelta(days=14, hours=hour)
                mg = g.merge(
                    stat_obs[["time", "speed"]].rename(columns={"time": "target_time", "speed": "obs_speed"}),
                    on="target_time", how="inner",
                ).dropna(subset=["obs_speed"])
                if len(mg) < 5:
                    continue
                mg["hour"] = hour
                rows.append(mg)
            if not rows:
                continue
            sdf = pd.concat(rows, ignore_index=True)
            dts = pd.to_datetime(sdf["time"])
            sdf["month_sin"] = np.sin(2 * np.pi * dts.dt.month / 12.0).values
            sdf["month_cos"] = np.cos(2 * np.pi * dts.dt.month / 12.0).values

            tr = sdf["time"] < VAL_START
            tu = (sdf["time"] >= TUNE_START) & (sdf["time"] <= TUNE_END)
            Xa_tr = sdf.loc[tr, acols].fillna(0).values.astype(np.float32)
            ya_tr = sdf.loc[tr, "obs_speed"].values.astype(float)
            if len(Xa_tr) < 30:
                continue
            K = min(50, len(Xa_tr))
            nn = NearestNeighbors(n_neighbors=K, metric="euclidean", n_jobs=-1)
            nn.fit(Xa_tr)
            if tu.sum() > 10:
                Xa_tu = sdf.loc[tu, acols].fillna(0).values.astype(np.float32)
                ya_tu = sdf.loc[tu, "obs_speed"].values.astype(float)
                _, idx = nn.kneighbors(Xa_tu)
                covs, wids = [], []
                for i in range(len(ya_tu)):
                    ns = ya_tr[idx[i]]
                    q5, q9 = np.percentile(ns, 5), np.percentile(ns, 95)
                    covs.append(q5 <= ya_tu[i] <= q9)
                    wids.append(q9 - q5)
                print(f"  Analog {sid}: K={K} cov={np.mean(covs):.3f} width={np.mean(wids):.2f}")

            asd = SAVE_DIR / region / "d14_analog"
            asd.mkdir(parents=True, exist_ok=True)
            with open(asd / f"{sid}.pkl", "wb") as f:
                pickle.dump({"nn": nn, "y_train": ya_tr, "acols": acols, "K": K}, f)

    print(f"Done in {time.time()-t0:.0f}s")


def train_direction_calibration():
    print("\n" + "=" * 60)
    print("V32: Station direction bias calibration")
    print("=" * 60)
    t0 = time.time()
    STATION_LEVEL = "10m"
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    offsets = {}
    biases = {}

    for region in REGIONS:
        features = load_features(region)
        features["time"] = pd.to_datetime(features["time"])
        features["latitude"] = features["latitude"].astype(float).round(2)
        features["longitude"] = features["longitude"].astype(float).round(2)
        obs = pd.read_parquet(TRAIN_DIR / f"stations_{region}_6h.parquet")
        obs["time"] = pd.to_datetime(obs["time"])
        obs = obs.dropna(subset=["direction"])
        region_meta = meta[meta["region"] == region]

        for horizon in HORIZONS:
            mp = PERHORIZ_DIR / region / STATION_LEVEL / f"d{horizon}" / "model.pkl"
            if not mp.exists():
                continue
            with open(mp, "rb") as f:
                art = pickle.load(f)
            dir_model, feat_cols = art["model"], art["feature_cols"]

            for _, row in region_meta.iterrows():
                sid = row["station"]
                nlat = round(float(row["nearest_grid_lat"]), 2)
                nlon = round(float(row["nearest_grid_lon"]), 2)
                so = obs[(obs["station"] == sid) & obs["direction"].notna()]
                if len(so) == 0:
                    offsets[(sid, horizon)] = 0.0
                    biases[(sid, horizon)] = 0.0
                    continue
                gf = features[(features["latitude"] == nlat) & (features["longitude"] == nlon)]
                if len(gf) == 0:
                    offsets[(sid, horizon)] = 0.0
                    biases[(sid, horizon)] = 0.0
                    continue

                all_y, all_d50, all_d05, all_d95 = [], [], [], []
                for hour in HOURS:
                    g = gf.copy()
                    g["target_time"] = g["time"] + pd.Timedelta(days=horizon, hours=hour)
                    tm = (g["time"] >= TUNE_START) & (g["time"] <= TUNE_END)
                    g = g[tm]
                    if len(g) == 0:
                        continue
                    mg = g.merge(
                        so[["time", "direction"]].rename(columns={"time": "target_time", "direction": "obs_dir"}),
                        on="target_time", how="inner",
                    )
                    if len(mg) < 5:
                        continue
                    from src.pipeline.run_v18 import _build_direction_features
                    X = _build_direction_features(mg, feat_cols, hour)
                    d05, d50, d95 = dir_model.predict(X)
                    all_y.extend(mg["obs_dir"].values.tolist())
                    all_d50.extend(d50.tolist())
                    all_d05.extend(d05.tolist())
                    all_d95.extend(d95.tolist())

                if len(all_y) < 10:
                    offsets[(sid, horizon)] = 0.0
                    biases[(sid, horizon)] = 0.0
                    continue

                y = np.array(all_y)
                d50 = np.array(all_d50)
                d05 = np.array(all_d05)
                d95 = np.array(all_d95)

                diff = y - d50
                bias_arr = np.where(diff > 180, diff - 360, np.where(diff < -180, diff + 360, diff))
                mean_bias = float(np.mean(bias_arr))

                cd50 = (d50 + mean_bias) % 360.0
                err_before = np.mean(_circ_dist(y, d50))
                err_after = np.mean(_circ_dist(y, cd50))

                if err_after < err_before:
                    biases[(sid, horizon)] = mean_bias
                else:
                    biases[(sid, horizon)] = 0.0

                ce = _circ_dist(y, cd50 if biases[(sid, horizon)] != 0.0 else d50)
                hw = ((d95 - d05) % 360.0) / 2.0
                scores = ce - hw
                n = len(scores)
                ql = min(np.ceil((n + 1) * (1 - ALPHA)) / n, 1.0)
                offsets[(sid, horizon)] = float(np.quantile(scores, ql))

                print(f"  {sid}/d{horizon}: bias={biases[(sid,horizon)]:+.1f} off={offsets[(sid,horizon)]:.1f} "
                      f"err {err_before:.1f}->{err_after:.1f}")

    sp = SAVE_DIR / "station_dir_cal_v32.pkl"
    sp.parent.mkdir(parents=True, exist_ok=True)
    with open(sp, "wb") as f:
        pickle.dump({"offsets": offsets, "biases": biases}, f)
    print(f"Done in {time.time()-t0:.0f}s")
    return offsets, biases


def predict_d14():
    print("\nPredicting d14 station speed...")
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    fc = _get_feat_cols()
    preds = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]
        mp = SAVE_DIR / region / "d14" / "model_lgb.pkl"
        if not mp.exists():
            print(f"  {region}: no d14 model")
            continue

        with open(mp, "rb") as f:
            art = pickle.load(f)
        models, cqr = art["models"], art["cqr"]

        for _, mrow in region_meta.iterrows():
            sid = mrow["station"]
            stat_h = float(mrow["height_m"])
            nlat = round(float(mrow["nearest_grid_lat"]), 2)
            nlon = round(float(mrow["nearest_grid_lon"]), 2)
            off = cqr.get(sid, 0.0)

            ap = SAVE_DIR / region / "d14_analog" / f"{sid}.pkl"
            analog_art = None
            if ap.exists():
                with open(ap, "rb") as f:
                    analog_art = pickle.load(f)

            for wid in range(1, 9):
                try:
                    inf = load_inference_features(wid, region)
                except FileNotFoundError:
                    continue
                grid = inf[
                    (inf["latitude"].astype(float).round(2) == nlat)
                    & (inf["longitude"].astype(float).round(2) == nlon)
                ].copy()
                if len(grid) == 0:
                    continue

                for hour in HOURS:
                    grid["height_m"] = stat_h
                    grid["latitude"] = float(mrow["latitude"])
                    grid["longitude"] = float(mrow["longitude"])
                    grid["station"] = sid
                    grid["hour"] = hour

                    X = _finalize(_build_features(grid, hour), fc)
                    X_arr = X.values.astype(np.float32)

                    m05 = np.maximum(models[0.05].predict(X_arr) - off, 0)
                    m50 = models[0.50].predict(X_arr)
                    m95 = models[0.95].predict(X_arr) + off

                    if analog_art is not None:
                        gc = grid.copy()
                        dt = pd.to_datetime(gc["time"])
                        gc["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12.0).values
                        gc["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12.0).values
                        Xa = gc[analog_art["acols"]].fillna(0).values.astype(np.float32)
                        nn, yt, K = analog_art["nn"], analog_art["y_train"], analog_art["K"]
                        _, idx = nn.kneighbors(Xa)
                        a05 = np.array([np.percentile(yt[idx[i]], 5) for i in range(len(Xa))])
                        a50 = np.array([np.percentile(yt[idx[i]], 50) for i in range(len(Xa))])
                        a95 = np.array([np.percentile(yt[idx[i]], 95) for i in range(len(Xa))])

                        w = 0.5
                        q05 = w * m05 + (1-w) * a05
                        q50 = w * m50 + (1-w) * a50
                        q95 = w * m95 + (1-w) * a95
                    else:
                        q05, q50, q95 = m05, m50, m95

                    q05, q50, q95 = np.sort(np.column_stack([q05, q50, q95]), axis=1).T
                    for i in range(len(grid)):
                        preds[(wid, region, sid, 14, int(hour))] = (float(q05[i]), float(q50[i]), float(q95[i]))

        print(f"  {region}: {len(preds)} d14 entries")
    return preds


def predict_direction(offsets, biases):
    print("\nPredicting station direction (v32)...")
    STATION_LEVEL = "10m"
    meta = pd.read_csv(SCORING_DIR / "station_metadata.csv")
    preds = {}

    for region in REGIONS:
        region_meta = meta[meta["region"] == region]
        for horizon in HORIZONS:
            mp = PERHORIZ_DIR / region / STATION_LEVEL / f"d{horizon}" / "model.pkl"
            if not mp.exists():
                continue
            with open(mp, "rb") as f:
                art = pickle.load(f)
            dir_model, feat_cols = art["model"], art["feature_cols"]

            for _, row in region_meta.iterrows():
                sid = row["station"]
                nlat = round(float(row["nearest_grid_lat"]), 2)
                nlon = round(float(row["nearest_grid_lon"]), 2)
                off = offsets.get((sid, horizon), 0.0)
                bias = biases.get((sid, horizon), 0.0)

                for wid in range(1, 9):
                    try:
                        inf = load_inference_features(wid, region)
                    except FileNotFoundError:
                        continue
                    grid = inf[
                        (inf["latitude"].astype(float).round(2) == nlat)
                        & (inf["longitude"].astype(float).round(2) == nlon)
                    ].copy()
                    if len(grid) == 0:
                        continue
                    available = [c for c in feat_cols if c in grid.columns]
                    missing = set(feat_cols) - set(available) - {
                        c for c in feat_cols if c.startswith(("hour_", "month_", "doy_"))
                    }
                    if missing:
                        continue

                    for hour in HOURS:
                        from src.pipeline.run_v18 import _build_direction_features
                        X = _build_direction_features(grid, feat_cols, hour)
                        d05, d50, d95 = dir_model.predict(X)
                        for i in range(len(X)):
                            d50_i = (float(d50[i]) + bias) % 360.0
                            d05_i = float(d05[i])
                            d95_i = float(d95[i])
                            if off != 0.0 or bias != 0.0:
                                hw = ((d95_i - d05_i) % 360.0) / 2.0
                                new_hw = max(hw + off, 0.0)
                                d05_i = (d50_i - new_hw) % 360.0
                                d95_i = (d50_i + new_hw) % 360.0
                            preds[(wid, region, sid, horizon, hour)] = (d05_i, d50_i, d95_i)
        print(f"  {region}: {len(preds)} entries")
    return preds


def generate_v32():
    print("\n" + "=" * 60)
    print("V32: Targeted compound submission")
    print("=" * 60)
    t0 = time.time()

    print("\n[1/4] Training d14 models...")
    train_d14_models()

    print("\n[2/4] Training direction calibration...")
    offsets, biases = train_direction_calibration()

    print("\n[3/4] Loading v31 base...")
    v31_path = PROJECT_ROOT / "starting-kit" / "phase_1" / "predictions_v31.csv"
    base = pd.read_csv(v31_path, low_memory=False)
    print(f"  Base rows: {len(base):,}")
    grid = base[base["type"] == "grid"].copy()
    stations = base[base["type"] == "station"].copy()
    stations["horizon"] = stations["horizon"].astype(int)
    stations["hour"] = stations["hour"].astype(int)

    print("\n[4/4] Predicting and assembling...")

    # Only replace d14 station speed
    d14_speed = predict_d14()
    print(f"  d14 speed entries: {len(d14_speed)}")
    d14_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "station": k[2], "horizon": k[3], "hour": k[4],
         "q05": v[0], "q50": v[1], "q95": v[2]}
        for k, v in d14_speed.items()
    ])
    if len(d14_df) > 0:
        d14_df["horizon"] = d14_df["horizon"].astype(int)
        d14_df["hour"] = d14_df["hour"].astype(int)
        mks = ["window", "region", "station", "horizon", "hour"]
        d14_only = stations[stations["horizon"] == 14].copy()
        d14_rest = stations[stations["horizon"] != 14].copy()
        d14_only = d14_only.merge(d14_df, on=mks, how="left", suffixes=("_old", "_new"))
        for qc in ["q05", "q50", "q95"]:
            nc, oc = f"{qc}_new", f"{qc}_old"
            if nc in d14_only.columns:
                d14_only[qc] = d14_only[nc].fillna(d14_only[oc])
                d14_only = d14_only.drop(columns=[nc, oc])
        stations = pd.concat([d14_rest, d14_only], ignore_index=True)

    # Replace station direction
    station_dir = predict_direction(offsets, biases)
    print(f"  Station dir entries: {len(station_dir)}")
    sdir_df = pd.DataFrame([
        {"window": k[0], "region": k[1], "station": k[2], "horizon": k[3], "hour": k[4],
         "dir_05": v[0], "dir_50": v[1], "dir_95": v[2]}
        for k, v in station_dir.items()
    ])
    if len(sdir_df) > 0:
        sdir_df["horizon"] = sdir_df["horizon"].astype(int)
        sdir_df["hour"] = sdir_df["hour"].astype(int)
        mks = ["window", "region", "station", "horizon", "hour"]
        stations = stations.merge(sdir_df, on=mks, how="left", suffixes=("_old", "_new"))
        for dc in ["dir_05", "dir_50", "dir_95"]:
            nc, oc = f"{dc}_new", f"{dc}_old"
            if nc in stations.columns:
                stations[dc] = stations[nc].fillna(stations[oc])
                stations = stations.drop(columns=[nc, oc])

    submission = pd.concat([grid, stations], ignore_index=True)
    print(f"\n  Total: {len(submission):,}")
    print(f"  Grid: {len(grid):,}, Station: {len(stations):,}")
    nans = submission[["q05", "q50", "q95", "dir_05", "dir_50", "dir_95"]].isna().sum().sum()
    print(f"  NaN: {nans}")
    q = submission[["q05", "q50", "q95"]].values
    cx = (q[:, 0] > q[:, 1]).sum() + (q[:, 1] > q[:, 2]).sum()
    print(f"  Crossings: {cx}")
    print(f"  Time: {time.time()-t0:.0f}s")
    save_submission(submission, "v32")


if __name__ == "__main__":
    generate_v32()
