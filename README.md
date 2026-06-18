# seawinds-reproduce

Full traceability and reproduction of the **third-place submission** for the
**Sea Winds Predictions** competition (Codabench Phase 1, #13821):
`submission_FINAL_BEST.zip`.

This repository contains the code, the full build DAG, and runnable verification so that the
third-place artifact can be **confirmed byte-for-byte** and **regenerated from its inputs**, with
every hop from the raw dataset documented and checksum-anchored.

```
sha256(submission_FINAL_BEST.zip)        = 0d8c48ac…b7cd7
sha256(inner predictions.csv)            = 5eed32b3…05bc9      (3,448,800 rows)
```

> **Reproducing / adjudicating this submission?** Follow **[`REPRODUCE.md`](REPRODUCE.md)** —
> a short, ordered guide: (1) confirm the submitted file is the exact scored artifact,
> (2) regenerate it from its published base, (3) rebuild from the raw dataset.

---

## TL;DR — verify the submission in 30 seconds

```bash
# 1. install the lightweight deps (numpy + pandas + pyarrow)
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 2. download submission_FINAL_BEST.zip from this repo's GitHub Release, then:
python verify_artifact.py submission_FINAL_BEST.zip
#   PASS : matches pinned 'submission_FINAL_BEST.zip'.
```

A `PASS` proves you hold the exact bytes of the third-place submission.

To **regenerate** the result from its immediate base and confirm it is identical:

```bash
python reproduce_final_best.py \
    --floor predictions_speedshrink_s08.csv \
    --canonical submission_FINAL_BEST.zip
#   VERDICT: NUMERICALLY IDENTICAL   (max |Δ| over all columns = 0; center frozen)
```

---

## What the submission is

We forecast wind **speed** and **direction** for two seas (North Sea, East China Sea), at
three lead times (1 / 7 / 14 days), from three data sources (offshore stations, surface
grid, pressure-level grid). That is **36 scored "cells."** For each we submit an interval —
a low / middle / high estimate (`q05/q50/q95` for speed, `dir_05/dir_50/dir_95` for
direction). Each cell is scored by the (circular) **Winkler** rule, teams are ranked per
cell, and the headline metric is the **average of the 36 ranks**.

The whole approach: **start from strong base forecasts, freeze the center prediction
(`q50`/`dir_50`), and re-calibrate only the interval *width*, one cell at a time**, using the
hidden leaderboard to keep what helped. The final file is the base predictions with a
handful of disjoint, center-frozen width overlays grafted on. See
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full story (Winkler asymmetry, the von
Mises direction-width calibration, compounding, and the dead-ends).

The exact cells changed by each overlay, and the per-hop checksums, are in
[`CHECKSUMS.md`](CHECKSUMS.md) and [`docs/PIPELINE.md`](docs/PIPELINE.md).

---

## Repository layout

```
seawinds-reproduce/
├── README.md                      ← you are here
├── REPRODUCE.md                   ← organiser guide (verify / regenerate / rebuild)
├── reproduce_from_raw.py          ← end-to-end orchestrator: drives the whole DAG with a checksum gate per hop
├── reproduce_final_best.py        ← regenerate FINAL_BEST from the floor + verify (numerical identity)
├── verify_artifact.py             ← verify any submission against the pinned sha256 registry
├── CHECKSUMS.md                   ← every artifact's sha256 + the verified build DAG
├── requirements.txt
├── docs/
│   ├── METHODOLOGY.md             ← plain-English overview of the method (with diagrams)
│   ├── PIPELINE.md                ← the full from-scratch procedure, tier by tier
│   ├── END_TO_END.md              ← the single end-to-end run (reproduce_from_raw.py) walkthrough
│   └── BASELINE_PROVENANCE.md     ← which lineage each of the 36 cells comes from
├── scripts/                       ← the runnable pipeline
│   ├── heavy/                     ← raw → heavy-notebook base (frozen center)
│   ├── rebuild_v51.py             ← raw + heavy + light → v51 (the 19-step early lineage)
│   ├── reproduce_v222_plus_v227_plus_v232.py   ← v51 → production base (deep-lineage driver)
│   └── build_*.py                 ← production base → v256 → … → FINAL_BEST (overlay builders)
└── src/                           ← the engine the lineage imports (experiments, pipeline, models, scoring)
```

The big artifacts (the 134 MB `.zip`, the ~419 MB CSVs, and the 21 GB raw dataset) are **not**
in the git tree — they exceed GitHub's file limit and the raw data is the competition's own
(licensed) dataset. The final submission `.zip` **and its base** (`submission_BEST_FLOOR.zip`)
are attached to the **GitHub Release** (both are the author's own prediction outputs); the raw
data is downloaded from the official sources (see below).

---

## Reproduction, in four tiers

Full detail in [`docs/PIPELINE.md`](docs/PIPELINE.md). Summary:

| Tier | Produces | Inputs | Fidelity |
|---|---|---|---|
| **0. Verify** | confirm the exact artifact | the Release `.zip` | **byte-exact** (`sha256`) ✅ |
| **1. Final overlays** | base → FINAL_BEST | a base CSV (+ raw for 1 hop) | **numerically identical** / byte-exact ✅ |
| **2. Floor chain** | production base → floor | production base + raw | deterministic |
| **3. Production base** | heavy root → production base | + 21 GB raw + models | deterministic, version-sensitive |
| **4. Heavy root** | raw → heavy base | raw + features | deterministic, version-sensitive |

Tiers 0 and 1 are verified **in this repo** against the real artifact (numerically identical
final hop; byte-exact speed-shrink hop). Tiers 2–4 are fully scripted and traced in
[`docs/PIPELINE.md`](docs/PIPELINE.md); a cold rebuild from raw is deterministic but
**library-version sensitive** (a 1-ULP
drift at the CatBoost/LightGBM root changes the final `sha256` though not the scores) — which
is exactly why the canonical artifact is sha-pinned and shipped rather than assumed
byte-reproducible from a fresh environment.

---

## Run the whole pipeline with one command

[`reproduce_from_raw.py`](reproduce_from_raw.py) is a single orchestrator that encodes
**every** stage of the DAG (raw → features → heavy → v51 → production base → overlays →
`FINAL_BEST`) and applies a `sha256` gate after each hop. Point it at a working tree that
has the code (this repo) plus the raw data:

```bash
# non-destructive: locate each stage's output and check its checksum
python reproduce_from_raw.py --root /path/to/working-tree --mode verify

# destructive: actually execute each producer in order, with a checksum gate per hop
python reproduce_from_raw.py --root /path/to/working-tree --mode run
```

`verify` against a complete tree reports every retained artifact `VERIFIED ✅` against its
pinned checksum (the one transient intermediate, `v256`, is not kept on disk). The full
walkthrough — the 9 stages, both modes, the expected output, how to assemble the working
tree, and the honest limits (the external feature step and the version-sensitive ML
checkpoints) — is in **[`docs/END_TO_END.md`](docs/END_TO_END.md)**.

**The lineage root `v51` is rebuilt from raw, deterministically.** It was actually run
end-to-end (19 steps) and its ML models were **frozen and shipped** as
`seawinds_v51_frozen_models.tar.gz` on the Release. Extract them into `<root>/logs/` and
[`scripts/rebuild_v51.py`](scripts/rebuild_v51.py) reproduces `v51′` (sha `4f14eb2e…`)
**byte-for-byte** on any machine (verified: the formerly-unseeded Track E and Track I steps
both reproduce identically). Canonical `v51`/`FINAL_BEST` stay anchored by their pinned shas
(the original Track E was unseeded and its models were never saved, so they are not
byte-reproducible — `verify_artifact.py` is the byte anchor). See `docs/END_TO_END.md`.

---

## Get the raw dataset (Tier 3–4, ≈ 21 GB)

The dataset is the competition's, under its own license (see [`NOTICE.md`](NOTICE.md)) — not
redistributed here.

- Competition: <https://www.codabench.org/competitions/13821/>
- Starting kit: <https://github.com/DavidMedernach/Hackathon-Sea-Winds-Predictions>
- Dataset `phase1_dataset.zip`: <https://zenodo.org/records/19538994>

Unzip to `data/phase1_dataset/`.

---

## The build trace

The step-by-step record of how the artifact is built is:

- [`docs/PIPELINE.md`](docs/PIPELINE.md) — the full from-raw build DAG, tier by tier, with
  exact commands and the determinism caveats.
- [`CHECKSUMS.md`](CHECKSUMS.md) — every artifact's `sha256` and the per-hop verification
  status (byte-exact / numerically identical / structural).
- [`docs/BASELINE_PROVENANCE.md`](docs/BASELINE_PROVENANCE.md) — which lineage each of the 36
  cells comes from, and the "trained on the wrong baseline" failures that shaped the rules.


---

## Honest reproducibility statement

- **The artifact is exact.** `verify_artifact.py` confirms you hold the third-place bytes.
- **The final result regenerates exactly** (numerically) from its base via
  `reproduce_final_best.py` / `scripts/build_final_best.py`, and the upstream
  speed-shrink hop reproduces **byte-for-byte**.
- **The full from-raw chain is deterministic but version-sensitive** at the ML-model root;
  it is scripted (`scripts/`) and traced (`docs/PIPELINE.md`), with the caveats spelled out
  in `docs/PIPELINE.md §7`.
- **Public ranks need the live board.** Local scoring reproduces per-cell *scores*; the
  per-cell *ranks* (and thus the headline mean rank) come from the live competition.

