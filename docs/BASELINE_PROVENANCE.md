# Baseline Provenance Registry

> **Living document.** Last updated: 2026-05-03 after v97 rejection.
>
> This file tracks the *source* of every dimension's predictions in the current
> best submission (v88). Its purpose is to prevent the recurring failure mode:
> **training a residual model on one baseline and applying it to a different
> baseline without knowing they differ.**

---

## The Recurring Failure Mode

We have burned submissions (v40, v43, v95, v97) on the same root cause:
**training a correction model against baseline X, then applying it to a
submission whose target dimension uses baseline Y.**

The v88 submission is a **franken-submission**: 36 dimensions, each from a
different lineage. Some use the heavy baseline, some use Track I residuals,
some use copula-adjusted intervals, some use MOS overlays, some use empirical
Bayes calibration. If you train a model on the raw HRES forecast (`dir_d7_h0`)
and apply it to a dimension that uses the heavy baseline, the correction is
computed against the wrong distribution and will likely harm the submission.

**Rule:** Before training ANY residual model for a dimension, you MUST know
what baseline the current best submission uses for that dimension.

---

## v88 Dimension-by-Dimension Provenance

Carefully traced from `EXPERIMENT_LOG.md`. Each dimension's lineage is
reconstructed by reading the "What was done" and "Scope verification" sections
of every submission from v27 to v88.

### North Sea

| Dimension | Source in v88 | Introduced by | Notes |
|-----------|---------------|---------------|-------|
| speed_surface_d1_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_surface_d7_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_surface_d14_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_pressure_d1_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_pressure_d7_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_pressure_d14_ns | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| dir_surface_d1_ns | **v46 copula** on v8 base | v46 | Speed-direction coupling; intervals adjusted by predicted speed |
| dir_surface_d7_ns | **v46 copula** on v28 heavy | v46 | Copula applied on top of heavy-baseline direction |
| dir_surface_d14_ns | **v16 baseline revert** | v16 | Reverted v8 per-horizon model back to baseline-light |
| dir_pressure_d1_ns | **v46 copula** on v8 base | v46 | Speed-direction coupling |
| dir_pressure_d7_ns | **v46 copula** on v8 base | v46 | Speed-direction coupling |
| dir_pressure_d14_ns | **v16 baseline revert** | v16 | Reverted v8 per-horizon model back to baseline-light |
| speed_stations_d1_ns | **v88 center MOS + EB** | v88 | LightGBM residual MOS (blend 0.80) + empirical-Bayes interval calibration |
| speed_stations_d7_ns | **heavy baseline** | v28/v31 | v30 MOS was reverted in v31; back to heavy |
| speed_stations_d14_ns | **heavy baseline** | v28/v31 | Never changed since v27/v31 heavy graft |
| dir_stations_d1_ns | **v35 donor** (from v32) | v35 | Cherry-picked the one working cell from v32's broad direction correction |
| dir_stations_d7_ns | **heavy baseline** | v28 | Heavy baseline cherry-pick; **FROZEN after v97** |
| dir_stations_d14_ns | **heavy baseline** | v31 | Never changed since v31 |

### East China Sea

| Dimension | Source in v88 | Introduced by | Notes |
|-----------|---------------|---------------|-------|
| speed_surface_d1_ecs | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_surface_d7_ecs | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_surface_d14_ecs | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_pressure_d1_ecs | **heavy baseline** | v27 | Grafted from `predictions_heavy.csv` |
| speed_pressure_d7_ecs | **v53 LightGBM** | v53 | Pressure-shear / ws³ features; replaces heavy baseline |
| speed_pressure_d14_ecs | **v56/v57 blend** | v56/v57 | 20% v55 overlay + lambda 0.35 on 850/925 levels |
| dir_surface_d1_ecs | **v46 copula** on v8 base | v46 | Speed-direction coupling |
| dir_surface_d7_ecs | **v46 copula** on v8 base | v46 | Speed-direction coupling |
| dir_surface_d14_ecs | **v85 u/v residual overlay** | v85 | Centre-only lambda 0.10 on top of v59 d10-HRES proxy |
| dir_pressure_d1_ecs | **v46 copula** on v8 base | v46 | Speed-direction coupling |
| dir_pressure_d7_ecs | **v51 v47 damped copula** | v51 | v47's per-horizon damping on ECS pressure d7/d14 |
| dir_pressure_d14_ecs | **v51 v47 damped copula** | v51 | v47's per-horizon damping on ECS pressure d7/d14 |
| speed_stations_d1_ecs | **v86 EB interval cal** | v86 | Preserves v85 q50; q05/q95 from shrunk station residual quantiles |
| speed_stations_d7_ecs | **heavy baseline** | v28/v31 | v30 MOS reverted in v31 |
| speed_stations_d14_ecs | **heavy baseline** | v28/v31 | Never changed since v31 |
| dir_stations_d1_ecs | **v39 Track I** | v39 | Residual sin/cos model on feature baseline |
| dir_stations_d7_ecs | **v41 gated Track I** | v41 | Residual sin/cos with center_shift <= 20° gate |
| dir_stations_d14_ecs | **heavy baseline** | v31 | **FROZEN after v43** |

---

## What This Means for Residual Models

### Safe to train on feature-baseline residuals

These dimensions use the raw HRES forecast (or something very close to it) as
their center prediction. Training residual models on the feature baseline is
safe because the training and submission baselines are the same:

