# PIPELINE — full from-scratch reproduction

This document traces the **complete** path from the raw competition dataset to the
third-place submission, and tells you exactly which parts you can re-run, how, and to
what fidelity. Read [`METHODOLOGY.md`](METHODOLOGY.md) first for *why* the pipeline looks
the way it does; this file is the *how*.

This document plus [`../CHECKSUMS.md`](../CHECKSUMS.md) and the verbatim build scripts under
[`../pipeline/`](../pipeline/) are the build trace: the DAG, every artifact's `sha256`, and
the exact, runnable transforms. (A full version-by-version development logbook exists but is
kept private — it contains live competition-operations data; it can be shared on request.)

---

## 0. The shape of the result

The submission is a single `predictions.csv` (3,448,800 rows) covering **36 scored cells**
= 2 regions × 3 sources × 3 horizons × 2 variables. The whole campaign keeps the **center
prediction frozen** (`q50` / `dir_50` from a strong base) and only re-calibrates the
**interval width** (`[q05,q95]` / `[dir_05,dir_95]`), one cell at a time, reading the hidden
leaderboard to keep what helped. The final file is therefore the base predictions with a
handful of disjoint, center-frozen width overlays grafted on.

See [`../CHECKSUMS.md`](../CHECKSUMS.md) for the exact DAG and every artifact's `sha256`.

---

## 1. Get the raw data (≈ 21 GB)

