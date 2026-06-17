# Checksums & the verified build DAG

Every artifact on the path to the first-place submission, with its `sha256`, and
the verification status of each hop. All hashes are over the exact files described.

## The first-place artifact

| Artifact | sha256 | Notes |
|---|---|---|
| `submission_FINAL_BEST.zip` | `0d8c48acedf0c2ca85dce2e62ffa5e65a2ab48c891a7af07d6162c3f76bb7cd7` | The submitted `.zip` (attached to the GitHub Release). |
| └ inner `predictions.csv` | `5eed32b3ee381cdd96e6cf2cd0641c900d1b932169e7f191e1b26c107e705bc9` | 3,448,800 data rows + header. |

CSV schema (15 columns):

```
type,window,region,latitude,longitude,station,horizon,hour,level,q05,q50,q95,dir_05,dir_50,dir_95
```

A row's scored "cell" (1 of 36) is derived, not stored:

- **region** — `north_sea` (NS) or `east_china_sea` (ECS)
- **source** — `station` rows → *stations*; grid rows with `level ∈ {10m,100m}` → *surface*; else → *pressure*
- **horizon** — `1`, `7`, or `14` days
- **variable** — *speed* uses `q05,q50,q95`; *direction* uses `dir_05,dir_50,dir_95`

The Winkler score uses only the `[05, 95]` interval; `q50` / `dir_50` are score-irrelevant
(this is why the whole method can freeze the center and move only the interval edges).

## The build DAG (root → first-place artifact)

```
raw phase1_dataset  (Zenodo / Codabench 13821)
  │  feature engineering  (starting-kit 1_feature_engineering.ipynb)
  ▼
features/  →  HEAVY NOTEBOOK  (2d_starting_kit_heavy.ipynb / pipeline/heavy/_heavy_extracted.py, seed=42)
  ▼
predictions_heavy.csv                          frozen-center root  (290 MB)
  │  deep lineage v26→v51→…→v196→v222→v227→v232
  │  pipeline/lineage/reproduce_v222_plus_v227_plus_v232.py
  ▼
submission_v222_plus_v227_plus_v232.zip        sha 13c9fa05…   PRODUCTION BASE
  │  pipeline/overlays/build_final_day_station_ladder.py   (Dir NS Sta d1 + WS ECS Surf d1)
  ▼
predictions_v256_…csv                          (intermediate; not retained on disk)
  │  pipeline/overlays/build_dir_shrink.py 0.12   (4 disjoint direction cells)
  ▼
predictions_dirshrink_combined.csv             sha 8b4347ec…
  │  pipeline/overlays/build_ecs_d14_reposition.py   (ECS Surf d14 climatological arcs; needs raw ECS train parquet)
  ▼
predictions_ecs_d14_reposition.csv             sha 0cbdf30e…
  │  pipeline/overlays/build_speed_shrink.py 0.08    (ECS Sta/Surf d14 speed)
  ▼
predictions_speedshrink_s08.csv  ≡ BEST_FLOOR  sha d95e4dd5…   (zip sha 17bde403…)
  │  pipeline/overlays/build_final_best.py           (Dir NS Pres d7 12% → 20%)
  ▼
predictions_FINAL_BEST.csv                     sha 5eed32b3…   ← FIRST PLACE
```

## Per-hop verification status

| Hop | Script | Inputs on disk? | Verified | Determinism |
|---|---|---|---|---|
| floor → **FINAL_BEST** | `build_final_best.py` | yes (floor) | ✅ **numerically identical** to canonical (max \|Δ\|=0 after CSV round-trip; sha differs only in cosmetic float formatting) | pure arithmetic |
| reposition → floor | `build_speed_shrink.py 0.08` | yes | ✅ **byte-exact** (sha `d95e4dd5…` reproduced) | pure arithmetic |
| dirshrink → reposition | `build_ecs_d14_reposition.py` | input yes; **needs raw ECS train parquet** | structural (climatology from raw) | deterministic given raw data |
| v256 → dirshrink | `build_dir_shrink.py 0.12` | input **not retained** | structural (log + source) | pure arithmetic |
| base → v256 | `build_final_day_station_ladder.py` | donor CSVs not all retained | structural (log + source) | deterministic |
| raw → production base | `reproduce_v222_plus_v227_plus_v232.py` | needs 21 GB raw + heavy models | not re-run here | deterministic, **library-version-sensitive** |
| raw → heavy root | heavy notebook (seed 42) | needs raw + features | not re-run here | deterministic, **library-version-sensitive** |

"Structural" = confirmed from the logbook (`docs/logbook/`) + the builder source, and (for
the on-disk hops) by column-level CSV diffing, but not re-run end-to-end here because the
exact input CSV is not retained on disk.

## Reproduce these checks yourself

```bash
# Byte-anchor the first-place artifact (after downloading it from the Release):
python verify_artifact.py /path/to/submission_FINAL_BEST.zip       # -> PASS

# Regenerate FINAL_BEST from the floor and confirm numerical identity:
python reproduce_final_best.py \
    --floor /path/to/predictions_speedshrink_s08.csv \
    --canonical /path/to/submission_FINAL_BEST.zip                 # -> NUMERICALLY IDENTICAL
```

See [`docs/PIPELINE.md`](docs/PIPELINE.md) for the full from-scratch procedure, including
the raw-data download and the deep-lineage rebuild.