| Dimension | Why it's safe |
|-----------|---------------|
| ALL grid speed | Heavy baseline speed ≈ HRES forecast speed (mean_diff < 1 m/s) |
| ALL station speed d7/d14 | Heavy baseline speed ≈ HRES forecast speed |
| dir_surface_d14_ns | v16 baseline revert = original HRES-like baseline |
| dir_pressure_d14_ns | v16 baseline revert = original HRES-like baseline |

### DANGEROUS to train on feature-baseline residuals

These dimensions use a baseline that is NOT the raw HRES forecast. Training on
feature residuals and applying to v88 is HIGH RISK:

| Dimension | Actual baseline in v88 | Risk |
|-----------|------------------------|------|
| dir_stations_d7_ns | **heavy baseline** (v28) | v97 proved even gated 15° corrections fail |
| dir_stations_d14_ecs | **heavy baseline** (v31) | v43 proved even 15° gated shifts regress +49 cWS |
| dir_surface_d7_ns | **v46 copula on heavy** | Copula already applied; feature residual is wrong proxy |
| dir_surface_d14_ecs | **v85 u/v overlay on d10-HRES** | Three layers deep; feature residual is meaningless |
| dir_pressure_d7_ecs | **v51 damped copula** | Already copula-adjusted; feature residual is wrong |
| dir_stations_d1_ns | **v35 donor** (from v32) | Donor-mined direction; not feature-baseline |
| dir_stations_d1_ecs | **v39 Track I** | Track I residual on feature baseline; already corrected |
| dir_stations_d7_ecs | **v41 gated Track I** | Track I residual on feature baseline; already corrected |

### Special case: d14 has no HRES forecast

The inference feature files only contain d1, d7, and d10 forecasts. There is no
d14 HRES forecast for the 2022 windows. Any d14 model must use persistence,
climatology, or a derived proxy (like v59's d10-HRES). Training on `dir_d14_h0`
from the training features and applying to inference is training on a forecast
that does not exist at inference time.

**This is why v59 uses `fcst_dir_d10_h*` as the d14 centre proxy.**

---

## Frozen Dimensions

These dimensions have failed correction attempts and should not be touched:

| Dimension | Failed Attempts | Date Frozen | Why frozen |
|-----------|-----------------|-------------|------------|
| dir_stations_d14_ecs | v40, v43 | 2026-04-27 | Even 30 rows with shift <= 15° regressed +49 cWS |
| dir_stations_d7_ns | v97 | 2026-05-03 | 15° gate regressed +61 cWS; feature baseline ≠ heavy baseline |

---

## The v97 Failure Explained

v97 attempted to apply Track I to `dir_stations_d7_ns`. The local evaluation
looked great (all splits improved with 15° gate). But the leaderboard regressed
+61 cWS.

**Root cause:** v88's `dir_stations_d7_ns` uses the **heavy baseline** (v28
cherry-pick). The Track I model was trained on residuals against the **feature
baseline** (`dir_d7_h0` from `train_north_sea.parquet`). These are two
completely different forecasts. The model learned to correct the feature
baseline toward observations. When applied to the heavy baseline, the
"corrections" systematically moved the center away from the true 2022
observations.

The 15° gate did not save v97 because the **small shifts** that passed the gate
were still computed relative to the wrong baseline. A shift of 10° from the
feature baseline is not the same as a shift of 10° from the heavy baseline.

**Lesson:** Gating on shift magnitude only works when the training and
submission baselines are the same distribution. When they differ, the gate
accepts rows that are "small shifts" in feature-baseline space but "harmful
shifts" in submission-baseline space.

---

## Pre-Submission Checklist

Before building ANY submission that trains on residuals or applies a
model-based correction:

1. **Look up the dimension in the provenance table above.**
   - If it says "heavy baseline" or "Track I" or "copula" or "MOS", the
     dimension already uses a non-feature baseline. Do not train on feature
     residuals.

2. **Is the dimension frozen?**
   - If yes, STOP. Do not waste a submission slot.

3. **Does the dimension use the feature baseline?**
   - Only these are safe for feature-residual training:
     - All grid speed
     - All station speed d7/d14
     - `dir_surface_d14_ns` and `dir_pressure_d14_ns` (v16 reverted baseline)
   - Everything else is HIGH RISK.

4. **For d14 dimensions, remember there is no HRES d14 forecast in inference.**
   - Any d14 correction must be built on d10, d7, or d1 proxies, not `dir_d14_h0`.

5. **If you must try a high-risk dimension, use a gate + small scope.**
   - Change only the target dimension.
   - Gate on center_shift relative to the ACTUAL submission baseline (not the
     feature baseline).
   - Accept only rows where the shift is very small (<= 10°) and the local
     validation improves on ALL splits with margin.

---

## How to Verify Baseline Match

```bash
source .venv/bin/activate

# Compare submission predictions to the feature baseline
python -m src.experiments.baseline_provenance \
  --submission starting-kit/phase_1/predictions_v88.csv \
  --mismatches-only
```

The analyzer computes per-dimension mean/max differences between v88 and the
inference feature baseline (`fcst_dir_d*` / `fcst_speed_d*`). Large differences
mean the dimension uses a non-feature baseline.

**Important:** The analyzer compares to `fcst_dir_d*` (inference features), not
`dir_d*` (training features). The training and inference forecast columns are
different forecasts. Always use inference features as the reference when
checking baseline match for submission purposes.