Nothing in this repo is the competition data — you download it from the official sources
(it is the competition's data, under its own license; see [`../NOTICE.md`](../NOTICE.md)).

- **Competition:** Codabench #13821 — <https://www.codabench.org/competitions/13821/>
- **Starting kit (code):** <https://github.com/DavidMedernach/Hackathon-Sea-Winds-Predictions>
- **Dataset:** `phase1_dataset.zip` from Zenodo — <https://zenodo.org/records/19538994>

Unzip to `data/phase1_dataset/` so you have `train/`, `inference/window_{1..8}/`, and
`scoring/`. The `train/` parquets are the 2019–2021 reanalysis "truth" + HRES forecasts +
station observations; `inference/window_{1..8}/` are the hidden-2022 test inputs.

---

## 2. Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt           # pandas / numpy / pyarrow are enough for Tier 1
# For the heavy base + deep lineage (Tiers 3–4) you also need the starting-kit stack:
# lightgbm>=4.3, catboost>=1.2, scikit-learn>=1.4, xgboost, xarray, netcdf4  (see starting-kit/requirements.txt)
```

The author's working interpreter was **Python 3.12.4**. The overlay tiers (1–2) need only
`numpy` + `pandas`. The model tiers (3–4) need CatBoost/LightGBM and are **library-version
sensitive** — see the determinism note in §7.

---

## 3. The four tiers of reproduction

Reproduction is layered. Each tier is independently runnable if you have its inputs. From
the cheapest/most-exact to the deepest:

| Tier | What it produces | Inputs needed | Fidelity here |
|---|---|---|---|
| **0. Verify** | confirm you hold the exact artifact | the Release `.zip` | byte-exact (`sha256`) |
| **1. Final overlays** | production base → FINAL_BEST | a base CSV (+ raw for one hop) | numerically identical / byte-exact |
| **2. Floor chain** | production base → BEST_FLOOR | production base + raw | deterministic |
| **3. Production base** | heavy root → production base | heavy root + 21 GB + models | deterministic, version-sensitive |
| **4. Heavy root** | raw → `predictions_heavy.csv` | raw + features | deterministic, version-sensitive |

A full cold rebuild runs 4 → 3 → 2 → 1; verification (0) and the final hop (1) are what you
can confirm *today* without the 21 GB download.

---

## Tier 0 — verify the artifact (byte-exact)

Download `submission_FINAL_BEST.zip` from the GitHub Release, then:

```bash
python verify_artifact.py submission_FINAL_BEST.zip
# file   : submission_FINAL_BEST.zip
# sha256 : 0d8c48ac…b7cd7
# inner  : predictions.csv  (3,448,800 data rows, expected 3,448,800: True)
# PASS   : matches pinned 'submission_FINAL_BEST.zip'.
```

A PASS proves you hold the exact bytes of the third-place submission.

---

## Tier 1 — production base → FINAL_BEST (the verified final overlays)

These hops are pure, deterministic post-processing. Given the base CSV of each hop, they
reproduce the next artifact exactly (one hop also reads the raw ECS train parquet for a
climatological arc). Order and effect:

```
predictions_v256_…csv
  └─ build_dir_shrink.py 0.12          → predictions_dirshrink_combined.csv   (sha 8b4347ec…)
       center-frozen arc shrink to 12% on 4 disjoint direction cells:
       Dir NS Pres d7, Dir NS Surf d7, Dir ECS Surf d7, Dir NS Sta d14
  └─ build_ecs_d14_reposition.py       → predictions_ecs_d14_reposition.csv   (sha 0cbdf30e…)
       replace Dir ECS Surf d14 arcs with climatological 90% arcs  (needs raw ECS train parquet)
  └─ build_speed_shrink.py 0.08        → predictions_speedshrink_s08.csv      (sha d95e4dd5…) ≡ BEST_FLOOR
       center-frozen speed shrink on q05/q95 of ECS Sta d14 + ECS Surf d14
  └─ build_final_best.py               → predictions_FINAL_BEST.csv           (sha 5eed32b3…) ← FINAL SUBMISSION (public #3)
       center-frozen arc shrink on Dir NS Pres d7 only, 12% → 20%
```

The last hop is provided as a standalone, runnable builder + verifier. If you have the
BEST_FLOOR base (`predictions_speedshrink_s08.csv` — regenerate it via the hop above, or it
is the inner CSV of `submission_BEST_FLOOR.zip`, sha `17bde403…`):

```bash
python reproduce_final_best.py \
    --floor predictions_speedshrink_s08.csv \
    --canonical submission_FINAL_BEST.zip
# VERDICT: NUMERICALLY IDENTICAL
#   center-frozen (q50 & dir_50 unchanged): True
#   max |Δ| over ALL columns (parsed): 0.000e+00
```

### Why the final hop is "numerically identical" and not "byte-identical"

The canonical file computed Dir NS Pres d7 as a **one-step 20% shrink of the *unshrunk*
upstream base (v256)**, then grafted it onto the floor. Re-deriving the same cell from the
on-disk **12%-shrunk** floor is a mathematically-equal but differently-ordered float
multiply: in memory the two differ by at most ~2.8e-14° (1 ULP). When written to CSV and
parsed back, **every value rounds to the same float64** as the canonical file (e.g.
`245.88000000000002` and `245.88` parse to the same double), so a scorer sees identical
predictions → identical Winkler scores and identical ranks. Only the raw file bytes (and
thus the `sha256`) differ, in cosmetic decimal formatting on the changed cell.

To regenerate the canonical `sha256` exactly, run the full chain from the heavy base so the
unshrunk v256 arc carries its exact float values into this hop (Tiers 2–4).

> **Note on the originals.** The scripts under `pipeline/overlays/` are the project's
> original builders, kept verbatim for traceability; they read/write `predictions_*.csv`
> from a working `submissions/` directory and hardcode each hop's base. `build_final_best.py`
> and the top-level `reproduce_final_best.py` / `verify_artifact.py` are the parameterized,
> path-agnostic entry points written for this reproduction.

---

## Tier 2 — production base → BEST_FLOOR

This is Tier 1 minus the last hop, starting one step earlier:

1. `build_final_day_station_ladder.py` — production base → `v256` (Dir NS Sta d1 0.60 shrink
   + a WS ECS Surf d1 speed donor). Deterministic.
2. `build_dir_shrink.py 0.12` → `dirshrink_combined`.
3. `build_ecs_d14_reposition.py` → `ecs_d14_reposition` (needs raw ECS train parquet).
4. `build_speed_shrink.py 0.08` → `speedshrink_s08` ≡ BEST_FLOOR.

The exact cells, fractions, and rationale for each are in the script docstrings (and in
[`../CHECKSUMS.md`](../CHECKSUMS.md) for the per-hop checksums).

---

## Tier 3 — heavy root → production base (deep lineage)

The production base `submission_v222_plus_v227_plus_v232.zip` (sha `13c9fa05…`) is the end
of a long, disjoint, center-frozen overlay lineage (≈ v26 → v51 → … → v196 → v222 → v227 →
v232) built on the heavy root. It is regenerated by:

```bash
python pipeline/lineage/reproduce_v222_plus_v227_plus_v232.py        # verify-only: re-hashes the stored base
```

The production base is **sha-pinned** (`13c9fa05…`). Its deep per-version lineage modules
(the ~200 exploration scripts in the original project's `src/experiments/`) embed live
competitor leaderboard snapshots and are therefore **not redistributed in this clean public
package**; the lineage entry point above is included for reference. Each overlay in the
lineage is a single-cell, center-frozen width change, recorded with its checksum in
[`../CHECKSUMS.md`](../CHECKSUMS.md). A full cold re-run from raw needs the 21 GB
dataset and the heavy models and is **library-version sensitive** (see §7); this is why the
production base and the final artifact are sha-pinned rather than assumed byte-reproducible
from a fresh environment.

The dimension-by-dimension provenance of the base — which lineage each of the 36 cells comes
from, and the costly "trained on the wrong baseline" failures that shaped the rules — is in
[`BASELINE_PROVENANCE.md`](BASELINE_PROVENANCE.md).

---

## Tier 4 — raw → heavy root (`predictions_heavy.csv`)

The frozen-center root is the "heavy notebook": a kitchen-sink base that trains, per region,
**CatBoost quantile speed models** (7 levels × 12 targets × 3 quantiles, `iterations=500,
depth=7, lr=0.05, l2=3, random_seed=42`, early-stopping on 2021) and **LightGBM sin/cos
direction models** (10m, applied to all levels with climatological offsets), then writes
`q05/q50/q95` + `dir_05/dir_50/dir_95` for all 8 inference windows.

- Notebook: `pipeline/heavy/2d_starting_kit_heavy.ipynb`
- Plain-Python extraction: `pipeline/heavy/_heavy_extracted.py`
  (per-region variants: `heavy_extracted_ns_only.py`, `heavy_extracted_ecs_only.py`)

It first needs the engineered features (`features/`), produced from the raw parquets by the
starting kit's `1_feature_engineering.ipynb`. Seeds are fixed (`random_seed=42`,
`RandomState(42)`), so it is deterministic **given identical feature parquets and identical
library versions** — see §7.

---

## 4. Scoring (optional, to confirm the result locally)

The competition metric is the (circular) Winkler score per cell, ranked across teams, then
averaged. A faithful local implementation is in `src/scoring/` (`winkler.py`, `evaluate.py`).
Because the per-cell *ranks* depend on every competitor's submission, you can reproduce the
per-cell **scores** locally but not the public *ranks* (those need the live board).

---

## 5. The 36-cell map

`region × source × horizon × variable`:

- regions: `north_sea`, `east_china_sea`
- sources: stations / surface grid (`level ∈ {10m,100m}`) / pressure grid (other levels)
- horizons: `1`, `7`, `14` days
- variables: speed (`q05,q50,q95`) and direction (`dir_05,dir_50,dir_95`)

The final submission only ever moved interval **widths** on a small set of these cells; the
centers are the heavy-root predictions throughout.

---

## 6. The exact final-overlay cells (what makes FINAL_BEST ≠ production base)

| Cell | Overlay | Effect |
|---|---|---|
| Dir NS Sta d1 | `build_final_day_station_ladder.py` | arc shrink 0.60 |
| WS ECS Surf d1 | `build_final_day_station_ladder.py` | speed donor |
| Dir NS Pres d7 | `build_dir_shrink.py` then `build_final_best.py` | arc shrink → **20%** |
| Dir NS Surf d7 | `build_dir_shrink.py 0.12` | arc shrink 0.12 |
| Dir ECS Surf d7 | `build_dir_shrink.py 0.12` | arc shrink 0.12 |
| Dir NS Sta d14 | `build_dir_shrink.py 0.12` | arc shrink 0.12 |
| Dir ECS Surf d14 | `build_ecs_d14_reposition.py` | climatological arcs |
| WS ECS Sta d14 | `build_speed_shrink.py 0.08` | speed shrink 0.08 |
| WS ECS Surf d14 | `build_speed_shrink.py 0.08` | speed shrink 0.08 |

All are disjoint and center-frozen; every other cell of FINAL_BEST is byte-identical to the
production base.

---

## 7. Determinism & honest limits

- **Tiers 0–1 are exact today.** Verification is byte-exact; the final overlay hop is
  numerically identical (and the speed-shrink hop is byte-exact) — both verified in this
  repo against the on-disk floor.
- **Tiers 2–4 are deterministic but version-sensitive.** The CatBoost/LightGBM training
  uses fixed seeds, but loosely-pinned model libraries mean a fresh `pip install` may not
  reproduce `predictions_heavy.csv` bit-for-bit; a 1-ULP drift at the root propagates to a
  different `sha256` at the end (though the *scores* track). This is why the canonical
  artifact is **sha-pinned and shipped** (Tier 0) rather than assumed reproducible to the
  byte from a cold environment.
- **Feature engineering is a prerequisite** of Tier 4 and was not re-audited for determinism
  here.
- **Ranks need the board.** Local scoring gives per-cell scores; the leaderboard ranks that
  (and the final standings) come from the live competition.

If your goal is "prove this is the submission" → Tier 0. If it is "rebuild the final
result from a base" → Tier 1. If it is "cold rebuild from raw" → Tiers 4→1, accepting the
version-sensitivity above, using this document and `CHECKSUMS.md` as the step-by-step trace.
