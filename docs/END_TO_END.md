# End-to-end run — `reproduce_from_raw.py`

A single orchestrator drives the **whole DAG**, raw dataset → `FINAL_BEST`, with a
checksum gate after every hop. This document is the full walkthrough: the stages, the
two run modes, the exact commands and their output, and the honest limits.

> **TL;DR.** Point it at a working tree and verify every hop:
> ```bash
> python reproduce_from_raw.py --root /path/to/working-tree --mode verify
> ```

---

## The 9 stages

| # | Stage | Producer | Output (gate) | Kind |
|--:|---|---|---|---|
| 1 | Feature engineering | starting-kit `1_feature_engineering.ipynb` | `data/phase1_dataset/features/…` | **external** |
| 2 | Heavy-notebook base | `scripts/heavy/heavy_extracted_{ns,ecs}_only.py` | `predictions_heavy.csv` (`dcc3ba48…`) | **checkpoint** (version-sensitive) |
| 3 | Early lineage → v51 | **`scripts/rebuild_v51.py`** (19 ordered hops, 8 train models) | `predictions_v51.csv` (`c7e392af…`) | **checkpoint** (rebuildable, version-sensitive) |
| 4 | Production base | `scripts/reproduce_v222_plus_v227_plus_v232.py` | `…v222_plus_v227_plus_v232` (`5d5c1ba9…`) | lineage (deterministic) |
| 5 | Final-day station ladder → v256 | `scripts/build_final_day_station_ladder.py` | `predictions_v256_…csv` | overlay |
| 6 | Direction shrink 0.12 | `scripts/build_dir_shrink.py combined` | `predictions_dirshrink_combined.csv` (`8b4347ec…`) | overlay |
| 7 | ECS d14 reposition | `scripts/build_ecs_d14_reposition.py` | `predictions_ecs_d14_reposition.csv` (`0cbdf30e…`) | overlay (reads raw) |
| 8 | Speed shrink 0.08 → BEST_FLOOR | `scripts/build_speed_shrink.py 0.08` | `predictions_speedshrink_s08.csv` (`d95e4dd5…`) | overlay |
| 9 | Final single-cell push | `scripts/build_final_best.py` | `predictions_FINAL_BEST.csv` (`5eed32b3…`) | final (numerically identical) |

Stages 4–9 are **deterministic post-processing**. Stages 2–3 train ML models (seeded
but library-version-sensitive). Stage 1 is the external starting-kit step.

---

## The working tree

The orchestrator runs against a `--root` that has the original layout. This repository
supplies the **code** (`scripts/`, `src/`); you supply the **data** and the cached
checkpoints:

```
<root>/
├── scripts/                     ← from this repo (lineage + overlay builders + heavy/)
├── src/                         ← from this repo (the engine the lineage imports)
├── data/phase1_dataset/         ← you download (raw train + inference + features)
├── starting-kit/phase_1/        ← heavy base + cached lineage checkpoints (heavy, v51, …)
└── submissions/                 ← prediction CSVs/zips are written here
```

Get the raw dataset from the official sources (see [`../NOTICE.md`](../NOTICE.md)):
Codabench #13821 · starting kit · Zenodo `phase1_dataset.zip`.

---

## Mode 1 — `verify` (default, non-destructive)

Locates each stage's output in the working tree and checks its `sha256`; for the final
hop it regenerates from the floor and numerically compares. No files are written.

```bash
python reproduce_from_raw.py --root /path/to/working-tree --mode verify
```

Example output against a complete working tree:

```
# Verifying the DAG against working tree: /path/to/working-tree

• [1/9] Feature engineering (raw -> features/)                   PRESENT         features present
✅ [2/9] Heavy-notebook base (features -> predictions_heavy.csv)  VERIFIED        sha256 dcc3ba48fd7b…
✅ [3/9] Early lineage (heavy -> v51)                             VERIFIED        sha256 c7e392afc179…
✅ [4/9] Production base (v51 -> v222_plus_v227_plus_v232)        VERIFIED        sha256 5d5c1ba9ab92…
· [5/9] Final-day station ladder (production base -> v256)       MISSING         (transient intermediate; not retained)
✅ [6/9] Direction shrink 0.12 (v256 -> dirshrink_combined)       VERIFIED        sha256 8b4347ec6141…
✅ [7/9] ECS d14 reposition (dirshrink_combined -> reposition)    VERIFIED        sha256 0cbdf30ee1e3…
✅ [8/9] Speed shrink 0.08 (reposition -> BEST_FLOOR)             VERIFIED        sha256 d95e4dd51a32…
✅ [9/9] Final single-cell push (BEST_FLOOR -> FINAL_BEST)        VERIFIED        canonical sha256 matches

verify complete.
```

`v256` is a transient intermediate that is not kept on disk, so it shows `MISSING` even on
a complete tree — that is expected and does not fail the run. Every artifact that *is*
retained verifies against its pinned `sha256`.

---

## Mode 2 — `run` (destructive: executes the producers)

Executes each stage's producer in order, writing intermediates into `<root>/submissions/`,
with a `sha256` gate after each hop. Requires the 21 GB raw dataset.

```bash
python reproduce_from_raw.py --root /path/to/working-tree --mode run
```

Behaviour:

