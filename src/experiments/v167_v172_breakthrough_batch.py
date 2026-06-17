"""v167-v172: breakthrough-candidate batch from the 2026-05-15 reset.

The batch keeps every candidate as a separate submission artifact. These are
not meant to be submitted blindly as a compound. They encode the next strategic
lanes after v164:

- v167: regime-selected ECS pressure d14 shear/ws3 lambda push.
- v168: ECS pressure d7 high-confidence interval shrink probe.
- v169: NS surface d14 v47 donor replay on the current base.
- v170: NS pressure d14 v47 donor replay on the current base.
- v171: narrow ExtraTrees residual center overlay for ECS surface d1 10m.
- v172: NS station d14 weighted-conformal width rebase, center-frozen.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.paths import HOURS, LOGS_DIR, PROJECT_ROOT
from src.io.dataset import load_features, load_inference_features
from src.pipeline.pipeline_utils import save_submission

VERSION_BASE = "v164"
OUT_DIR = LOGS_DIR / "v167_v172_breakthrough_batch"
PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"

Q_COLS = ["q05", "q50", "q95"]
DIR_COLS = ["dir_05", "dir_50", "dir_95"]
KEY_COLS = ["type", "window", "region", "latitude", "longitude", "station", "horizon", "hour", "level"]
SURFACE_LEVELS = {"10m", "100m"}
PRESSURE_LEVELS = {"1000", "925", "850", "700", "500"}


@dataclass(frozen=True)
class CandidateResult:
    version: str
    base_version: str
    description: str
    zip_path: str
    changed_rows: int
    speed_changed_rows: int
    direction_changed_rows: int
    manifest_path: str


def load_predictions(version: str) -> pd.DataFrame:
    path = PHASE1 / f"predictions_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    return pd.read_csv(path, engine="python")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalized_level(frame: pd.DataFrame) -> pd.Series:
    return frame["level"].astype(str)


def pressure_mask(frame: pd.DataFrame, region: str, horizon: int) -> pd.Series:
    level = normalized_level(frame)
    return (
        frame["type"].eq("grid")
        & frame["region"].eq(region)
        & frame["horizon"].astype(int).eq(horizon)
        & ~level.isin(SURFACE_LEVELS)
    )


def surface_mask(frame: pd.DataFrame, region: str, horizon: int) -> pd.Series:
    level = normalized_level(frame)
    return (
        frame["type"].eq("grid")
        & frame["region"].eq(region)
        & frame["horizon"].astype(int).eq(horizon)
        & level.isin(SURFACE_LEVELS)
    )


def station_mask(frame: pd.DataFrame, region: str, horizon: int) -> pd.Series:
    return frame["type"].eq("station") & frame["region"].eq(region) & frame["horizon"].astype(int).eq(horizon)


def assert_same_keys(base: pd.DataFrame, donor: pd.DataFrame, mask: pd.Series, *, donor_name: str) -> None:
    if len(base) != len(donor):
        raise RuntimeError(f"{donor_name} row mismatch: base={len(base)} donor={len(donor)}")
    left = base.loc[mask, KEY_COLS].fillna("").astype(str).reset_index(drop=True)
    right = donor.loc[mask, KEY_COLS].fillna("").astype(str).reset_index(drop=True)
    mismatch = left.ne(right).any(axis=1)
    if bool(mismatch.any()):
        first = int(np.flatnonzero(mismatch.to_numpy())[0])
        raise RuntimeError(f"{donor_name} key mismatch at target row {first}")


def repair_quantiles(frame: pd.DataFrame, mask: pd.Series) -> None:
    q = np.sort(frame.loc[mask, Q_COLS].to_numpy(float), axis=1)
    q[:, 0] = np.maximum(q[:, 0], 0.0)
    frame.loc[mask, Q_COLS] = q


def validate_scope(base: pd.DataFrame, candidate: pd.DataFrame, allowed_q: pd.Series, allowed_dir: pd.Series) -> dict:
    q_changed = candidate[Q_COLS].round(9).ne(base[Q_COLS].round(9)).any(axis=1)
    dir_changed = candidate[DIR_COLS].round(9).ne(base[DIR_COLS].round(9)).any(axis=1)
    non_target_q = int((q_changed & ~allowed_q).sum())
    non_target_dir = int((dir_changed & ~allowed_dir).sum())
    if non_target_q or non_target_dir:
        raise RuntimeError(f"Non-target changes: q={non_target_q}, dir={non_target_dir}")
    q = candidate[Q_COLS].to_numpy(float)
    crossing = int(((q[:, 0] > q[:, 1]) | (q[:, 1] > q[:, 2]) | (q[:, 0] < 0)).sum())
    if crossing:
        raise RuntimeError(f"Quantile crossing/negative rows: {crossing}")
    nans = int(candidate[Q_COLS + DIR_COLS].isna().sum().sum())
    if nans:
        raise RuntimeError(f"NaNs in prediction columns: {nans}")
    return {
        "changed_rows": int((q_changed | dir_changed).sum()),
        "speed_changed_rows": int(q_changed.sum()),
        "direction_changed_rows": int(dir_changed.sum()),
        "non_target_q_rows": non_target_q,
        "non_target_dir_rows": non_target_dir,
        "quantile_crossing_rows": crossing,
        "nan_prediction_values": nans,
    }


def save_candidate(base: pd.DataFrame, candidate: pd.DataFrame, version: str, description: str, allowed_q: pd.Series, allowed_dir: pd.Series, extra: dict) -> CandidateResult:
    checks = validate_scope(base, candidate, allowed_q, allowed_dir)
    zip_path = save_submission(candidate, version)
    manifest = {
        "version": version,
        "base_version": VERSION_BASE,
        "description": description,
        "checks": checks,
        **extra,
        "zip_path": str(zip_path),
    }
    manifest_path = OUT_DIR / f"{version}_manifest.json"
    write_json(manifest_path, manifest)
    return CandidateResult(
        version=version,
        base_version=VERSION_BASE,
        description=description,
        zip_path=str(zip_path),
        changed_rows=checks["changed_rows"],
        speed_changed_rows=checks["speed_changed_rows"],
        direction_changed_rows=checks["direction_changed_rows"],
        manifest_path=str(manifest_path),
    )


def apply_pressure_blend_from_anchor(candidate: pd.DataFrame, mask: pd.Series, anchor: pd.DataFrame, donor: pd.DataFrame, lambdas: pd.Series) -> None:
    for col in Q_COLS:
        candidate.loc[mask, col] = (
            anchor.loc[mask, col].astype(float)
            + lambdas.loc[mask].to_numpy(float) * (donor.loc[mask, col].astype(float) - anchor.loc[mask, col].astype(float))
        )
    repair_quantiles(candidate, mask)


def build_v167(base: pd.DataFrame, anchor: pd.DataFrame, donor: pd.DataFrame) -> CandidateResult:
    version = "v167"
    description = "Regime-selected ECS pressure d14 lambda: v166-style 850 lift plus high-wind 850/925 push to 0.95."
    out = base.copy()
    target = pressure_mask(out, "east_china_sea", 14) & normalized_level(out).isin({"850", "925"})

    work = out.loc[target, ["window", "level", "q50", "q05", "q95"]].copy()
    work["level"] = work["level"].astype(str)
    work["width"] = work["q95"].astype(float) - work["q05"].astype(float)
    window_level = work.groupby(["level", "window"], as_index=False).agg(mean_q50=("q50", "mean"), mean_width=("width", "mean"))
    window_level["score"] = window_level["mean_q50"] + 0.10 * window_level["mean_width"]
    window_level["high_regime"] = False
    for level, group in window_level.groupby("level"):
        cutoff = float(group["score"].median())
        window_level.loc[group.index, "high_regime"] = group["score"] >= cutoff

    high_keys = {
        (str(row.level), int(row.window))
        for row in window_level.itertuples(index=False)
        if bool(row.high_regime)
    }
    lambdas = pd.Series(np.nan, index=out.index, dtype=float)
    level = normalized_level(out)
    # v166-equivalent baseline inside this candidate: 850 goes to 0.80; 925 is already 0.80 in v164.
    lambdas.loc[target & level.eq("850")] = 0.80
    lambdas.loc[target & level.eq("925")] = 0.80
    high = target & pd.Series(
        [(str(lv), int(w)) in high_keys for lv, w in zip(level.to_numpy(), out["window"].to_numpy())],
        index=out.index,
    )
    lambdas.loc[high] = 0.95
    changed = target & lambdas.notna()
    apply_pressure_blend_from_anchor(out, changed, anchor, donor, lambdas)

    allowed_q = changed
    allowed_dir = pd.Series(False, index=out.index)
    diagnostics = {
        "anchor_version": "v53",
        "donor_version": "v55",
        "lambda_policy": "850/925 lambda 0.80, high-regime window-level cells lambda 0.95",
        "high_regime_keys": sorted([f"{lv}:w{w}" for lv, w in high_keys]),
        "changed_by_level": out.loc[changed].groupby(out.loc[changed, "level"].astype(str)).size().to_dict(),
        "window_level_scores": window_level.to_dict(orient="records"),
    }
    return save_candidate(base, out, version, description, allowed_q, allowed_dir, diagnostics)


def build_v168(base: pd.DataFrame) -> CandidateResult:
    version = "v168"
    description = "ECS pressure d7 high-confidence width shrink: q50 fixed, shrink only high-speed/high-width pressure rows."
    out = base.copy()
    target = pressure_mask(out, "east_china_sea", 7)
    level = normalized_level(out)
    work = out.loc[target, ["window", "level", "q05", "q50", "q95"]].copy()
    work["level"] = work["level"].astype(str)
    work["width"] = work["q95"].astype(float) - work["q05"].astype(float)
    work["q50"] = work["q50"].astype(float)

    eligible = pd.Series(False, index=out.index)
    for lv, idx in work.groupby("level").groups.items():
        group = work.loc[idx]
        q50_cut = float(group["q50"].quantile(0.55))
        width_cut = float(group["width"].quantile(0.45))
        idx_series = pd.Index(idx)
        eligible.loc[idx_series] = (group["q50"] >= q50_cut).to_numpy() & (group["width"] >= width_cut).to_numpy()

    idx = out.index[target & eligible]
    q05 = out.loc[idx, "q05"].to_numpy(float)
    q50 = out.loc[idx, "q50"].to_numpy(float)
    q95 = out.loc[idx, "q95"].to_numpy(float)
    lower_hw = np.maximum(q50 - q05, 0.0)
    upper_hw = np.maximum(q95 - q50, 0.0)
    lower_delta = np.minimum(0.035, lower_hw * 0.025)
    upper_delta = np.minimum(0.035, upper_hw * 0.025)
    out.loc[idx, "q05"] = np.maximum(q05 + lower_delta, 0.0)
    out.loc[idx, "q95"] = q95 - upper_delta
    repair_quantiles(out, target & eligible)

    allowed_q = target & eligible
    allowed_dir = pd.Series(False, index=out.index)
    diagnostics = {
        "scope": "grid/east_china_sea/pressure/d7/speed",
        "q50_changed": False,
        "selected_rows": int((target & eligible).sum()),
        "target_rows": int(target.sum()),
        "mean_width_delta_if_coverage_unchanged": float(-np.mean(lower_delta + upper_delta)) if len(idx) else 0.0,
        "changed_by_level": out.loc[target & eligible].groupby(level.loc[target & eligible]).size().to_dict(),
    }
    return save_candidate(base, out, version, description, allowed_q, allowed_dir, diagnostics)


def build_v169_or_v170(base: pd.DataFrame, *, version: str, group: str) -> CandidateResult:
    if group == "surface":
        target = surface_mask(base, "north_sea", 14)
        description = "NS surface d14 high-confidence shrink: q50 fixed, shrink only high-speed/high-width rows."
        max_side_shrink = 0.0030
        pct_of_halfwidth = 0.010
    elif group == "pressure":
        target = pressure_mask(base, "north_sea", 14)
        description = "NS pressure d14 high-confidence shrink: q50 fixed, shrink only high-speed/high-width rows."
        max_side_shrink = 0.0040
        pct_of_halfwidth = 0.010
    else:
        raise ValueError(group)

    out = base.copy()
    work = out.loc[target, ["level", "q05", "q50", "q95"]].copy()
    work["level"] = work["level"].astype(str)
    work["width"] = work["q95"].astype(float) - work["q05"].astype(float)
    work["q50"] = work["q50"].astype(float)
    eligible = pd.Series(False, index=out.index)
    for _, idx in work.groupby("level").groups.items():
        group_frame = work.loc[idx]
        q50_cut = float(group_frame["q50"].quantile(0.55))
        width_cut = float(group_frame["width"].quantile(0.45))
        eligible.loc[pd.Index(idx)] = (
            (group_frame["q50"] >= q50_cut)
            & (group_frame["width"] >= width_cut)
        ).to_numpy()

    selected = target & eligible
    idx = out.index[selected]
    q05 = out.loc[idx, "q05"].to_numpy(float)
    q50 = out.loc[idx, "q50"].to_numpy(float)
    q95 = out.loc[idx, "q95"].to_numpy(float)
    lower_hw = np.maximum(q50 - q05, 0.0)
    upper_hw = np.maximum(q95 - q50, 0.0)
    lower_delta = np.minimum(max_side_shrink, lower_hw * pct_of_halfwidth)
    upper_delta = np.minimum(max_side_shrink, upper_hw * pct_of_halfwidth)
    out.loc[idx, "q05"] = np.maximum(q05 + lower_delta, 0.0)
    out.loc[idx, "q95"] = q95 - upper_delta
    repair_quantiles(out, selected)
    allowed_q = selected
    allowed_dir = pd.Series(False, index=out.index)
    base_width = base.loc[target, "q95"].astype(float) - base.loc[target, "q05"].astype(float)
    cand_width = out.loc[target, "q95"].astype(float) - out.loc[target, "q05"].astype(float)
    diagnostics = {
        "scope": f"grid/north_sea/{group}/d14/speed",
        "target_rows": int(target.sum()),
        "selected_rows": int(selected.sum()),
        "q50_changed": False,
        "max_side_shrink": max_side_shrink,
        "pct_of_halfwidth": pct_of_halfwidth,
        "mean_selected_width_delta_if_coverage_unchanged": float(-np.mean(lower_delta + upper_delta)) if len(idx) else 0.0,
        "mean_q50_delta_vs_base": float((out.loc[target, "q50"].astype(float) - base.loc[target, "q50"].astype(float)).mean()),
        "mean_width_delta_vs_base": float((cand_width - base_width).mean()),
    }
    return save_candidate(base, out, version, description, allowed_q, allowed_dir, diagnostics)


def extra_trees_feature_columns(frame: pd.DataFrame, hour: int) -> list[str]:
    preferred = [
        "latitude",
        "longitude",
        "t2m",
        "msl",
        "sshf",
        "z700",
        "sst",
        "blh",
        "cape",
        f"fcst_speed_d1_h{hour}",
        f"fcst_dir_d1_h{hour}",
        f"fcst_speed_d7_h{hour}",
        f"fcst_dir_d7_h{hour}",
        f"fcst_speed_d10_h{hour}",
        f"fcst_dir_d10_h{hour}",
    ]
    for pressure_level in ("1000", "925", "850", "700", "500"):
        preferred.append(f"fcst_u_{pressure_level}_d1_h{hour}")
        preferred.append(f"fcst_v_{pressure_level}_d1_h{hour}")
    return [col for col in preferred if col in frame.columns]


def fit_extra_trees_hour(train: pd.DataFrame, hour: int) -> tuple[ExtraTreesRegressor, list[str], dict]:
    target_col = f"speed_d1_h{hour}"
    base_col = f"fcst_speed_d1_h{hour}"
    cols = extra_trees_feature_columns(train, hour)
    work_cols = list(dict.fromkeys(cols + [target_col, base_col]))
    work = train[work_cols].copy()
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target_col, base_col])
    if len(work) > 240_000:
        work = work.sample(240_000, random_state=171 + hour)
    y = work[target_col].astype(float).to_numpy() - work[base_col].astype(float).to_numpy()
    X = work[cols].apply(pd.to_numeric, errors="coerce").fillna(work[cols].median(numeric_only=True)).astype(np.float32)
    model = ExtraTreesRegressor(
        n_estimators=180,
        max_depth=14,
        min_samples_leaf=120,
        max_features=0.70,
        bootstrap=True,
        random_state=1710 + hour,
        n_jobs=-1,
    )
    model.fit(X, y)
    diagnostics = {
        "hour": int(hour),
        "rows": int(len(work)),
        "features": cols,
        "residual_mean": float(np.mean(y)),
        "residual_std": float(np.std(y)),
    }
    return model, cols, diagnostics


def build_v171(base: pd.DataFrame) -> CandidateResult:
    version = "v171"
    description = "ExtraTrees residual center overlay for ECS surface d1 10m; interval widths preserved."
    out = base.copy()
    train = load_features("east_china_sea").copy()
    train["latitude"] = train["latitude"].astype(float).round(2)
    train["longitude"] = train["longitude"].astype(float).round(2)

    inference_frames = []
    for window in range(1, 9):
        inf = load_inference_features(window, "east_china_sea").copy()
        inf["window"] = window
        inf["latitude"] = inf["latitude"].astype(float).round(2)
        inf["longitude"] = inf["longitude"].astype(float).round(2)
        inference_frames.append(inf)
    inference = pd.concat(inference_frames, ignore_index=True)

    pred_rows = []
    model_diagnostics = []
    for hour in HOURS:
        model, cols, diag = fit_extra_trees_hour(train, int(hour))
        X = inference[cols].apply(pd.to_numeric, errors="coerce")
        med = train[cols].median(numeric_only=True)
        X = X.fillna(med).astype(np.float32)
        residual = model.predict(X)
        shift = np.clip(0.20 * residual, -0.08, 0.08)
        rows = inference[["window", "latitude", "longitude"]].copy()
        rows["hour"] = int(hour)
        rows["shift"] = shift
        pred_rows.append(rows)
        diag["mean_shift"] = float(np.mean(shift))
        diag["p05_shift"] = float(np.quantile(shift, 0.05))
        diag["p95_shift"] = float(np.quantile(shift, 0.95))
        model_diagnostics.append(diag)

    shifts = pd.concat(pred_rows, ignore_index=True)
    target = (
        out["type"].eq("grid")
        & out["region"].eq("east_china_sea")
        & out["horizon"].astype(int).eq(1)
        & normalized_level(out).eq("10m")
    )
    current = out.loc[target, ["window", "latitude", "longitude", "hour"]].copy()
    current["latitude"] = current["latitude"].astype(float).round(2)
    current["longitude"] = current["longitude"].astype(float).round(2)
    merged = current.reset_index().merge(shifts, on=["window", "latitude", "longitude", "hour"], how="inner")
    if len(merged) != int(target.sum()):
        raise RuntimeError(f"v171 merge mismatch: {len(merged)} merged vs {int(target.sum())} target")
    idx = merged["index"].to_numpy(int)
    shift = merged["shift"].to_numpy(float)
    for col in Q_COLS:
        out.loc[idx, col] = out.loc[idx, col].astype(float).to_numpy() + shift
    repair_quantiles(out, target)

    allowed_q = target
    allowed_dir = pd.Series(False, index=out.index)
    diagnostics = {
        "scope": "grid/east_china_sea/surface_10m/d1/speed",
        "model": "ExtraTreesRegressor residual against fcst_speed_d1_h{hour}",
        "blend": 0.20,
        "shift_clip": [-0.08, 0.08],
        "target_rows": int(target.sum()),
        "model_diagnostics": model_diagnostics,
    }
    return save_candidate(base, out, version, description, allowed_q, allowed_dir, diagnostics)


def build_v172(base: pd.DataFrame, donor_v157: pd.DataFrame) -> CandidateResult:
    version = "v172"
    description = "NS station d14 weighted-conformal width rebase from v157 onto v164; centers frozen."
    target = station_mask(base, "north_sea", 14)
    assert_same_keys(base, donor_v157, target, donor_name="v157")
    out = base.copy()
    out.loc[target, ["dir_05", "dir_95"]] = donor_v157.loc[target, ["dir_05", "dir_95"]].to_numpy()
    moved_centers = int(out.loc[target, "dir_50"].round(9).ne(base.loc[target, "dir_50"].round(9)).sum())
    if moved_centers:
        raise RuntimeError(f"v172 center moved: {moved_centers}")
    allowed_q = pd.Series(False, index=out.index)
    allowed_dir = target
    old_hw = ((base.loc[target, "dir_95"].astype(float) - base.loc[target, "dir_05"].astype(float)) % 360.0) / 2.0
    new_hw = ((out.loc[target, "dir_95"].astype(float) - out.loc[target, "dir_05"].astype(float)) % 360.0) / 2.0
    diagnostics = {
        "donor_version": "v157",
        "scope": "station/north_sea/d14/direction_width_only",
        "target_rows": int(target.sum()),
        "dir50_changed_rows": moved_centers,
        "mean_halfwidth_delta_vs_base": float((new_hw - old_hw).mean()),
    }
    return save_candidate(base, out, version, description, allowed_q, allowed_dir, diagnostics)


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("v167-v172 breakthrough candidate batch")
    print("=" * 72)
    print(f"Base: {VERSION_BASE}")

    base = load_predictions(VERSION_BASE)
    anchor_v53 = load_predictions("v53")
    donor_v55 = load_predictions("v55")
    donor_v157 = load_predictions("v157")

    results = []
    builders = [
        ("v167", lambda: build_v167(base, anchor_v53, donor_v55)),
        ("v168", lambda: build_v168(base)),
        ("v169", lambda: build_v169_or_v170(base, version="v169", group="surface")),
        ("v170", lambda: build_v169_or_v170(base, version="v170", group="pressure")),
        ("v171", lambda: build_v171(base)),
        ("v172", lambda: build_v172(base, donor_v157)),
    ]
    for name, builder in builders:
        print(f"\nBuilding {name}...")
        result = builder()
        results.append(result.__dict__)
        print(
            f"  {name}: changed={result.changed_rows:,}, "
            f"speed={result.speed_changed_rows:,}, dir={result.direction_changed_rows:,}"
        )

    summary = {
        "base_version": VERSION_BASE,
        "built": results,
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    write_json(OUT_DIR / "batch_manifest.json", summary)
    pd.DataFrame(results).to_csv(OUT_DIR / "batch_summary.csv", index=False)
    print("\nBuilt candidates:")
    print(pd.DataFrame(results)[["version", "changed_rows", "speed_changed_rows", "direction_changed_rows", "zip_path"]].to_string(index=False))
    print(f"\nElapsed: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
