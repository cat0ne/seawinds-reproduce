# Reproducing the submission — guide for the competition organiser

This is the short, do-this-in-order guide to **confirm and reproduce**
`submission_FINAL_BEST.zip` — the team's final selected entry for the Sea Winds
Predictions competition (Codabench Phase 1, #13821), which finished **3rd** on the public
leaderboard.

You need only Python 3.10+ and the lightweight dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # numpy + pandas + pyarrow
```

There are three independent things you can do; **Step 1 alone already proves the result.**

---

## Step 1 — Confirm the submitted file is the exact scored artifact (≈ 30 s)

Take the `submission_FINAL_BEST.zip` you received as the team's submission (or download it
from this repository's **GitHub Release**) and check it against the pinned checksum:

```bash
python verify_artifact.py /path/to/submission_FINAL_BEST.zip
```

Expected:

```
sha256 : 0d8c48acedf0c2ca85dce2e62ffa5e65a2ab48c891a7af07d6162c3f76bb7cd7
inner  : predictions.csv  (3,448,800 data rows, expected 3,448,800: True)
PASS   : matches pinned 'submission_FINAL_BEST.zip'.
```

A `PASS` proves the file in this repository is byte-for-byte the file that was scored.

---

## Step 2 — Regenerate the final file from its published base (≈ 2–3 min)

This shows that the winning predictions follow deterministically from the documented final
transformation. Download **both** assets from the GitHub Release:

- `submission_FINAL_BEST.zip` — the result
- `submission_BEST_FLOOR.zip` — its immediate base (the team's intermediate output, "BEST_FLOOR")

Then run:

```bash
python reproduce_final_best.py \
    --floor      submission_BEST_FLOOR.zip \
    --canonical  submission_FINAL_BEST.zip
```

Expected verdict:

```
center-frozen (q50 & dir_50 unchanged): True
max |Δ| over ALL columns (parsed)     : 0.000e+00
VERDICT: NUMERICALLY IDENTICAL
```

What this proves: the only change from the base to the final submission is a **center-frozen
20 % circular-arc shrink** of the interval on a single cell — *direction, North Sea,
pressure-level grid, 7-day horizon* (`build_final_best.py`). The forecast centers
(`q50`/`dir_50`) are untouched, and every value a scorer parses is identical to the submitted
file. (The raw file `sha256` differs only in cosmetic decimal formatting — see
[`docs/PIPELINE.md`](docs/PIPELINE.md) §7 "numerically identical vs byte-identical".)

### The base (`BEST_FLOOR`) is itself reproducible — it is not a trusted blob

`submission_BEST_FLOOR.zip` is an **intermediate result**, hosted only so this step runs
without the 21 GB raw download. Its provenance is code in this repository — every hop that
produces it has a script under [`scripts/`](scripts/), and every artifact's checksum and
producing script is tabulated in [`CHECKSUMS.md`](CHECKSUMS.md):

| Intermediate result | produced by | from | needs |
|---|---|---|---|
| `predictions_speedshrink_s08.csv` (= BEST_FLOOR) | `scripts/build_speed_shrink.py 0.08` | `ecs_d14_reposition` | pure arithmetic (byte-exact) |
| `predictions_ecs_d14_reposition.csv` | `scripts/build_ecs_d14_reposition.py` | `dirshrink_combined` | raw ECS train parquet (climatology) |
| `predictions_dirshrink_combined.csv` | `scripts/build_dir_shrink.py 0.12` | `v256` | pure arithmetic |
| `predictions_v256_…csv` | `scripts/build_final_day_station_ladder.py` | production base | deterministic |
| `submission_v222_plus_v227_plus_v232` (production base) | `scripts/reproduce_v222_plus_v227_plus_v232.py` | heavy root | 21 GB raw + heavy models |
| `predictions_heavy.csv` (heavy root) | `scripts/heavy/` (`_heavy_extracted.py` / notebook) | raw dataset | 21 GB raw + features |

So the floor can be rebuilt from the raw dataset through these scripts (Step 3); hosting it
just lets you verify the final transformation first, offline. The full hop-by-hop procedure
and the determinism caveats are in [`docs/PIPELINE.md`](docs/PIPELINE.md).

---

## Step 3 — Rebuild from the raw dataset (full from-scratch)

You hold the raw competition dataset, so you can rebuild the whole chain. The complete,
tier-by-tier procedure — raw data → engineered features → heavy-notebook base → compounding
overlays → `FINAL_BEST` — is in **[`docs/PIPELINE.md`](docs/PIPELINE.md)**, with the exact
scripts under [`scripts/`](scripts/) and every artifact's checksum in
[`CHECKSUMS.md`](CHECKSUMS.md).

Read `docs/PIPELINE.md` §7 first: the model-training root (CatBoost/LightGBM, fixed seeds) is
deterministic but **library-version sensitive**, so a cold rebuild reproduces the *scores*
exactly but may differ from the canonical `sha256` by floating-point ULPs. That is why the
canonical artifact is sha-pinned and shipped (Step 1), and why Step 2 demonstrates the final
transformation against the published base. The deep per-version lineage modules are not in
this public package (they embed live competitor board snapshots); they can be provided on
request.

---

## Scoring it yourself

The metric is the per-cell (circular) Winkler score, ranked across teams, then averaged. Use
your official scoring program on the inner `predictions.csv`, or the faithful local
implementation in [`src/scoring/`](src/scoring/) for the per-cell Winkler scores. (Per-cell
*ranks* require the full competitor field, i.e. the live leaderboard.)

---

## What "reproduce the result" means here, in one line

`submission_FINAL_BEST.zip` is a set of strong base wind forecasts whose **centers are frozen**
and whose **interval widths are re-calibrated, one cell at a time**; Step 1 proves you hold the
exact scored file, and Step 2 deterministically regenerates it from its published base.