- **Checkpoints (stages 2–3)** are treated as *cached* by default: if `predictions_heavy.csv`
  / `predictions_v51.csv` are present, their `sha256` is verified and they are **not**
  rebuilt. Pass `--rebuild-checkpoints` to rebuild them — **`v51` is rebuilt from raw by
  `scripts/rebuild_v51.py`** (see next section); `heavy` is regenerated from the starting-kit
  heavy notebook. Both train version-sensitive ML, so expect **score-equivalent, not
  byte-identical** output.
- **External (stage 1)** halts with guidance if the engineered features are absent.
- **Lineage + overlays (stages 4–9)** run their producers and are gated on the pinned
  `sha256`. The final hop is gated on numerical identity (max |Δ| = 0 after CSV round-trip;
  the byte-anchor sha is verified separately by `verify_artifact.py`).

A stage whose producer or inputs are missing prints `BLOCKED` with the exact prerequisite
and stops, so you always know what to provide next.

---

## Rebuilding `v51` from raw (stage 3)

`v51` is the lineage root. It is **fully rebuildable** from the engineered features + the two
base-notebook outputs by [`scripts/rebuild_v51.py`](../scripts/rebuild_v51.py), which runs the
exact **19-step ordered chain** (every producer is in `src/`; the three non-`__main__`
entrypoints — `generate_v40()`, `run_b1_experiment()` → v46, `run_v47()` → v47 — are invoked
explicitly):

```bash
python scripts/rebuild_v51.py --root /path/to/working-tree --plan   # print the 19 steps
python scripts/rebuild_v51.py --root /path/to/working-tree          # run the chain
python scripts/rebuild_v51.py --root /path/to/working-tree --start-at v32   # resume
```

The chain: `run_v7 → v8 → v16 → v19 → v26 → v27 (grafts heavy) → v28 → v30 → v31 (uses light)
→ v32 → v34 → v35 → v38 → v39 → generate_v40 → v41 → v46 → v47 → v51`. **8 of the 19 steps
train models** (`v7, v8, v19, v30, v32, v34, v39, v40` — LightGBM / CatBoost / sklearn,
seeded). `run_v7` must run first because `v32` loads the direction models it writes to
`logs/direction_models_v7/`.

**Prerequisites** (pre-existing inputs, not produced by the chain):
`data/phase1_dataset/` (features + reanalysis), `starting-kit/phase_1/predictions_heavy.csv`,
and `starting-kit/phase_1/predictions_light.csv` (both are starting-kit notebook outputs).

The orchestrator runs this automatically when you pass `--mode run --rebuild-checkpoints`.

### Deterministic rebuild with the frozen models (executed & verified)

The chain has been **run end-to-end** and its model artifacts **frozen and shipped**. To get
a **byte-deterministic** rebuild, download `seawinds_v51_frozen_models.tar.gz` from the
Release and extract it into `<root>/logs/` before running — every ML step then *loads* the
frozen models instead of retraining:

```bash
tar -xzf seawinds_v51_frozen_models.tar.gz -C /path/to/working-tree   # -> <root>/logs/...
python scripts/rebuild_v51.py --root /path/to/working-tree
# -> ✓ BYTE-IDENTICAL to the frozen-models reference v51' (4f14eb2e…)
```

Verified results from the actual run:
- The full `raw → v51` chain completed **all 19 steps** and produced `v51′`, sha
  **`4f14eb2e0c396316f31b778a6db6c69c87e641e856c3d8806258277d4d07ff1a`**.
- Re-running the two formerly-nondeterministic steps with the frozen caches reproduced them
  **byte-for-byte** (`v34`/Track E and `v39`/Track I both `MATCH=True`). All other steps are
  seeded, pure transforms, or load cached models — so the whole chain is now deterministic.
- `v51′ ≠ canonical v51` (`c7e392af…`): canonical `v51` is **not** byte-reproducible because
  Track E was trained **unseeded** and its original models were never saved. `v51′` is a
  fixed, deterministic, fully-from-raw reference lineage; the canonical winning artifact stays
  anchored by its pinned sha (`verify_artifact.py`).

---

## Honest limits (why "fully autonomous from only raw" is not achievable)

1. **Stage 1 is external.** Feature engineering is the official starting kit's notebook,
   not re-distributed here.
2. **Stages 2–3 are ML.** `v51` **is rebuildable from raw** via `scripts/rebuild_v51.py` and,
   **with the shipped frozen models, reproduces byte-identically** (`v51′` = `4f14eb2e…`).
   A *cold* rebuild (no frozen models, e.g. different CatBoost/LightGBM/sklearn versions, or
   re-training the unseeded Track E) is only **score-equivalent** — and the *canonical* `v51`
   (`c7e392af…`) / winning `FINAL_BEST` are not byte-reproducible at all, because the original
   Track E was unseeded and its models were never saved. The canonical artifact is the sha
   anchor; the frozen-models rebuild is the deterministic from-raw reference.
   The intermediate CSVs `v26…v50` are not retained, so the early lineage runs end-to-end
   (the script does exactly that).
3. **Therefore the byte-exact anchor is the sha-pinned artifact**, and the final
   transformation is what regenerates exactly. Everything from the production base onward
   (stages 4–9) is deterministic and gated to its `sha256`.

See [`PIPELINE.md`](PIPELINE.md) §7 for the full determinism discussion and
[`../CHECKSUMS.md`](../CHECKSUMS.md) for every hop's checksum.
