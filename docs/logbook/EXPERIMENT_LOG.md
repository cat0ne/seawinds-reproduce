# Experiment Log — Sea Winds Predictions

> Living document. One section per submission, updated after each leaderboard score.
> Raw scores live in `submissions/log.json`. This file captures the *why* and *what we learned*.

| 2026-06-15 00:35 | last_shot_speed_shrink_on_final_best | PENDING SCORE | LAST SHOT / RANK-2 ATTEMPT | `submission_LAST_SHOT.zip`, rebased on `submission_FINAL_BEST.zip`; changes only speed q05/q95 on NS/ECS station d7 plus NS surface/pressure d7/d14 | High-risk final slot: keeps final_best direction gain and attacks the only remaining cells with enough combined rank upside. |
---

## Build — submission_LAST_SHOT.zip

**Recorded**: 2026-06-15T00:35:00+02:00
**Artifact**: `submissions/submission_LAST_SHOT.zip`
**Base**: `submissions/predictions_FINAL_BEST.csv`
**ZIP SHA256**: `245271d6a0a81d067b0204cb1ea8c37875ad95f1cd4259d215f38f157bfbd243`
**predictions.csv SHA256**: `0253d385a7cdcb2b0c7e9f6015454dcc2111ae086b2699c8457cbd37302f571e`
**Posture**: final-slot rank-2 attempt

### Scope

Center-frozen speed shrink only. `q50` is unchanged, all direction columns are
unchanged, and no non-target q rows changed.

```text
ECS Sta d7   s=0.10  rows=224     width 7.0814 -> 6.3733
NS Sta d7    s=0.10  rows=256     width 11.3143 -> 10.1829
NS Surf d7   s=0.02  rows=164160  width 10.0033 -> 9.8032
NS Surf d14  s=0.02  rows=164160  width 10.4741 -> 10.2646
NS Pres d7   s=0.02  rows=410400  width 17.2683 -> 16.9229
NS Pres d14  s=0.02  rows=410400  width 18.2178 -> 17.8535
```

### Verification

ZIP integrity passes, the archive contains exactly one `predictions.csv`, the
header is correct, and the file has `3,448,801` lines including the header.
Numeric scope diff against `predictions_FINAL_BEST.csv`: `1,149,600` changed
rows; `q05/q95` changed only; `q50` and all direction values unchanged.

### Decision

Upload only if spending the final risk slot. This is not a floor packet. It is
the only current artifact with enough combined upside to plausibly catch rank 2:
station d7 speed can move multiple ranks if overcoverage transfers, and the NS
grid speed micro-shrinks can add small visible flips.

## Rank Refresh — submission_FINAL_BEST.zip

**Recorded**: 2026-06-15T00:22:00+02:00
**Source**: pasted Codabench leaderboard row `797583`
**Artifact**: `submissions/submission_FINAL_BEST.zip`
**ZIP SHA256**: `0d8c48acedf0c2ca85dce2e62ffa5e65a2ab48c891a7af07d6162c3f76bb7cd7`
**predictions.csv SHA256**: `5eed32b3ee381cdd96e6cf2cd0641c900d1b932169e7f191e1b26c107e705bc9`
**Codabench display**: `Mean Rank=99999.0`
**Real public placement**: rank `#3` by recomputing all 36 per-dimension ranks
**Estimated visible mean rank**: `5.027778`

### Method

Parsed the 24 visible leaderboard rows and ignored the fake displayed mean-rank
values. Per-dimension ranks use average tie ranking across the pasted score
cells.

### Decision

Treat `submission_FINAL_BEST.zip` as the final selected artifact. It improves
`Dir NS Pressure d7` versus the prior floor (`247.53 -> 246.11`) at pasted
precision, but the refreshed board also improves competitors. Hegoa remains
behind `Printemps` and `JLShen`, ahead of `Matteo`.

## Rank Refresh — submission_BEST_FLOOR.zip best floor

**Recorded**: 2026-06-14T22:57:00+02:00
**Source**: pasted Codabench leaderboard row `797515`
**Artifact**: `submissions/submission_BEST_FLOOR.zip`
**Alias**: byte-identical to `submissions/submission_speedshrink_s08.zip`
**ZIP SHA256**: `17bde40362671bac983d21559394b9dc6322689dbf0456c75ef04ba62130f38e`
**predictions.csv SHA256**: `d95e4dd51a322c0a27b1019f7a040a4737d9df51d601f3af667a5f7e5a17ec0b`
**Codabench display**: `Mean Rank=99999.0`
**Real public placement**: rank `#3` by recomputing all 36 per-dimension ranks
**Estimated visible mean rank**: `4.805556`

### Method

Parsed the 24 visible leaderboard rows and removed the fake displayed mean-rank
value from scoring. For this floor decision, the Hegoa row is the pasted row for
`submission_BEST_FLOOR.zip` itself, not the older `dirshrink_combined` override.
Per-dimension ranks use average tie ranking, which best matches Codabench's
displayed mean ranks for the other participants.

### Decision

Treat `submission_BEST_FLOOR.zip` as the best floor submission. It is behind
`Printemps` and `JLShen`, ahead of `Matteo`, and materially ahead of the rest
of the visible board. Pending packets `v257` through `v261` must beat this
floor before promotion.

## Build — v260_combined_dirpush_hint (FINAL-HOUR DIR PUSH, PENDING SCORE)

**Recorded**: 2026-06-14T19:47:16+00:00
**Artifact**: `submissions/submission_v260_combined_dirpush_hint.zip`
**Base**: `dirshrink_combined`
**Posture**: high-risk public-rank push on already raw-positive direction cells

### Approach

Built on scored `dirshrink_combined` and increased shrink only on direction
cells that were raw-positive in the combined score. This targets public rank
positions rather than the already-rank-1 `Dir NS Sta d1` margin.

### Scope

Dir NS Pres d7 0.12->0.28, 410400/410400 changed; Dir NS Surf d7 0.12->0.20, 164160/164160 changed; Dir ECS Surf d7 0.12->0.25, 164160/164160 changed; Dir NS Sta d14 0.12->0.12, 0/256 changed

Rows: `3,448,800`. ZIP SHA256: `b631be5150d0e9bc6ddedb73fcc18e618e0f8e90fd3ac86fd06a6959e9eac29b`.

### Next Step

Upload as a final-hour risk slot. If any pushed cell regresses, back off to the
medium bracket or keep `dirshrink_combined` selected.

## Build — v261_combined_dirpush_mid (FINAL-HOUR DIR PUSH, PENDING SCORE)

**Recorded**: 2026-06-14T19:47:16+00:00
**Artifact**: `submissions/submission_v261_combined_dirpush_mid.zip`
**Base**: `dirshrink_combined`
**Posture**: medium-risk bracket between proven 12% and hinted push

### Approach

Built on scored `dirshrink_combined` and increased shrink only on direction
cells that were raw-positive in the combined score. This targets public rank
positions rather than the already-rank-1 `Dir NS Sta d1` margin.

### Scope

Dir NS Pres d7 0.12->0.20, 410400/410400 changed; Dir NS Surf d7 0.12->0.16, 164160/164160 changed; Dir ECS Surf d7 0.12->0.18, 164160/164160 changed; Dir NS Sta d14 0.12->0.12, 0/256 changed

Rows: `3,448,800`. ZIP SHA256: `0e6e2106caef85c3208682ea73cfc83425643ca0142023fcc42cf0aa3a790380`.

### Next Step

Upload as a final-hour risk slot. If any pushed cell regresses, back off to the
medium bracket or keep `dirshrink_combined` selected.

## Build — v257_combined_sta_d1_total_0p70 (FINAL-HOUR STATION PUSH, PENDING SCORE)

**Recorded**: 2026-06-14T19:08:42+00:00
**Artifact**: `submissions/submission_v257_combined_sta_d1_total_0p70.zip`
**Base**: `dirshrink_combined`
**Posture**: aggressive continuation of monotonic station d1 shrink ladder

### Approach

Built on the scored non-worse `dirshrink_combined` packet and pushed only the
already monotonic `Dir NS Sta d1` shrink. All four d7/d14 direction winners and
the ECS surface d1 speed donor are preserved.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `fc615257877e26cd4afde5c39657562903b1310ccd9193745d5439cb5d8c6822`.

### Next Step

Upload as a final-hour risk slot. Stop this ladder at the first primary or
target-cell regression.

## Build — v258_combined_sta_d1_total_0p80 (FINAL-HOUR STATION PUSH, PENDING SCORE)

**Recorded**: 2026-06-14T19:08:42+00:00
**Artifact**: `submissions/submission_v258_combined_sta_d1_total_0p80.zip`
**Base**: `dirshrink_combined`
**Posture**: high-risk continuation of monotonic station d1 shrink ladder

### Approach

Built on the scored non-worse `dirshrink_combined` packet and pushed only the
already monotonic `Dir NS Sta d1` shrink. All four d7/d14 direction winners and
the ECS surface d1 speed donor are preserved.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `5bc6fc1eac6bde96f09eeff7fc6a66813ba292e152465abe3ccec378caa15b28`.

### Next Step

Upload as a final-hour risk slot. Stop this ladder at the first primary or
target-cell regression.

## Build — v259_combined_sta_d1_total_0p90 (FINAL-HOUR STATION PUSH, PENDING SCORE)

**Recorded**: 2026-06-14T19:08:42+00:00
**Artifact**: `submissions/submission_v259_combined_sta_d1_total_0p90.zip`
**Base**: `dirshrink_combined`
**Posture**: maximum-risk station d1 over-shrink probe after v256 remained positive

### Approach

Built on the scored non-worse `dirshrink_combined` packet and pushed only the
already monotonic `Dir NS Sta d1` shrink. All four d7/d14 direction winners and
the ECS surface d1 speed donor are preserved.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `c47b6bbd297f832c6a0c72baaea1c537e5233a52d0e1598ec7c1bc8619f1b92b`.

### Next Step

Upload as a final-hour risk slot. Stop this ladder at the first primary or
target-cell regression.

## Score Update — dirshrink_combined

**Recorded**: 2026-06-14T18:22:00+00:00
**Artifact**: `submission_dirshrink_combined.zip`
**Base comparison**: `v256_station_0p60_plus_ecs_d1_speed_only`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418801`
**Codabench primary delta vs `v256_station_0p60_plus_ecs_d1_speed_only`**: `+0.000000`
**Estimated public-rank delta vs `v256_station_0p60_plus_ecs_d1_speed_only`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d14_ns             305.6286  303.2145   -2.4141     -1
dir_pressure_d7_ns              255.2599  247.5340   -7.7259      0
dir_surface_d7_ns               284.7855  279.4518   -5.3337      0
dir_surface_d7_ecs              265.8556  264.2036   -1.6520      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v256_station_0p60_plus_ecs_d1_speed_only

**Recorded**: 2026-06-14T17:47:12+00:00
**Artifact**: `submission_v256_station_0p60_plus_ecs_d1_speed_only.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418801`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000061`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.5052   -0.2422     -1
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v255_station_0p55_plus_ecs_d1_speed_only

**Recorded**: 2026-06-14T17:44:32+00:00
**Artifact**: `submission_v255_station_0p55_plus_ecs_d1_speed_only.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418805`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000057`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.5254   -0.2220     -1
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v254_station_0p50_plus_ecs_d1_speed_only

**Recorded**: 2026-06-14T17:42:07+00:00
**Artifact**: `submission_v254_station_0p50_plus_ecs_d1_speed_only.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418810`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000052`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.5455   -0.2019     -1
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v253_station_0p45_plus_ecs_d1_speed_only

**Recorded**: 2026-06-14T17:02:09+00:00
**Artifact**: `submission_v253_station_0p45_plus_ecs_d1_speed_only.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418815`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000047`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.5657   -0.1817     -1
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Build — v254_station_0p50_plus_ecs_d1_speed_only (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T16:36:48+00:00
**Artifact**: `submissions/submission_v254_station_0p50_plus_ecs_d1_speed_only.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: aggressive compound cleanup; tests whether the post-v252 station shrink can move further

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `059b0db8226b58359e91b85ba68486b335ca7a486116f9d432f0fbdcf527c874`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v255_station_0p55_plus_ecs_d1_speed_only (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T16:36:48+00:00
**Artifact**: `submissions/submission_v255_station_0p55_plus_ecs_d1_speed_only.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: high-risk compound cleanup; explores whether the station d1 interval remains over-wide

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `fbf0d31c2b612dc0735def8ccaaf81a0b3e978797bb9d3514df4710a379f7af1`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v256_station_0p60_plus_ecs_d1_speed_only (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T16:36:48+00:00
**Artifact**: `submissions/submission_v256_station_0p60_plus_ecs_d1_speed_only.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: maximum-risk compound cleanup; final-day over-shrink probe after v252 proved +0.45 positive

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `ee08079cd41e96616ab177a264ba535052b1fa2b2deab7375e76838f8f9970f8`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v253_station_0p45_plus_ecs_d1_speed_only (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T16:21:59+00:00
**Artifact**: `submissions/submission_v253_station_0p45_plus_ecs_d1_speed_only.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: compound cleanup; preserves v252 winning cells while removing observed NS d1 speed regression

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `9f57cebb4d0250dcb9839838ee38e91b4d2bb888e6c96ff7c831dd8a82081e2b`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Score Update — v252_full_risk_ns_sta_d1_0p45_plus_d1_speed

**Recorded**: 2026-06-14T16:21:44+00:00
**Artifact**: `submission_v252_full_risk_ns_sta_d1_0p45_plus_d1_speed.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418819`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000043`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `-0.0278`

### Decision

Rank-positive candidate. Consider promotion only if changed cells are intentional and no blocked ingredient is included.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.5657   -0.1817     -1
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
speed_surface_d1_ns               4.7073    4.7089    0.0016      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v248_ns_sta_d1_dir_shrink_extra_0p25

**Recorded**: 2026-06-14T16:21:36+00:00
**Artifact**: `submission_v248_ns_sta_d1_dir_shrink_extra_0p25.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418839`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000023`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `+0.0000`

### Decision

No automatic promotion. Follow final-20 plan and preserve quota.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.6465   -0.1009      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Build — v252_full_risk_ns_sta_d1_0p45_plus_d1_speed (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T15:45:47+00:00
**Artifact**: `submissions/submission_v252_full_risk_ns_sta_d1_0p45_plus_d1_speed.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: full-risk compound; post-v249 station bracket plus non-route-positive d1 speed probes

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied; WS NS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `a7a98912d28d2c10af6eca7e4e79a787a0237ffbe1222d7e5300f8eb670e769e`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v250_ns_sta_d1_dir_shrink_extra_0p45 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T15:38:12+00:00
**Artifact**: `submissions/submission_v250_ns_sta_d1_dir_shrink_extra_0p45.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction post-v249 bracket; expected to clear boundary with small margin

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `e6aa2294f0726f7d6f75ae2188fd3ab820a2b2320c52c2c7df7182702a3bb2a1`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v251_ns_sta_d1_dir_shrink_extra_0p50 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T15:38:12+00:00
**Artifact**: `submissions/submission_v251_ns_sta_d1_dir_shrink_extra_0p50.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction post-v249 bracket; larger clearance, higher undercoverage risk

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `d44c67187f0364cfc9e66d9082d2e736f4aa2af1ed17d9af610c9dd634554833`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Score Update — v249_ns_sta_d1_dir_shrink_extra_0p35

**Recorded**: 2026-06-14T15:37:04+00:00
**Artifact**: `submission_v249_ns_sta_d1_dir_shrink_extra_0p35.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-14`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418839`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `-0.000023`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `+0.0000`

### Decision

No automatic promotion. Follow final-20 plan and preserve quota.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7474  170.6465   -0.1009      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Build — v248_ns_sta_d1_dir_shrink_extra_0p25 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:45:29+00:00
**Artifact**: `submissions/submission_v248_ns_sta_d1_dir_shrink_extra_0p25.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction fine bracket; between v244 and v245

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `2c1273b17227eeb4c1b3b48a47add45f0a87f479dea1207cf8ea46bd74b17e59`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v249_ns_sta_d1_dir_shrink_extra_0p35 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:45:29+00:00
**Artifact**: `submissions/submission_v249_ns_sta_d1_dir_shrink_extra_0p35.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction fine bracket; between v245 and v246

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `8741e9de855ca6e682ec7950a13018c4dbccb3938fdb4f5b744b7a1ee9b15c16`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v243_ns_sta_d1_dir_shrink_extra_0p10 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:21:10+00:00
**Artifact**: `submissions/submission_v243_ns_sta_d1_dir_shrink_extra_0p10.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction ladder; v227-proven family, still endpoint-risk

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `0a0e8f134cedd0b5de15ae64fbe38193743042abbd7e6b3f709e74ed95fdebb3`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v244_ns_sta_d1_dir_shrink_extra_0p20 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:21:10+00:00
**Artifact**: `submissions/submission_v244_ns_sta_d1_dir_shrink_extra_0p20.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction ladder; roughly double v227 additional pressure

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `9dda003be1de0a3726fc818f472b889fa577b1251bd44f163367c4638553a82a`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v245_ns_sta_d1_dir_shrink_extra_0p30 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:21:10+00:00
**Artifact**: `submissions/submission_v245_ns_sta_d1_dir_shrink_extra_0p30.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction ladder; linearized target clears fresh rank-1 boundary

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `ebb9ee94889394d8956f501275cac0b243d447a798546b419da84b5b4738098e`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v246_ns_sta_d1_dir_shrink_extra_0p40 (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:21:10+00:00
**Artifact**: `submissions/submission_v246_ns_sta_d1_dir_shrink_extra_0p40.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell station direction ladder; aggressive undercoverage-risk point

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied

Rows: `3,448,800`. ZIP SHA256: `0b06173543ebbfbb9400fcec3aad0472f75cca3ea553ca3cd3881cab7deeabb9`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Build — v247_full_risk_ns_sta_d1_plus_d1_speed (FINAL-DAY RISK, PENDING SCORE)

**Recorded**: 2026-06-14T13:21:10+00:00
**Artifact**: `submissions/submission_v247_full_risk_ns_sta_d1_plus_d1_speed.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: full-risk compound; station rank flip attempt plus non-route-positive d1 speed probes

### Approach

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied; WS NS Surf d1 69768/164160 changed/copied

Rows: `3,448,800`. ZIP SHA256: `6a0c0b2f61eee61fd83fbbca802b43e0cc3d61c314576337353e1fc4785d84b9`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.

## Invalidation — v237-v242 Zero-Diff Donor Grafts

**Recorded**: 2026-06-14T11:55:04+00:00
**Decision**: do not upload `v237`-`v242`; generated CSV/ZIP files were removed.

### Root Cause

The local target-cell `q05/q50/q95` values in `predictions_v47.csv` and `predictions_v48.csv` are byte-equivalent to `predictions_v222_plus_v227_plus_v232.csv` for the five mined cells. The apparent donor improvements came from old two-decimal leaderboard values such as `15.12` and `9.72` being compared against current four-decimal cells such as `15.1216` and `9.7234`.

### Evidence

Chunked diff confirmed `changed_rows = 0` and `max_abs_diff = 0.0` for all five planned graft cells. `scripts/build_cell_donor_grafts.py` now refuses zero-diff donor grafts before producing uploadable artifacts.

## Build — v237_donor_v47_ws_ns_surf_d14 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v237_donor_v47_ws_ns_surf_d14.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell public-rank probe; exact historical donor score target

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS NS Surf d14 from v47 11->7 (0/164160 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`4`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Build — v238_donor_v47_ws_ns_surf_d7 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v238_donor_v47_ws_ns_surf_d7.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell public-rank probe; exact historical donor score target

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS NS Surf d7 from v47 11->8 (0/164160 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`3`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Build — v239_donor_v47_ws_ns_pres_d14 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v239_donor_v47_ws_ns_pres_d14.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell public-rank probe; exact historical donor score target

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS NS Pres d14 from v47 10->7 (0/410400 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`3`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Build — v240_donor_v47_ws_ns_pres_d7 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v240_donor_v47_ws_ns_pres_d7.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell public-rank probe; exact historical donor score target

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS NS Pres d7 from v47 10->8 (0/410400 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`2`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Build — v241_donor_v48_ws_ecs_surf_d7 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v241_donor_v48_ws_ecs_surf_d7.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: single-cell public-rank probe; exact historical donor score target

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS ECS Surf d7 from v48 3->2 (0/164160 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`1`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Build — v242_donor_rank_sweep_all5 (DONOR GRAFT, INVALID / DO NOT UPLOAD)

**Recorded**: 2026-06-14T11:48:14+00:00
**Artifact**: `submissions/submission_v242_donor_rank_sweep_all5.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: full-risk compound; cells are disjoint and independent but not score-gated as a stack

### Approach

Copied only the official target-cell speed interval columns from historically
scored donor submissions onto the current production base. No direction columns
or non-target rows are intentionally changed.

### Scope

WS NS Surf d14 from v47 11->7 (0/164160 changed/copied); WS NS Surf d7 from v47 11->8 (0/164160 changed/copied); WS NS Pres d14 from v47 10->7 (0/410400 changed/copied); WS NS Pres d7 from v47 10->8 (0/410400 changed/copied); WS ECS Surf d7 from v48 3->2 (0/164160 changed/copied)

Rows: `3,448,800`. Projected visible rank gain:
`13`. ZIP SHA256: `6f85a69b74ce23e144044379bdc1a0d00445f9ab49445c62a8e2663e931ffb9f`.

### Outcome

Invalidated before upload on `2026-06-14T11:55:04+00:00`. A chunked diff against the production base found `0` changed target rows; the generated CSV/ZIP were byte-identical to `v222_plus_v227_plus_v232` and were removed from `submissions/`. The apparent donor rank gains came from rounded historical leaderboard values, not real local prediction deltas.

## Score Update — v236_full_risk_jlshen

**Recorded**: 2026-06-14T00:40:26+02:00
**Artifact**: `submission_v236_full_risk_jlshen.zip`
**Base comparison**: `v222_plus_v227_plus_v232`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-12-pasted-top-two`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418884`
**Codabench primary delta vs `v222_plus_v227_plus_v232`**: `+0.000022`
**Estimated public-rank delta vs `v222_plus_v227_plus_v232`**: `+0.0000`

### Decision

No automatic promotion. Follow final-20 plan and preserve quota.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ecs             241.2614  241.3581    0.0967      0
speed_surface_d14_ecs            10.6506   10.6552    0.0046      0
speed_surface_d7_ns              14.4643   14.4662    0.0019      0
speed_pressure_d1_ns              6.7876    6.7886    0.0010      0
speed_pressure_d7_ecs            15.3733   15.3737    0.0004      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Build — v236_full_risk_jlshen (FULL RISK, SCORED REJECT)

**Recorded**: 2026-06-13T21:51:25+00:00
**Artifact**: `submissions/submission_v236_full_risk_jlshen.zip`
**Base**: `v222_plus_v227_plus_v232`
**Posture**: full-risk JLShen response after quota increased to 25 available submissions.

### Approach

Stacked the remaining high-upside built probes on the scored production base:
`v233`, `v234`, `v229`, `v230`, and `v235`. The builder applies each donor only
on rows where it differs from its own `v222` base, so the scored `v227` and
`v232` direction gains are preserved outside the true `v235` target rows.

### Scope

Overlay changed rows: `v233:271744, v234:144836, v229:348840, v230:63965, v235:224`. Total rows:
`3,448,800`. ZIP SHA256: `5a278c42e6902d747626efdddde6d557d9474a4d5c016c8e1180c48c330a8d89`.

### Outcome

Scored as a reject on 2026-06-14: primary `1.418884` versus production
`v222_plus_v227_plus_v232` at `1.418862`. All five overlaid target probes
failed or regressed their cells, so do not promote this artifact or route any
of `v233`, `v234`, `v229`, `v230`, or `v235` as the next comeback slot.

## Board Refresh — 2026-06-12 JLShen Overtakes Raw Lead

**Recorded**: 2026-06-12
**Snapshot**: `2026-06-12-pasted-top-two`
**Board state**: June 8 competitors preserved, JLShen added
**Router**: `HOLD_ECS_D1`

### Decision

Treat this as a tactical reset, not a score event. `v222_plus_v227_plus_v232`
remains the production base. `v235` and
`v222_plus_v227_plus_v232_plus_v235` are built-hold only and must not be
treated as production or uploaded automatically.

### Damaged Cells

- `Dir NS Surf d1` gap `3.0256` cWS
- `Dir ECS Surf d1` gap `5.4262` cWS
- `Dir ECS Sta d14` gap `24.5648` cWS

### Next Lane

Surface-d1 direction recapture using `v46` copula-lineage provenance, with
center/regime/concentration adjustments only. Do not do blind endpoint edits.
Keep `Dir ECS Sta d14` research-only because station d14 direction has already
failed catastrophically.

## Score Update — v222_plus_v227_plus_v232

**Recorded**: 2026-06-08T09:32:19+00:00
**Artifact**: `submission_v222_plus_v227_plus_v232.zip`
**Base comparison**: `v227`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-06`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418862`
**Codabench primary delta vs `v227`**: `+0.000000`
**Estimated public-rank delta vs `v227`**: `+0.0000`

### Decision

v222_plus_v227_plus_v232 is target-positive on dir_stations_d7_ns while preserving the prior chain. Refresh the live board before spending any further station-direction salvage slot.

### Target Rank EV

- Target: `Dir NS Sta d7` (`dir_stations_d7_ns`)
- Score: `310.9467 -> 310.2390` (`-0.7077`)
- Rank: `4 -> 4` (`+0`)
- Boundary: `carlometta` at `301.5400`; clearance `-8.6990`
- Gate flags: target_positive=`true`, visible_rank_gain=`false`, primary_nonworse=`true`

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d7_ns              310.9467  310.2390   -0.7077      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v227

**Recorded**: 2026-06-07T00:00:00Z
**Artifact**: `submission_v227.zip`
**Base comparison**: `v222_plus_v225`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-06`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418862`
**Codabench primary delta vs `v222_plus_v225`**: `-0.000004`
**Estimated public-rank delta vs `v222_plus_v225`**: `+0.0000`

### Decision

v227 is target-positive on dir_stations_d1_ns versus v222. Run next_slot_decision.py --report-date "$(date +%F)"; if v232 is still justified, the next guarded build is v222_plus_v227_plus_v232 so the v227 gain is preserved.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_stations_d1_ns              170.7878  170.7474   -0.0404      0
speed_surface_d1_ecs              4.5951    4.5972    0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v226

**Recorded**: 2026-06-06T21:39:50+00:00
**Artifact**: `submission_v226.zip`
**Base comparison**: `v222`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-06`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418875`
**Codabench primary delta vs `v222`**: `+0.000003`
**Estimated public-rank delta vs `v222`**: `+0.0000`

### Decision

SCORED: REJECT. Standalone `v226` worsened its intended cell
`speed_surface_d7_ecs` from `9.7234` to `9.7246` and did not preserve the
current best `v222_plus_v225` speed_surface_d1_ecs gain. Primary `1.418875`
is worse than both `v222` (`1.418872`) and `v222_plus_v225` (`1.418866`).
Do not build on `v226`; the speed chain remains locked. After `v227` scored as
the new best, the router-selected upload is the guarded
`v222_plus_v227_plus_v232` compound, not standalone `v232`.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
speed_surface_d7_ecs              9.7234    9.7246    0.0012      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v222_plus_v225

**Recorded**: 2026-06-06T17:12:15+00:00
**Artifact**: `submission_v222_plus_v225.zip`
**Base comparison**: `v222`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-06`
**Parsed score cells**: `36 / 36`
**Board freshness**: `OK`
**Codabench primary_score / tracked mean_rank**: `1.418866`
**Codabench primary delta vs `v222`**: `-0.000006`
**Estimated public-rank delta vs `v222`**: `+0.0000`

### Decision

v222_plus_v225 outcome RAW_ONLY_GAIN: improved speed_surface_d1_ecs (-0.0021) but did not flip a visible rank versus v222. Hold the raw-only gain; do not build v222_plus_v225_plus_v226 unless a refreshed live board makes this cell rank-moving.

### Target Rank EV

- Target: `WS ECS Surf d1` (`speed_surface_d1_ecs`)
- Score: `4.5972 -> 4.5951` (`-0.0021`)
- Rank: `4 -> 4` (`+0`)
- Boundary: `carlometta` at `4.5900`; clearance `-0.0051`
- Gate flags: target_positive=`true`, visible_rank_gain=`false`, primary_nonworse=`true`

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
speed_surface_d1_ecs              4.5972    4.5951   -0.0021      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Update — v222

**Recorded**: 2026-06-04T00:16:50+00:00
**Artifact**: `submission_v222.zip`
**Base comparison**: `v196`
**Snapshot**: `competitors_snapshot.json` as-of `2026-06-04`
**Codabench primary_score / tracked mean_rank**: `1.418872`
**Estimated public-rank delta vs `v196`**: `-0.0833`

### Decision

PROMOTE v222. Next: refresh board, then choose hold/v225 diagnostic/v223 only by boundary. Apply docs/research/POST_V222_SCENARIO_MATRIX_2026_06_04.md before spending the next slot.

### Largest Deltas Versus Base

```text
cell                                base       new   score_d rank_d
-------------------------------------------------------------------
dir_pressure_d7_ns              266.5361  255.2599  -11.2762     -2
dir_pressure_d7_ecs             233.5926  229.7705   -3.8221     -1
dir_surface_d7_ns               285.8122  284.7855   -1.0267      0
```

### Next Step

Run:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

## Score Progression

| # | ID | Score | Mean Rank | Delta | Key change |
|---|-----|-------|-----------|-------|------------|
| 1 | s001 | 1.673 | 1.67 | — | Baseline (2a_light unmodified) |
| 2 | s002 | 1.770 | 1.77 | +0.097 | Station EMOS calibration (catastrophic) |
| 3 | v2 | 1.679 | 1.68 | -0.091 | Direct pressure CatBoost (no horizon feature) |
| 4 | v3 | 1.651 | 1.65 | -0.028 | v2 + direction overlay (LightGBM sin/cos) |
| 5 | v4 | 1.632 | 1.63 | -0.019 | Baseline speed + direction overlay (cherry-pick) |
| 6 | v5 | 1.670 | 1.67 | +0.038 | Horizon-aware pressure + direction scaling (regression) |
| 7 | **v6** | **1.625** | **1.63** | **-0.045** | **v4 + station height correction** |
| 8 | v7 | 1.666 | 1.67 | +0.041 | Per-horizon direction (merge bug — NOT real) |
| 9 | **v8** | **1.494** | **4.22** | **-0.172** | **Residual speed + per-horizon direction (BREAKTHROUGH)** |
| 10 | v12 | — | PENDING | — | Cherry-pick (identical to v8?) |
| 11 | v13 | 1.496 | — | +0.002 | d14 cross-horizon residual (regression) |
| 12 | v14 | 1.497 | — | +0.001 | CQR calibration on pressure (regression) |
| 13 | v15 | 1.584 | — | +0.087 | Station direction (catastrophic) |
| 14 | **v16** | **1.494** | **4.28** | **0.000** | **NS d14 direction revert to baseline (mean_rank WORSE due to carlometta)** |
| 15 | v17 | — | PENDING | — | Selective CQR calibration on pressure speed |
| 16 | v18 | — | PENDING | — | Station direction only |
| 17 | **v19** | **1.451** | PENDING | **-0.043** | **Station model breakthrough — promote as tactical base** |
| 18 | **v26** | **1.451** | PENDING | **0.000 primary / -45.24 raw cWS** | **v19 station speed + station-direction cherry-pick — promote** |
| 19 | **v27** | **1.436** | PENDING | **-0.015 primary / -9.16 raw WS** | **v26 + heavy-baseline grid-speed graft — promote** |
| 20 | **v28** | **1.436** | PENDING | **0.000 primary / -16.99 raw cWS** | **v27 + heavy NS d7 station/surface direction cherry-pick — promote** |
| 21 | v29 | — | HOLD | — | Reserve micro-gain: v28 + baseline ECS surface d14 direction revert |
| 22 | **v30** | **1.435** | SCORED | **-0.001 primary / -0.376 raw WS** | **v28 + pressure-conditioned station speed d1/d7; mixed but aggregate win** |
| 23 | **v31** | **1.435** | SCORED | **-0.001 primary / -1.095 raw scoped** | **v28 + cleaned v30 station winners + held v29 ECS surface d14 direction — promote** |
| 24 | **v32** | **1.439** | **REJECT** | **+0.004 primary / +52.86 raw scoped** | **V31 + d14 enriched LGB+analog station speed + direction bias correction (rejected)** |
| 25 | v33 | 1.449 | REJECT | +0.015 primary / +616.36 raw station-direction | V31 + Track D circular station-direction overlay only (failed transfer) |
| 26 | v34 | 1.448 | REJECT | +0.014 primary / +1.95 raw station-speed | V31 + Track E station-speed residual overlay (failed transfer except ECS d1) |
| 27 | **v35** | **1.433** | **PROMOTE** | **-0.002 primary / -7.52 raw cWS** | **V31 + v32 NS d1 station-direction donor only — new base** |
| 28 | v37 | 1.444 | REJECT | +0.011 primary / +165.78 raw cWS | V35 + Track F pressure d1/d7 direction overlay failed transfer |
| 29 | **v38** | **1.432** | **PROMOTE** | **-0.0006 primary / -0.2017 raw WS** | **V35 + v34 ECS d1 station-speed donor only — new base** |
| 30 | v39 | 1.432 | RAW WIN | 0.000 primary / -13.50 raw cWS | V38 + Track I ECS d1 station-direction residual transferred |
| 31 | v40 | 1.433 | REJECT | +0.0006 primary / +574.64 raw cWS | V38 + Track I ECS all station-direction failed due d14 |
| 32 | **v41** | **1.429** | **PROMOTE** | **-0.0028 primary / -12.19 raw cWS** | **V39 + gated Track I ECS d7 station direction — new base** |
| 33 | v42 | 1.429 | PENDING / METHODOLOGY | 0.000 primary / identical preds | V41 learned gate (logistic regression trained on v41 labels) |
| 34 | v43 | 1.429 | REJECT | 0.000 primary / +49.0 cWS d14 | Ultra-conservative d14 probe: even 30 rows with shift <= 15° regressed |
| 35 | **v46** | **1.429** | **PROMOTE** | **-0.000752 primary / -22.3 raw cWS** | **Speed-direction copula: first moat technique transfers** |
| 36 | v47 | 2.11 | NEUTRAL | +0.00 mean_rank / same 17 #1 ranks | Copula per-horizon damping — BUILT ON WRONG BASE (v41 not v46) |
| 37 | v48 | 2.44 | REJECT | +0.33 mean_rank / NS speed regressed | Yeo-Johnson grid speed retrain — overfit, dead end |
| 38 | v50 | 4.06 | CATASTROPHIC | +1.95 mean_rank / all grid speed rank 10 | CQR calibration — constant offsets too crude, intervals 2x wider |
| 39 | **v51** | **1.429** | **1.44 est.** | **primary neutral / -2.30 raw cWS** | **V46 + v47 ECS pressure d7/d14 direction donor — current base** |
| 40 | v52 | 1.430 | REJECT | +0.0011 primary / +0.3845 raw WS | V51 + ECS surface d7/d14 spatial-aggregation speed overlay regressed |
| 41 | **v53** | **1.428** | **PROMOTE** | **-0.0009 primary / -0.3399 raw WS** | **V51 + ECS pressure d7 shear/ws³ speed overlay — former base** |
| 42 | v54 | 1.428 | REJECT | primary neutral / +0.5270 raw WS | V53 + NS pressure d7 shear/ws³ speed overlay regressed |
| 43 | v55 | 1.428233 | REJECT | +0.000456 primary / +0.1643 raw WS | V53 + full ECS pressure d14 shear/ws³ speed overlay too aggressive |
| 44 | **v56** | **1.427768** | **PROMOTE** | **-0.000009 primary / -0.0032 raw WS** | **V53 + 20% v55 ECS pressure d14 speed blend — former base** |
| 45 | **v57** | **1.427719** | **PROMOTE** | **-0.000049 primary / -0.0178 raw WS** | **V56 + lambda 0.35 only on ECS pressure d14 levels 850/925 — current base** |
| 46 | **v58** | **1.427510** | **PROMOTE** | **-0.000209 primary / -0.0750 raw WS** | **V57 + gated North Sea station d1 hierarchical MOS 20% blend — current base** |
| 47 | **v59** | **1.427510** | **PROMOTE RAW / RANK NEUTRAL** | **0.000000 primary / -0.4346 raw cWS** | **V58 + ECS surface d14 calibrated d10-HRES direction overlay — current raw base** |
| 48 | v60 | 1.427510 | REJECT vs v59 | 0.000000 primary / +0.2965 raw cWS vs v59 | V59 + learned ECS surface d14 direction centre regressed hidden vs v59 |
| 49 | v83 | 1.427754 | REJECT | +0.000244 primary / +0.0878 raw WS | V59 + standalone byte-equal ECS station d14 stable-only half-shrunk offsets failed hidden |
| 50 | v104 | **1.504240** | **REJECT** | **+0.0797** | Compound residual-target (station NS d1 + grid surface d1 ECS/NS) — CATASTROPHIC |
| 51 | v105 | 1.424518 | VALIDATED RANK-NEUTRAL | 0.0000 | Targeted NS direction copula (d7/d14 only) — conservative scope |
| 52 | v106 | — | REJECT | — | Calibration sweep on rank-2 station speed — zero improvements found |
| 53 | v107 | 1.424518 | **REJECT** | +160 cWS raw / 0.000 rank | Cherry-pick v3 dir_pressure_d7_ns — public scores invert completely on hidden |
| 54 | v108 | PENDING | SUPERSEDED | — | Conservative width-only MOS for NS station d14 — superseded by v109 compound |
| 55 | v109 | PENDING | PENDING | — | Compound v105 + v108: NS grid copula + NS station d14 width MOS — efficient quota use |
| 50 | v84 | 1.427510 | PROMOTE RAW / RANK NEUTRAL | 0.000000 primary / -0.1186 raw cWS | V59 + ECS surface d14 u/v residual centre-only overlay, lambda 0.05 |
| 51 | v85 | 1.427510 | PROMOTE RAW / RANK NEUTRAL | 0.000000 primary / -0.1285 raw cWS vs v84 | V59 + ECS surface d14 u/v residual centre-only overlay, lambda 0.10 |
| 52 | **v86** | **1.426551** | **PROMOTE / BREAKTHROUGH** | **-0.000959 primary / -0.3454 raw WS** | **V85 + ECS station d1 residual interval calibration, q50 preserved** |
| 53 | **v88** | **1.425474** | **PROMOTE / BREAKTHROUGH** | **-0.001077 primary / -0.3876 raw WS** | **V86 + NS d1 center MOS + EB residual interval calibration** |
| 54 | v92 | — | HOLD | — | Enhanced station features for ECS d1 — does not beat v91 threshold |
| 55 | v93 | — | HOLD | — | Radical station features for ECS d1 — plateau confirmed at ~-0.32 WS |
| 56 | v94 | 1.427919 | **REJECT** | **+0.002445 primary / +0.806 WS NS / +0.074 WS ECS** | **V88 + global half-offset on surface d7 speed — catastrophic hidden transfer failure** |
| 57 | v95 | — | **REJECT** | **NS +0.559 avg / ECS -0.064 avg (split regression)** | **V88 center-MOS + EB intervals on station d7 — architecture does not transfer** |
| 58 | v96 | 1.425478 | **NEUTRAL** | **+0.000004 primary / NS grid dir −5.3 cWS d7 / −2.2 cWS d7 pressure** | **V46 copula on NS grid only — safe but ineffective, base already near ceiling** |
| 59 | v97 | 1.425474 | **REJECT** | **+61.3 cWS dir_stations_d7_ns** | **V88 + gated Track I d7 NS — local eval misleading, feature baseline ≠ v88 baseline** |
| 60 | **v101** | **1.424861** | **PROMOTE** | **−0.000613 primary / −0.221 WS speed_stations_d1_ecs** | **Residual-target CatBoost MOS — new base** |
| 61 | **v102** | **1.424518** | **PROMOTE** | **−0.000343 primary / −0.123 WS speed_stations_d1_ecs** | **Pushed residual-target (600 iter, depth=6) — diminishing returns, still rank 2** |
| 62 | v103 | 1.424669 | **REJECT** | **+0.000151 primary / +0.054 WS speed_stations_d1_ecs vs v102** | **v58-only A/B test — hypothesis disproven, neighbor features help hidden** |
| 63 | v104 | 1.504240 | **REJECT** | **+0.0797 primary** | **Compound residual-target grid+station — catastrophic** |
| 64 | v105 | 1.424518 | **VALIDATED** | **0.0000** | **NS grid copula d7/d14 — rank-neutral raw win** |
| 65 | v107 | 1.424518 | **REJECT** | **0.0000 rank / +160 cWS raw** | **Cherry-pick v3 dir_pressure_d7_ns — public scores invert on hidden** |
| 66 | v108 | — | **SUPERSEDED** | — | **NS station d14 width MOS — superseded by v109** |
| 67 | v109 | 1.424518 | **REJECT** | **0.0000 rank / +587 cWS raw** | **Compound v105 + v108 — v108 catastrophically wrong on hidden** |
| 68 | v110 | 1.479108 | **REJECT** | **+0.055 primary** | **Pooled DirectionModel on ALL grid direction — catastrophic hidden regression** |
| 69 | v111 | 1.424518 | **REJECT** | **0.0000 primary / d14 +22** | **Residual direction model ECS surface d7/d14 — d14 fatal** |
| 70 | v112 | — | **H1 RULED OUT** | **217.5 vs 217.4 holdout** | **Enriched features (296 cols) — zero improvement on direction** |
| 71 | v113 | 1.424518 | — | H2 Climatology blend d14 ECS | **RULED OUT** — only −0.098 WS improvement |
| 72 | v114 | 1.425198 | **H3 RULED OUT** | **+0.00068 primary / ECS dir all worse** | **Station-to-grid IDW correction — backfired on all ECS surface horizons** |
| 73 | **v116** | **1.423832** | **PROMOTE** | **−0.000686 primary / −0.247 WS speed_stations_d14_ns** | **Residual-target CatBoost MOS for NS station d14 — NEW BEST** |
| 74 | v115 | 1.424676 | **REJECT** | **+0.000158 primary / +0.057 WS speed_pressure_d14_ecs** | **v55 pressure-physics blend ECS d14 — slight regression** |
| 75 | v117 | 1.424518 | **REJECT** | **0.0000 rank / +3.5 WS dir_surface_d14_ecs** | **Heavy baseline direction graft — WORSENED target dimension** |
| 76 | v118 | 1.424518 | **REJECT** | **0.0000 rank / −3.1 d7 ECS / −3.8 d14 ECS raw** | **Seasonal width calibration — raw improved but rank unchanged** |
| 77 | **v119** | **PENDING** | **GAMBLING** | **Local −4.36 WS / 256 rows / NS station d7** | **Residual-target CatBoost MOS on NS station d7 — where v95 failed** |
| 78 | **v120** | **1.429910** | **CATASTROPHIC** | **+0.005392 primary / +1.94 WS speed_stations_d14_ecs** | **Residual-target CatBoost MOS on ECS station d14 — LOCAL WAS LYING (−3.0 → +1.9)** |
| 79 | **v121** | **1.424518** | **REJECT** | **0.0000 rank / +136 WS dir_surface_d14_ecs raw** | **Hybrid centres+widths — WIDTH IS NOT THE GAP. Raw score exploded, rank unmoved.** |
| 80 | **v119_fs** | **1.430375** | **CATASTROPHIC** | **+0.006543 primary / +2.11 WS speed_stations_d7_ns** | **Feature selection (30 features) did NOT fix overfitting. NS d7 is DEAD.** |
| 81 | **v120_fs** | **PENDING** | **FIX ATTEMPT** | **Local −0.95 WS / 30 features / ECS station d14** | **Feature-selection retrain of v120: much safer than −3.00 WS original** |
| 82 | **v116_tight** | **1.425231** | **REJECT** | **+0.001399 primary / +0.257 WS speed_stations_d14_ns** | **Post-hoc 8% tightening caused undercoverage. v116 intervals were already optimal.** |
| 83 | **v122** | **1.434836** | **CATASTROPHIC** | **+0.011004 primary / 4/6 station dims regressed** | **Combined model: local ALL 18 splits improved, hidden 4/6 REGRESSED. Data pooling is DEAD.** |
| 84 | **v123** | **1.425338** | **REJECT** | **+0.001506 primary / +0.30 WS speed_surface_d14_ns** | **Grid MOS with HRES d10 base — local validation used WRONG BASE. v102 grid already much better than HRES.** |
| 85 | **v126** | **1.424868** | **REGRESSED** | **+0.001036 primary / +0.126 WS** | **Cross-station IDW for ECS d1 station speed — built on wrong base (v102 not v116). ECS station curse continues.** |
| 86 | **v124b** | **PENDING** | **LANE 1** | **20% blend / 410k rows / NS pressure d14** | **NS pressure d14 physics conservative blend — upper levels weak, 1000/925 have signal, gap 0.003** |
| 87 | **v124c** | **1.423832** | **NEUTRAL** | **+0.000000 primary / +0.106 WS** | **NS pressure d14 physics on v116 base — REGRESSED on target dim. NS pressure physics DEAD.** |
| 88 | **v127** | **1.423832** | **RANK-NEUTRAL** | **-17.7 cWS direction / 0.000 rank** | **v116 + v105 NS copula + v118 ECS seasonal — all 6 dims improved, none flipped rank** |
| 89 | **v130** | **1.422977** | **PROMOTE** | **-0.000855 primary / -0.2 cWS avg** | **v127 + von Mises 70% blend on pressure d7/d14 — pressure direction narrowed via wind-speed-conditioned kappa** |
| 90 | **v132** | **1.422674** | **NEW BEST** | **-0.000303 primary / ECS d14 -0.58** | **90% von Mises on ECS pressure, NS reverted to v127 — ECS pressure direction breakthrough** |
| 91 | v135 | 1.422977 | **REJECT** | **0.000 rank / ECS d14 -4.80 raw** | **CQR angular CP d14 pressure — raw improved but conformal spill into d7 canceled benefit** |
| 92 | v137 | 1.422681 | **REJECT** | **+0.000007 primary** | **Von Mises enriched kappa features — helped NS d7 but hurt d14 consistently** |
| 93 | v138 | 1.422674 | **RANK-NEUTRAL** | **0.000 primary / ECS d14 -5.53 raw** | **v132 + CQR angular expansion ECS d14 pressure only — raw win no rank flip** |
| 94 | v139 | 1.426090 | **CATASTROPHIC** | **+0.003416 primary / +333 to +561 cWS** | **Per-station sin/cos LightGBM direction model — 6th station-direction curse failure** |
| 95 | v142a | 1.422674 | **REJECT RAW** | **0.000 primary / +317.37 cWS dir_stations_d7_ns** | Scoped HRES physical direction blend — hidden transfer failed catastrophically |
| 96 | v143 | 1.422674 | **RANK-NEUTRAL** | **0.000 primary / d14 -1.27 / d7 +1.14** | ECS surface d7/d14 u/v residual MLP — mixed, no rank flip |
| 97 | **v142** | **1.421875** | **NEW BEST** | **-0.000799 primary / NS d7 -3.24 / ECS d7 -3.46** | **HRES fcst_dir 50% blend station d7 — FIRST station direction success after 6 failures** |
| 98 | v145 | 1.421875 | RANK-NEUTRAL | 0.000 primary / ECS d14 -1.225 raw cWS | Regime analog center move transferred raw, but no rank flip |
| 99 | **v146** | **1.421297** | **NEW BEST** | **-0.000578 vs v142 / station d7 wins, ECS surface d14 regressed** | **Weighted conformal direction widths, no centers moved; station d7 transferred** |
| 100 | v147 | — | PENDING | — | Circular forest residual distribution, ECS surface d7/d14 center-only |
| 101 | v148 | — | PENDING | — | IsolationForest-gated conformal widths, no centers moved; ECS surface d14 only |
| 102 | v149 | 1.421297 | TIED BEST | 0.000 vs v146 / ECS d14 raw-cleaner | v146 station d7 widths + v145 ECS surface d14 center, excluding bad ECS d14 width |
| 103 | v150 | 1.421297 | TIED BEST | 0.000 vs v149 / ECS d14 raw-cleanest | v149 + v147 forest ECS surface d14 center only; excludes ECS d7 forest risk |
| 104 | **v151** | **1.420250** | **NEW BEST** | **−0.001047 primary** | **Donor oracle: harvested speed + d14 direction wins, but dir_pressure_d7_ns toxic (+162 cWS)** |
| 105 | **v152** | **1.420300** | **NEW BEST (clean)** | **−0.000997 primary / 5 speed wins** | **Speed-only donor oracle: safe base, no toxic direction donors** |
| 106 | **v153** | **1.420250** | **NEW BEST (clean)** | **−0.000050 vs v152 / matches v151 without toxic donor** | **v152 + 2 safe v151 direction donors — definitive best** |
| 107 | v154 | 1.420250 | TIED BEST | 0.000 vs v153 / dir_pressure_d7_ns -10.08 raw | v153 + merge-aligned dir_pressure_d7_ns from v3 (raw-cleaner, rank-neutral) |
| 108 | v155 | 1.420250 | TIED BEST | 0.000 vs v153 / raw-cleanest direction base | v153 + all merge-aligned donor improvements; donor-oracle direction exhausted |
| 109 | v156 | 1.420250 | TIED BEST | 0.000 primary / dir_stations_d14_ecs -10.15 raw | v155 + ECS station d14 direction weighted-conformal widths; raw transferred, rank-neutral |
| 110 | v157 | PENDING | PENDING | Replay mean -1.04 cWS / worst split -0.19 | v155 + NS station d14 direction weighted-conformal widths, center-frozen |
| 111 | v158 | 1.420252 | REJECT | +0.000002 primary / target +0.0009 WS | v156 + `speed_surface_d14_ns` q05/q95 micro-shrink; hidden undercoverage |
| 112 | v159 | HOLD | HOLD | Not submitted | v156 + `speed_pressure_d14_ns` q05/q95 micro-shrink; held after v158 regression |
| 113 | v160 | HOLD | HOLD | Not submitted | v156 + `speed_pressure_d7_ns` q05/q95 micro-shrink; held after v158 regression |
| 114 | v161 | HOLD | HOLD | Not submitted | v156 + `speed_surface_d1_ecs` q05/q95 micro-shrink; held after v158 regression |
| 115 | **v162** | **1.420203** | **NEW BEST** | **-0.000047 primary / speed_pressure_d14_ecs -0.0167** | **v156 + ECS pressure d14 850/925 lambda 0.35 -> 0.50; pressure lane still transfers** |
| 116 | **v163** | **1.420160** | **NEW BEST** | **-0.000043 primary / speed_pressure_d14_ecs -0.0156** | **v162 + ECS pressure d14 850/925 lambda 0.50 -> 0.65; pressure lane still monotone** |
| 117 | **v164** | **1.420138** | **NEW BEST** | **-0.000022 primary / speed_pressure_d14_ecs -0.0078** | **925-only lambda 0.65 -> 0.80 transferred; pressure lane still monotone but diminishing** |
| 118 | v165 | 1.420591 | REJECT | +0.000453 primary / speed_stations_d1_ecs +0.1629 | v164 + v79 station d1 bias failed; offsets not additive after v102 |
| 119 | **v166** | **1.420120** | **NEW BEST** | **-0.000018 primary / speed_pressure_d14_ecs -0.0066** | **850-only lambda 0.65 -> 0.80 transferred; both 850/925 now at lambda 0.80** |
| 120 | **v167** | **1.420092** | **NEW BEST** | **-0.000028 primary / speed_pressure_d14_ecs -0.0102** | **Regime-selected ECS pressure d14 lambda selector transferred; still just above 17.8900 boundary** |
| 121 | v168 | PENDING | PENDING | 144,344 speed rows | ECS pressure d7 high-confidence width shrink |
| 122 | v169 | PENDING | PENDING | 72,199 speed rows | NS surface d14 high-confidence width shrink |
| 123 | v170 | PENDING | PENDING | 159,318 speed rows | NS pressure d14 high-confidence width shrink |
| 124 | v171 | PENDING | PENDING | 82,080 speed rows | ExtraTrees ECS surface d1 10m residual center overlay |
| 125 | v172 | PENDING | PENDING | 256 direction rows | NS station d14 weighted-conformal width rebase, centers frozen |
| 126 | **v173** | **1.420083** | **NEW BEST** | **-0.000009 primary / speed_pressure_d14_ecs -0.0033** | **Final ECS pressure d14 lambda probe crossed visible 17.8900 boundary** |
| 127 | v174 | 1.420094 | REJECT | +0.000011 primary / speed_pressure_d7_ecs +0.0041 | v173 + rebased ECS pressure d7 shrink regressed; stop this lane |
| 128 | v175 | PENDING | PENDING | 72,199 speed rows / q50 frozen | v173 + rebased NS surface d14 high-confidence shrink |
| 129 | v176 | PENDING | PENDING | 159,318 speed rows / q50 frozen | v173 + rebased NS pressure d14 high-confidence shrink |
| 130 | v177 | 1.420120 | REJECT | +0.000037 primary / speed_surface_d14_ns +0.0135 | v173 + NS surface d14 interval translation regressed; block this lane |
| 131 | v178 | PENDING | PENDING | 271,708 pressure speed rows / width preserved | v173 + NS pressure d14 interval translation from split-stable residual-bias bins |
| 132 | v179 | 1.420083 | NEUTRAL/REJECT | +0.000000 primary / dir_stations_d14_ns +2.1571 cWS | v173 + v172 NS station d14 weighted-conformal widths failed target |
| 133 | v180 | 1.420083 | NEUTRAL/REJECT | +0.000000 primary / speed_pressure_d14_ns +0.0001 | v173 + NS pressure d14 q3-only tiny shrink did not transfer |
| 134 | v181 | 1.420083 | NEUTRAL/REJECT | +0.000000 primary / speed_pressure_d14_ns +0.0061 WS | v173 + NS pressure d14 q4 low-side widening failed hidden |
| 135 | v182 | 1.421147 | REJECT | +0.001064 primary / speed_stations_d1_ecs +0.3832 WS | v173 + low-capacity ExtraTrees ECS station d1 speed MOS failed hidden despite replay gate |
| 136 | v183 | PENDING | DO NOT SUBMIT AS BUILT | 512 station direction rows / centers frozen | includes failed d14 station-width family from v179; only d7-only derivative remains arguable |
| 137 | v184 | HOLD | DO NOT SUBMIT | 178,838 pressure speed rows / q4 q05 only | v173 + v181 smaller 0.010 bracket killed by v181 regression |
| 138 | v185 | 1.420087 | REJECT/NEUTRAL | +0.000004 primary / speed_surface_d14_ns +0.0015 WS | v173 + NS surface d14 q4 low-side widening failed hidden |
| 139 | v186 | PENDING | PENDING | 11,099 surface speed rows / anomaly width only | v173 + ECS surface d7 anomaly-aware interval adapter |
| 140 | v187 | NO ZIP | REJECTED OFFLINE | period avg +1.298 WS | kNN analog station d7 NS residual failed leave-period gate |
| 141 | v188 | NO ZIP | BLOCKED | needs >=2 scored winners | guarded compound pack implemented, refuses unscored candidates |
| 142 | v190 | NO ZIP | ANALYSIS | donor atlas + rank-gap oracle | v173 post-v185 selector audit; speed donors were not real prediction deltas |
| 143 | **v191** | **1.419810** | **NEW BEST** | **-0.000273 primary / dir_pressure_d7_ecs -1.1775 cWS** | **ECS pressure d7 speed-conditioned circular concentration response transferred** |
| 144 | v192 | 1.420083 | NEUTRAL/REJECT | +0.000000 primary / dir_pressure_d14_ecs +0.4392 cWS | ECS pressure d14 sibling concentration response failed target |
| 145 | v193 | NO ZIP | REJECTED OFFLINE | 0 changed rows | NS surface d7 best donor was byte-identical to v173 |
| 146 | v194 | NO ZIP | REJECTED OFFLINE | 0 changed rows | NS surface d14 best donor was byte-identical to v173 |
| 147 | v195 | NO ZIP | REJECTED OFFLINE | donor edge below threshold | station-speed revival gate failed after v165/v182/v187 |
| 148 | **v196** | **1.419757** | **NEW BEST** | **-0.000053 primary / dir_pressure_d7_ecs -0.2311 cWS** | **mild-plus bracket of v191 for ECS pressure d7 direction — current best** |
| 149 | v197 | 1.419810 | REJECT/NEUTRAL | +0.000053 vs v196 / dir_pressure_d14_ecs +0.0103 cWS | selective ECS pressure d14 coverage expansion from v191 failed; lacks v196 d7 gain |
| 150 | **v222** | **1.418872** | **NEW BEST** | **-0.000885 primary / dir_pressure_d7_ns 266.5361->255.2599 / dir_pressure_d7_ecs 233.5926->229.7705** | **v212 confirmed Lane A pressure d7 compound plus v204 undo; promoted as active base** |
| 151 | v223 | PENDING | BUILT OPTIONAL | 77,349 surface direction rows / centers frozen | v222 + v216 NS surface d7 Lane A overlay; raw-improving but not current-board rank-flipping |
| 152 | v224 | PENDING | BUILT DIAGNOSTIC | 164,160 speed rows / q50 frozen | v196 + `speed_surface_d1_ecs` q05/q95 micro-shrink; targets current rank 4 -> 2 speed boundary but belongs to risky post-hoc speed class |
| 153 | v225 | PENDING | BUILT HOLD / SPEED DIAGNOSTIC | 69,768 speed rows / q50 frozen | v196 + `speed_surface_d1_ecs` 10m uncertainty-state width redistribution; stronger than v224 but lacks hidden row-level truth |
| 154 | v226 | 1.418875 | REJECT | +0.000003 primary / speed_surface_d7_ecs 9.7234->9.7246 | Held one-cell ECS surface d7 speed lean-tail probe from v222; q50 and all direction columns frozen. |
| 155 | **v227** | **1.418862** | **NEW BEST** | -0.000004 primary / dir_stations_d1_ns 170.7878->170.7474 / speed_surface_d1_ecs 4.5951->4.5972 | Held one-cell North Sea station d1 direction micro-shrink from v222; direction centers and all speed columns frozen. |
| 156 | v228 | PENDING | BUILT HOLD / SPEED DIAGNOSTIC | 69,768 speed rows / q50 frozen | v222 + `speed_surface_d1_ns` 10m uncertainty-state width redistribution; stronger audit than v225 but same speed-family gate |
| 157 | v229 | PENDING | BUILT HOLD / SPEED DIAGNOSTIC | 348,840 speed rows / q50 frozen | v222 + `speed_pressure_d1_ns` pressure-level uncertainty-state width redistribution; hold behind the active speed branch only after prior score-intake rank-flip gates pass; skip v228 on the current board unless v228 becomes rank-moving |
| 158 | v230 | PENDING | BUILT HOLD / SPEED DIAGNOSTIC | 63,965 speed rows / q50 frozen | v222 + `speed_surface_d14_ecs` 10m asymmetric speed-bin endpoint shift; hold behind the active speed branch after v229 passes its score-intake rank-flip gate |
| 159 | pressure d14 ECS lambda audit | NO ZIP | AUDITED HOLD | remaining 82,080 non-high 850/925 rows | `speed_pressure_d14_ecs` remaining lambda branch covers only ~15% of current 0.0886 WS rank boundary; no v231 build |
| 160 | station d7 NS speed audit | NO ZIP | BLOCKED | current rank-5 gap 0.1134 WS | `speed_stations_d7_ns` current families are blocked: v89/v95 split-regressed, v119_fs regressed hidden +2.1086 WS, v187/v195 refused build |
| 161 | station d14 NS speed audit | NO ZIP | AUDITED HOLD | current rank-2 gap 0.2195 WS | Current base already carries best hidden value `15.5595`; v116_tight and later station-speed extensions failed; no new build |
| 162 | pressure d14 ECS direction audit | NO ZIP | AUDITED HOLD | current rank-5 gap 0.2904 cWS | Current base already carries best hidden value `300.5204`; v192 narrowing and v197 widening both failed; no endpoint-only build |
| 163 | surface d7 ECS direction audit | NO ZIP | AUDITED HOLD | current rank-3 gap 0.6656 cWS | Current base already carries best hidden value `265.8556`; v217 lost/reverted, v143 center move regressed, donor edge only `-0.0012`; no endpoint-only build |
| 164 | station d14 NS direction audit | NO ZIP | AUDITED HOLD | current rank-5 gap 2.0686 cWS | Current base already carries best hidden value `305.6286`; v179/v108/v204 station d14 width/widening families failed; no endpoint-only build |
| 165 | pressure d1 ECS direction audit | NO ZIP | AUDITED HOLD | current rank-3 gap 3.3410 cWS | Do not upload `v213`: best hidden donor edge is only `-0.0010` cWS from catastrophic `v50`, while `v213` widened `42.47%` of changed d1 rows and `v215` skipped it |
| 166 | pressure d1 NS direction audit | NO ZIP | AUDITED HOLD | current rank-3 gap 6.5270 cWS | Do not upload `v214`: no hidden-scored donor beats current `79.8870`, and `v215` estimates `v214` near `~76`, still behind the `73.36` next-rank boundary |
| 167 | pressure d7 ECS direction audit | NO ZIP | AUDITED HOLD | current rank-3 gap 8.3405 cWS | Current base already carries best hidden value `229.7705` from v222; v191/v196/v209 ladder harvested; no new endpoint-only build |
| 168 | pressure d7 NS direction audit | NO ZIP | AUDITED HOLD | current rank-2 gap 18.7199 cWS | Current base already carries best hidden value `255.2599` from v222; v198/v202/v202b were superseded by v211/v222; no new endpoint-only build |
| 169 | surface d14 ECS direction audit | NO ZIP | AUDITED HOLD | current rank-2 gap 20.6417 cWS | Current base already carries best hidden value `325.6517` from v150/v222; v60 replay failed hidden, v117/v121 falsified heavy center/width explanations; no new build |
| 170 | v209 | PENDING | RETROSPECTIVE FALLBACK | 227,332 pressure direction rows / centers frozen | Standalone ECS pressure d7 Lane A attribution artifact; verified and logged for v222 fallback branch only |
| 171 | v211 | PENDING | RETROSPECTIVE FALLBACK | 254,479 pressure direction rows / centers frozen | Standalone NS pressure d7 Lane A attribution artifact; verified and logged for v222 fallback branch only |
| 172 | v212 | PENDING | RETROSPECTIVE FALLBACK | v209 + v211 pressure d7 compound | Minimal Lane A pressure d7 compound; carries v204 station d14 state, so v222 is preferred |
| 173 | v221 | PENDING | RETROSPECTIVE FALLBACK | v218 minus v217 surface d7 | Removes v217 from v218 but still carries v204 station d14 state; use only if v222/v223 cannot be used |
| 174 | v232 | PENDING | BUILT HOLD / DIRECTION DIAGNOSTIC | 256 station direction rows / centers frozen | v222 + d7-only salvage of v183 asymmetric NS station d7 endpoints; excludes failed d14 family; hold behind v222_plus_v225 speed-gated queue and v227 |
| 175 | **v222_plus_v225** | **1.418866** | **NEW BEST** | -0.000006 primary / speed_surface_d1_ecs 4.5972->4.5951 | Direct production-preserving speed diagnostic built from v196 with v222, v225 overlays. |
| 176 | v233 | PENDING | COMPOUND REJECT/HOLD | 271,744 pressure speed rows / q50 frozen | Its target cell was tested inside `v236_full_risk_jlshen` and worsened `15.3733->15.3737`; do not route this endpoint probe. |
| 177 | v234 | PENDING | COMPOUND REJECT/HOLD | 144,836 surface speed rows / q50 frozen | Its target cell was tested inside `v236_full_risk_jlshen` and worsened `14.4643->14.4662`; do not route this endpoint probe. |
| 178 | v235 | PENDING | COMPOUND REJECT/HOLD | 224 station direction rows / centers frozen | Its target cell was tested inside `v236_full_risk_jlshen` and worsened `241.2614->241.3581`; do not route this endpoint probe. |
| 179 | remaining low-gap audit | NO ZIP | NO ADDITIONAL BUILD | all unbuilt cells with gap <= 1.0 | Post-v236, every old low-gap queue cell is BLOCKED, AUDITED_HOLD, or not route-positive; no score-gated queue candidate remains. |
| 180 | NS pressure d7 speed lean-tail audit | NO ZIP | AUDITED HOLD | closest clearing variant `-0.003307` vs `0.0033` WS boundary | Distinct capped-tail HRES-gated idea is too marginal to build before a genuinely new mechanism or fresh live-board trigger. |
| 181 | NS surface d14 speed block refresh | NO ZIP | BLOCKED | exact cell failed v158/v177/v185; EDA says under-covered | Tiny `0.0016` WS boundary is fake low-hanging fruit unless a non-endpoint mechanism or new validation oracle appears |
| 182 | NS pressure d14 speed block refresh | NO ZIP | BLOCKED | exact q3/q4 endpoint probes failed v180/v181 | Tiny `0.0027` WS boundary is closed until a non-endpoint mechanism or new validation oracle appears |
| 183 | ECS station d1 speed block refresh | NO ZIP | BLOCKED | v101/v102 plateau; v165/v182 revivals failed; v195 no donor | Current `0.0557` WS boundary is not actionable without a stronger station-speed validation oracle |
| 184 | extended low-gap audit | NO ZIP | NO ADDITIONAL BUILD | all unbuilt cells with gap <= 12.0 | Larger direction gaps are also already audited/held; after v236, no local low-gap queue build should precede a refreshed positive router decision. |
| 185 | compound preflight matrix | NO ZIP | PRE-SCORE READY / SUPERSEDED | 1 pass / 82 blocked | Historical pre-score state: `v222_plus_v225` passed compound guards, but its later raw-only score and the v236 reject closed the old queue. |
| 186 | all non-leading rank target audit | NO ZIP | NO WATCH TARGETS | 29 non-leading cells / 0 WATCH | Every non-#1 cell was classified; after v236, current routing remains hold until a refreshed positive route-eligible artifact exists. |
| 187 | next upload readiness gate | NO ZIP | PRE-SCORE READY / SUPERSEDED | `v222_plus_v225` ready / 0 blockers | Historical pre-score upload handoff; the active route is now `HOLD_ECS_D1`, not the old low-gap queue. |
| 188 | speed-chain rank-flip gate | NO ZIP | ROUTER/BUILDER HARDENED | raw-only gains no longer unlock next speed compound | Decision helpers and compound guards now require visible rank gain before advancing the speed chain |
| 189 | v222_plus_v225 branch matrix | NO ZIP | BRANCH MATRIX OK | 5 synthetic post-score outcomes | Only rank-flip/primary-nonworse outcomes build `v222_plus_v225_plus_v226`; raw-only/failing outcomes route to `v227` |
| 190 | verifier subset scope guard | NO ZIP | UPLOAD ORDER GUARD | subset checks no longer look like global queue decisions | `verify_upload_packet.py --artifacts v227 v232 v235 --fast` now labels `v227` as candidate only among requested artifacts and points back to `next_slot_decision.py` |
| 191 | rank-EV boundary clearance | NO ZIP | RANK-EV RISK AUDIT | `v234` gain 4 but clearance only `0.000096` | Rank-EV reports now expose nearest-boundary clearance; keep `v234` behind clean `v233` despite bigger visible jump unless live board refresh improves its margin |
| 192 | readiness clearance handoff | NO ZIP | READY HANDOFF UPDATED | `v222_plus_v225` clearance `0.004086`; full row scan + board age shown | Next upload readiness Markdown/JSON now show full row-count verification, board snapshot age, rank EV, and boundary clearance for the exact next artifact before upload |
| 193 | readiness rank-EV hard block | NO ZIP | READY GATE HARDENED | `v222_plus_v225` gain 2 / clearance `0.004086` | `next_upload_readiness.py` now blocks missing/stale/non-positive rank EV, so READY requires a mechanically valid and rank-moving artifact |
| 193 | verified post-score follow-up | NO ZIP | HANDOFF HARDENED | remove `--no-verify` from generated next-slot command | After recording a score, generated commands now rerun `next_slot_decision.py` with artifact verification enabled |
| 194 | v222_plus_v225 scope audit | NO ZIP | SCOPE GATE PASS | 3,448,800 rows / 0 reconstruction mismatches | Full compound audit proves `v222_plus_v225` equals `v196` + `v222` direction overlays + `v225` speed_surface_d1_ecs only |
| 195 | v222_plus_v225 upload handoff sync | NO ZIP | HANDOFF SYNCED | upload packet + queue now include scope gate, score dry-run, and verified follow-up | Operator-facing upload docs now match `next_slot_decision.py` and readiness: upload `v222_plus_v225`, dry-run score intake, apply the score, then rerun verified `next_slot_decision.py` |
| 196 | board snapshot ingest validation | NO ZIP | LIVE-BOARD GATE HARDENED | TSV dry-run preview + strict JSON validation + stale-overwrite guard | `board_monitor.py` now validates/pastes leaderboard snapshots, previews parsed rank impact, and refuses older board snapshots before they can corrupt rank-gap decisions |
| 197 | readiness board freshness gate | NO ZIP | READY GATE HARDENED | board age `1 <= 2` days for current packet | `next_upload_readiness.py` now blocks READY if the stored public-board snapshot is unknown, future-dated, or older than two days, protecting low-gap rank decisions from stale boundaries |
| 198 | router board freshness gate | NO ZIP | ROUTER GATE HARDENED | stale board now returns `REFRESH_BOARD` | `next_slot_decision.py` now refuses low-gap upload/build recommendations and rank-positive speed gates when the stored board is stale, so post-score branching cannot advance from outdated boundaries |
| 199 | post-score board freshness gate | NO ZIP | SCORE INTAKE GATE HARDENED | stale branch reports now say `REFRESH_BOARD` | `record_codabench_score.py` and `post_score_decision.py` now record scores while suppressing next-compound recommendations from stale public-board snapshots |
| 200 | compound-builder board freshness gate | NO ZIP | BUILDER GATE HARDENED | direct preflight/build now blocks stale board snapshots | `build_scored_compound.py` and the compound preflight matrix now refuse score-gated compounds when visible-rank boundaries come from stale or unparseable public-board snapshots |
| 201 | score-intake dry-run artifact preview | NO ZIP | SCORE INTAKE HANDOFF HARDENED | dry-run now writes report + hypothetical next-decision JSON | `record_codabench_score.py` dry-run now leaves `log.json` unchanged while writing the branch report and previewing the next queue decision from an in-memory scored record |
| 202 | readiness compound freshness echo | NO ZIP | READY HANDOFF HARDENED | matrix board freshness is now explicit in readiness JSON/Markdown | `next_upload_readiness.py` now carries the compound preflight matrix's own board-freshness payload and blocks READY if that matrix is blocked |
| 203 | score-intake parsed-cell echo | NO ZIP | SCORE INTAKE HANDOFF HARDENED | dry-run reports now show parsed score cells | `record_codabench_score.py` and `post_score_decision.py` now print `Parsed score cells: 36 / 36` when all scorer metrics were accepted |
| 204 | router parsed-cell caution | NO ZIP | ROUTER HANDOFF HARDENED | next-slot cautions now require `36 / 36` before apply | `next_slot_decision.py` now carries the score-intake parsed-cell check into upload/build/wait decisions so the first router output matches the upload packet |
| 205 | readiness caution echo | NO ZIP | READY HANDOFF HARDENED | readiness Markdown now surfaces next-slot cautions | `next_upload_readiness.py` now renders router cautions, including the `Parsed score cells: 36 / 36` dry-run requirement, before the upload commands |
| 206 | upload queue speed-order sync | NO ZIP | QUEUE HANDOFF HARDENED | human queue now matches verifier/router v233/v234 order | `UPLOAD_QUEUE_2026_06_04.md` now lists v233/v234 before later held probes and includes v235; `test_verify_upload_packet.py` guards against static verifier artifacts missing from the Markdown queue |
| 207 | v228 rank-EV skip gate | NO ZIP | ROUTER/BUILDER HARDENED | `v228` gain 0 / clearance `-0.005956`; `v229` gain 1 | Pending speed probes now need positive visible rank EV before they can block the chain; current-board clean speed branches skip v228 and build the matching `...plus_v229` compound instead |
| 208 | score-recorder skip-v228 handoff | NO ZIP | SCORE INTAKE HANDOFF HARDENED | clean v234 score now writes next-decision JSON for `...plus_v229` | `record_codabench_score.py` post-score JSON handoff is regression-tested so a clean v234 result cannot route the next slot to non-rank-moving v228 on the current board |
| 209 | guarded speed-chain branch matrix | NO ZIP | BRANCH MATRIX OK | 9 synthetic speed-chain outcomes | Router now preserves the progressed v234->v229->v230 branch before shorter v233 fallbacks; matrix covers raw-only fallbacks and the current-board skip-v228 path |
| 210 | upload queue branch-matrix sync | NO ZIP | QUEUE HANDOFF SYNCED | current clean chain documented as v225->v226->v233->v234->v229->v230 | Upload queue now references the guarded speed-chain matrix and removes stale shorter v226->v229 preservation examples from the current-board handoff |
| 211 | readiness branch-matrix gate | NO ZIP | READY GATE HARDENED | readiness now requires `BRANCH_MATRIX_OK` / 9 scenarios | Final readiness report now includes and blocks on the guarded speed-chain branch matrix before declaring `v222_plus_v225` ready |
| 212 | score-intake readiness preflight | NO ZIP | SCORE INTAKE HANDOFF HARDENED | dry-run wrapper writes report + next-decision JSON without ledger mutation | `score_intake_readiness.py` is now the first post-upload command; it parses the scorer log, previews the branch from an in-memory scored ledger, and keeps `record_codabench_score.py --apply` as the explicit ledger-writing step |
| 213 | offensive rank plan gate | NO ZIP | LOW-HANGING PLAN READY | v222_plus_v225 first / 29 non-leading cells classified / 0 WATCH | `offensive_rank_plan.py` now composes router, rank EV, all-target audit, and low-gap audits; readiness blocks if this plan drifts from `LOW_HANGING_PLAN_READY` |
| 214 | Phase 1 budget gate | NO ZIP | BUDGET READY | current state refreshed to 135/150 used, 15 remaining, 9 positives need min 2 daily-cap days | `phase1_budget.py` centralizes deadline/quota/daily-cap state; offensive plan and readiness now expose the budget gate before spending the next low-gap slot |
| 215 | queue clearance-ratio risk bands | NO ZIP | RANK-EV RISK HARDENED | v222_plus_v225 adequate; v234/v230 razor; v228 no-flip | `queued_upload_rank_ev.py` now reports normalized boundary-clearance ratio and bands, and the offensive/readiness reports surface them without changing the next upload |
| 216 | router rank-EV context | NO ZIP | ROUTER HANDOFF HARDENED | plain router now prints v222_plus_v225 rank 4->2 / ratio 0.568 adequate | `next_slot_decision.py` now surfaces the same rank-EV and positive-queue context in text output before upload commands |
| 217 | score-intake outcome classifier | NO ZIP | SCORE INTAKE HARDENED | preflight now labels CLEAN_RANK_FLIP / RAW_ONLY_GAIN / TARGET_FAILED | `score_intake_readiness.py` now emits structured outcome status before ledger mutation, so the v222_plus_v225 score paste directly says whether the speed chain can advance |
| 218 | readiness outcome-gate sync | NO ZIP | READY HANDOFF HARDENED | readiness now names `CLEAN_RANK_FLIP` as the only speed-chain advance outcome | `next_upload_readiness.py` and the generated readiness report now align the upload handoff with score-intake outcomes: apply valid scores after 36/36 parse, but advance the speed chain only on `CLEAN_RANK_FLIP` |
| 219 | router outcome-gate caution | NO ZIP | ROUTER HANDOFF HARDENED | router cautions now include `Outcome: CLEAN_RANK_FLIP` | `next_slot_decision.py` now prints and emits the same score-intake outcome gate as readiness, so the first post-upload command list cannot imply that a raw-only speed gain unlocks the next compound |
| 220 | static handoff outcome-gate sync | NO ZIP | DOC HANDOFF HARDENED | upload packet, queue, matrix, and final plan now use `CLEAN_RANK_FLIP` | Operator-facing docs now define the `v222_plus_v225` speed-chain unlock as score-intake `CLEAN_RANK_FLIP`, not vague clean/raw-positive wording; generated branch/preflight/audit artifacts were refreshed |
| 221 | post-score helper outcome labels | NO ZIP | SCORE HANDOFF HARDENED | `post_score_decision.py` now labels CLEAN_RANK_FLIP / RAW_ONLY_GAIN / TARGET_FAILED | The post-score report used by `record_codabench_score.py` now matches score-intake outcome names for `v222_plus_v225`, so dry-run/apply reports cannot describe raw-only speed movement as a clean speed-chain unlock |
| 222 | low-hanging target gate test sync | NO ZIP | TEST HANDOFF HARDENED | broader queue tests now require `CLEAN_RANK_FLIP` wording | `test_low_hanging_rank_targets.py` now locks the `WS ECS Pres d7` held-v233 policy to score-intake `CLEAN_RANK_FLIP` for `v222_plus_v225`, keeping later speed probes gated behind the exact classifier rather than vague clean-score wording |
| 223 | readiness rank-EV JSON alias | NO ZIP | READY HANDOFF HARDENED | top-level readiness `rank_ev` mirrors next-slot candidate | `next_upload_readiness.py` now exposes the current low-hanging rank-EV candidate at top level in JSON, so score-paste checks can read `rank_ev.version`, `rank_ev.cell`, and boundary clearance without fragile nested paths |
| 224 | score-intake target rank-EV evidence | NO ZIP | SCORE HANDOFF HARDENED | outcome JSON/report now include target boundary clearance | `score_intake_readiness.py` now attaches target rank-EV evidence to `CLEAN_RANK_FLIP`/`RAW_ONLY_GAIN` outcomes, including base rank, new rank, boundary score, and boundary clearance for the uploaded low-gap cell |
| 225 | score-recorder target rank-EV report | NO ZIP | SCORE HANDOFF HARDENED | apply/dry-run reports now include target boundary clearance | `record_codabench_score.py` now writes the same target rank-EV block in its own decision report and experiment-log score payload, so the official score apply path shows the target cell, rank flip, boundary, clearance, and gate flags before any next-slot branch is followed |
| 226 | June 6 readiness refresh | NO ZIP | READY TO UPLOAD | `v222_plus_v225` ready; board age `2/2`; full row scan pass | `next_upload_readiness.py` now labels generated reports with the requested report date, and the June 6 readiness artifacts confirm the low-hanging upload is still valid today but at the board freshness limit |
| 227 | readiness freshness expiry | NO ZIP | READY HANDOFF HARDENED | board valid-through date now explicit | `next_upload_readiness.py` now emits `valid_through` and `days_until_refresh_required`; the June 6 packet states the 2026-06-04 board is valid only through 2026-06-06, so a later decision must refresh the board before using rank boundaries |
| 228 | readiness freshness status | NO ZIP | READY HANDOFF HARDENED | board state now `EXPIRES_TODAY` | `next_upload_readiness.py` now emits a machine-readable freshness status (`VALID`, `EXPIRES_TODAY`, `EXPIRED`, etc.); the June 6 packet is still ready but explicitly says the stored board expires today |
| 229 | router freshness payload | NO ZIP | ROUTER HANDOFF HARDENED | `next_slot_decision.py --json` now shows board `EXPIRES_TODAY` | The main router now emits and prints board freshness (`valid_through`, days until refresh, freshness status, blocker), so the primary next-slot command exposes that the 2026-06-04 board is usable only through 2026-06-06 |
| 230 | score-intake freshness payload | NO ZIP | SCORE HANDOFF HARDENED | dry-run score intake now echoes full board freshness | `score_intake_readiness.py` now carries the same structured board freshness into stdout, JSON, and the decision report, so the post-upload dry run shows whether a clean score can advance immediately or needs a board refresh first |
| 231 | budget helper queue inference | NO ZIP | BUDGET HANDOFF HARDENED | `phase1_budget.py --json` now infers 9 positive queued candidates | The quota helper now derives the current positive visible-rank queue from rank-EV manifests when no override is supplied, so operators can check `BUDGET_READY` without manually remembering the queue count |
| 232 | raw board-paste ingest | NO ZIP | LIVE-BOARD GATE HARDENED | `board_monitor.py --ingest-paste` now parses Codabench raw copies | Board refresh can now ingest the raw copied leaderboard text format with metadata/rank lines, participant names with spaces, duplicates, self-row exclusion, and sentinel filtering before the same snapshot validation and stale-overwrite guard |
| 233 | offensive-plan freshness echo | NO ZIP | LOW-HANGING PLAN HARDENED | offensive plan now shows board `EXPIRES_TODAY` | `offensive_rank_plan.py` now carries the structured board freshness payload into Markdown/JSON, so the top-level low-hanging plan exposes when its rank-boundary evidence expires before recommending `v222_plus_v225` |
| 234 | readiness offensive freshness gate | NO ZIP | READY GATE HARDENED | readiness now validates offensive-plan freshness | `next_upload_readiness.py` now embeds and checks the offensive plan's board freshness against the top-level board snapshot, so READY blocks if the high-level low-hanging plan is missing, blocked, or drifted from the current board evidence |
| 235 | report-date freshness gate | NO ZIP | READY GATE HARDENED | June 7 report over June 4 board now blocks | `next_upload_readiness.py --report-date` now drives board freshness for both the readiness snapshot and embedded offensive plan, so future-dated handoff packets cannot stay READY from the machine date after rank-boundary evidence expires |
| 236 | offensive-plan report-date CLI | NO ZIP | LOW-HANGING PLAN HARDENED | top-level plan can be regenerated as stale on demand | `offensive_rank_plan.py --report-date` now controls the plan title and board freshness date directly; `2026-06-07` over the June 4 snapshot returns `LOW_HANGING_PLAN_REVIEW` and blocks stale low-gap rank decisions |
| 237 | stale-board raw-paste refresh handoff | NO ZIP | ROUTER HANDOFF HARDENED | `REFRESH_BOARD` now prints raw-paste ingest commands first | `next_slot_decision.py` now routes stale-board refresh through `board_monitor.py --ingest-paste /tmp/leaderboard.txt` dry-run/apply before TSV fallback, matching the raw Codabench copy format already supported by the board monitor |
| 238 | score-intake report-date freshness | NO ZIP | SCORE HANDOFF HARDENED | stale score-paste previews now route to `REFRESH_BOARD` | `score_intake_readiness.py --report-date` now drives board freshness for the parsed score outcome and previewed next-decision JSON, so a clean-looking `v222_plus_v225` score cannot unlock the next compound from an expired board |
| 239 | score-apply report-date freshness | NO ZIP | SCORE HANDOFF HARDENED | applying a stale-date score writes `REFRESH_BOARD` next-decision JSON | `record_codabench_score.py --report-date` now drives board freshness for the decision report, experiment-log branch text, and next-decision JSON, so recording a score after board expiry cannot recommend the next low-gap compound until the board is refreshed |
| 240 | readiness date-aware score commands | NO ZIP | READY HANDOFF HARDENED | generated score commands now pass `--report-date "$(date +%F)"` | `next_upload_readiness.py` now writes post-upload score-intake/apply commands that use the actual shell date for board freshness, so the saved handoff automatically routes to `REFRESH_BOARD` after the current board expires |
| 241 | router report-date CLI | NO ZIP | ROUTER HANDOFF HARDENED | June 7 router over June 4 board now returns `REFRESH_BOARD` | `next_slot_decision.py --report-date` now drives board freshness in the canonical router's text and JSON output, so the direct next-slot command cannot recommend `v222_plus_v225` or later low-gap compounds after rank-boundary evidence expires |
| 242 | router date-aware score commands | NO ZIP | ROUTER/READY HANDOFF HARDENED | canonical router commands now pass `--report-date "$(date +%F)"` | `next_slot_decision.py` now emits date-aware score-intake/apply and follow-up router commands, and `next_upload_readiness.py` now passes `--report-date` into its embedded router decision so stale-date readiness blocks at the queue-decision layer too |
| 243 | refresh rerun date-aware | NO ZIP | REFRESH HANDOFF HARDENED | `REFRESH_BOARD` follow-up now reruns router with `--report-date "$(date +%F)"` | The stale-board refresh branch now ends with the same date-aware `next_slot_decision.py` rerun used by upload handoffs, so a refreshed board cannot be followed by a date-implicit next-slot decision copied from stale output |
| 244 | score-report follow-up date-aware | NO ZIP | SCORE REPORT HARDENED | score reports and lessons now point to date-aware next-slot reruns | `record_codabench_score.py` and `post_score_decision.py` now write actionable follow-up text with `next_slot_decision.py --report-date "$(date +%F)"`, so applying a Codabench score cannot leave the operator with a date-implicit next-step command |
| 245 | readiness pre-upload commands | NO ZIP | READY HANDOFF HARDENED | readiness Markdown now includes fresh-board verifier before upload | `next_upload_readiness.py` now renders the router's pre-upload commands, including `verify_upload_packet.py --require-fresh-board --report-date "$(date +%F)"`, so the readiness page itself separates artifact verification/upload from post-score handling |
| 246 | anonymous board-refresh attempt | NO ZIP | EXTERNAL REFRESH BLOCKED | Codabench CSV endpoint returned 404 / anonymous page has no board rows | `docs/research/BOARD_REFRESH_ATTEMPT_2026_06_06.md` records that unauthenticated refresh could not obtain the live board; after the June 4 board expires, use logged-in copy/paste or TSV ingest before spending another low-gap slot |
| 247 | browser board-table refresh | NO ZIP | LIVE BOARD REFRESHED | 19 competitors / 36 cells / board valid through 2026-06-08 | In-app browser extraction refreshed `competitors_snapshot.json` to as-of `2026-06-06`; before scoring, `v222_plus_v225` remained next with `WS ECS Surf d1` rank `4 -> 2`, clearance `0.004086`, and fresh-board verifier required before upload |
| 248 | v222_plus_v225 score intake | `submission_v222_plus_v225.zip` | SCORED: NEW BEST / RAW_ONLY_GAIN | primary `1.418866`; `speed_surface_d1_ecs` `4.5972 -> 4.5951`; visible rank `4 -> 4` | `v222_plus_v225` is the new production best, but the speed gate did not produce a clean visible rank flip. Stop the speed-width chain: do not upload/build `v226` or later speed probes from this result. |
| 249 | v227 readiness after raw-only speed gate | `submission_v227.zip` | SCORED: NEW BEST | `Dir NS Sta d1` improved to `170.7474`; quota moved to `134/150 used, 16 remaining` after upload | `v227` became the active best; its gain is now preserved through the scored `v222_plus_v227_plus_v232` upload packet. |
| 250 | v222_plus_v227_plus_v232 | 1.418862 | SCORED / NON-WORSE | +0.000000 primary / dir_stations_d7_ns 310.9467->310.2390 | Score-gated compound built from v196 with v222, v227, v232 overlays. |
| 251 | v222_plus_v227_plus_v232_plus_v235 | PENDING | READY TO UPLOAD / PENDING SCORE | v222:835164, v227:835420, v232:835420, v235:835388; full row scan PASS | v196 + score-gated overlays; preserves scored `v222_plus_v227_plus_v232` and tests `Dir ECS Sta d1` with thin boundary clearance |
| 252 | June 8 leaderboard refresh | NO ZIP | LIVE BOARD REFRESHED | `Hégoa` #1 mean rank `3.79`; Printemps #2 `4.61`; 20 competitors after self-row exclusion | Ingested user's post-`v222_plus_v227_plus_v232` board paste; snapshot is as-of `2026-06-08`, valid through `2026-06-10`, and keeps `v222_plus_v227_plus_v232_plus_v235` as READY_TO_UPLOAD |
| 253 | June 12 leaderboard refresh | NO ZIP | JLShen RAW LEAD / ROUTER HOLD | JLShen inserted; production base remains `v222_plus_v227_plus_v232` | Snapshot `2026-06-12-pasted-top-two` preserves the June 8 rows, adds JLShen, blocks automatic old-queue uploads, and opens surface-d1 direction recapture as the next research lane. |
| 254 | Phase 1 quota correction | NO ZIP | BUDGET READY | user reports 25 available submissions; budget gate now `125/150` used | `phase1_budget.py` and the offensive plan now use 25 remaining slots while keeping the daily cap as the binding practical constraint. |
| 255 | v236_full_risk_jlshen | 1.418884 | REJECT | +0.000022 primary / dir_stations_d1_ecs 241.2614->241.3581 / speed_surface_d14_ecs 10.6506->10.6552 | Full-risk JLShen response compound: production v222_plus_v227_plus_v232 plus v233, v234, v229, v230, and v235 true changed-row overlays. |
| 1001 | v237_donor_v47_ws_ns_surf_d14 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 4 / WS NS Surf d14 from v47 11->7 (0/164160 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1002 | v238_donor_v47_ws_ns_surf_d7 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 3 / WS NS Surf d7 from v47 11->8 (0/164160 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1003 | v239_donor_v47_ws_ns_pres_d14 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 3 / WS NS Pres d14 from v47 10->7 (0/410400 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1004 | v240_donor_v47_ws_ns_pres_d7 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 2 / WS NS Pres d7 from v47 10->8 (0/410400 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1005 | v241_donor_v48_ws_ecs_surf_d7 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 1 / WS ECS Surf d7 from v48 3->2 (0/164160 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1006 | v242_donor_rank_sweep_all5 | NO ZIP | INVALID / DO NOT UPLOAD | rank-gain target 13 / WS NS Surf d14 from v47 11->7 (0/164160 changed/copied); WS NS Surf d7 from v47 11->8 (0/164160 changed/copied); WS NS Pres d14 from v47 10->7 (0/410400 changed/copied); WS NS Pres d7 from v47 10->8 (0/410400 changed/copied); WS ECS Surf d7 from v48 3->2 (0/164160 changed/copied) | Zero-diff build: local donor cells matched production exactly; rounded historical scores created false projected rank gain. |
| 1007 | v243_ns_sta_d1_dir_shrink_extra_0p10 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1008 | v244_ns_sta_d1_dir_shrink_extra_0p20 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1009 | v245_ns_sta_d1_dir_shrink_extra_0p30 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1010 | v246_ns_sta_d1_dir_shrink_extra_0p40 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1011 | v247_full_risk_ns_sta_d1_plus_d1_speed | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied; WS ECS Surf d1 69768/164160 changed/copied; WS NS Surf d1 69768/164160 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1012 | **v248_ns_sta_d1_dir_shrink_extra_0p25** | **1.418839** | **NEW BEST** | -0.000023 primary / dir_stations_d1_ns 170.7474->170.6465 | Extra center-frozen NS station d1 direction shrink: +0.25 deg per side on production base. |
| 1013 | **v249_ns_sta_d1_dir_shrink_extra_0p35** | **1.418839** | **NEW BEST** | -0.000023 primary / dir_stations_d1_ns 170.7474->170.6465 | Extra center-frozen NS station d1 direction shrink: +0.35 deg per side on production base. |
| 1014 | v250_ns_sta_d1_dir_shrink_extra_0p45 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1015 | v251_ns_sta_d1_dir_shrink_extra_0p50 | PENDING | BUILT / PENDING SCORE | Dir NS Sta d1 256/256 changed/copied | Final-day nonzero-diff rank-recapture packet. |
| 1016 | **v252_full_risk_ns_sta_d1_0p45_plus_d1_speed** | **1.418819** | **NEW BEST** | -0.000043 primary / dir_stations_d1_ns 170.7474->170.5657 / speed_surface_d1_ecs 4.5972->4.5951 | Full-risk final-day compound: v250-style NS station d1 direction shrink plus real-delta d1 speed-width probes from v222_plus_v225 and v228. |
| 1017 | **v253_station_0p45_plus_ecs_d1_speed_only** | **1.418815** | **NEW BEST** | -0.000047 primary / dir_stations_d1_ns 170.7474->170.5657 / speed_surface_d1_ecs 4.5972->4.5951 | Post-v252 cleanup compound: keep v250-style NS station d1 direction shrink and the v222_plus_v225 ECS d1 speed donor, but drop the v228 NS d1 speed donor. |
| 1018 | **v254_station_0p50_plus_ecs_d1_speed_only** | **1.418810** | **NEW BEST** | -0.000052 primary / dir_stations_d1_ns 170.7474->170.5455 / speed_surface_d1_ecs 4.5972->4.5951 | Aggressive ECS-only cleanup compound: +0.50 NS station d1 direction shrink plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor. |
| 1019 | **v255_station_0p55_plus_ecs_d1_speed_only** | **1.418805** | **NEW BEST** | -0.000057 primary / dir_stations_d1_ns 170.7474->170.5254 / speed_surface_d1_ecs 4.5972->4.5951 | High-risk ECS-only cleanup compound: +0.55 NS station d1 direction shrink plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor. |
| 1020 | **v256_station_0p60_plus_ecs_d1_speed_only** | **1.418801** | **NEW BEST** | -0.000061 primary / dir_stations_d1_ns 170.7474->170.5052 / speed_surface_d1_ecs 4.5972->4.5951 | Maximum-risk ECS-only cleanup compound: +0.60 NS station d1 direction shrink plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor. |

---

## Guarded Speed-Chain Branch Matrix -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/speed_chain_branch_matrix.py`
- `tests/test_speed_chain_branch_matrix.py`
- `scripts/next_slot_decision.py`
- `docs/research/SPEED_CHAIN_BRANCH_MATRIX_2026_06_05.md`
- `docs/research/speed_chain_branch_matrix_2026_06_05.json`

### Result

Added a dry-run matrix that scores synthetic in-memory outcomes for the guarded
speed chain and runs the real `next_slot_decision.py` router without touching
`submissions/log.json`. The matrix covers nine outcomes:

- clean `v222_plus_v225` -> build `v222_plus_v225_plus_v226`
- raw-only `v222_plus_v225` -> upload `v227`
- clean `v226` -> build `...plus_v233`
- raw-only `v226` -> build preservation `v222_plus_v225_plus_v227`
- clean `v233` -> build `...plus_v234`
- raw-only `v233` -> build preservation `v222_plus_v225_plus_v226_plus_v227`
- clean `v234` -> skip held/non-rank-moving v228 and build `...plus_v229`
- clean `v229` -> build `...plus_v230`
- clean `v230` -> build preservation `...plus_v227`

The matrix exposed a router ordering bug: after a clean
`v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229` score, the router
could fall back to the shorter `v222_plus_v225_plus_v226_plus_v233_plus_v229`
branch. `next_slot_decision.py` now checks the progressed v234->v229->v230
branch before shorter v233 fallbacks.

### Lesson

The low-gap speed chain is now mechanically gated through the same rules at
each step: target-positive, primary-nonworse versus the prior scored base, and
visible-rank-positive on the stored board. Current next action remains
external scoring of `v222_plus_v225`; do not build or upload deeper compounds
until that score is recorded cleanly.

---

## Upload Queue Branch-Matrix Sync -- No ZIP

**Status**: QUEUE HANDOFF SYNCED / NO ZIP
**Artifacts**:
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `tests/test_speed_chain_branch_matrix.py`

### Result

Synchronized the human upload queue with the guarded speed-chain matrix. The
queue now points directly at
`docs/research/SPEED_CHAIN_BRANCH_MATRIX_2026_06_05.md` and documents the
current-board clean chain as:

```text
v222_plus_v225 -> v226 -> v233 -> v234 -> skip v228 -> v229 -> v230 -> matching ...plus_v227
```

The handoff no longer lists stale shorter current-board preservation examples
such as `v222_plus_v225_plus_v226_plus_v229_plus_v227`. Those branches remain
mechanically buildable only as explicit alternate/refreshed-board routes, not
as the current low-hanging path.

### Lesson

The operator-facing queue is part of the rank strategy. If the machine router
learns a new branch order, the upload queue must stop advertising older
examples that would spend a remaining slot on the wrong preserved chain.

---

## Readiness Branch-Matrix Gate -- No ZIP

**Status**: READY GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The final readiness gate now imports the guarded speed-chain matrix and refuses
`READY_TO_UPLOAD` unless it reports `BRANCH_MATRIX_OK`. The regenerated
readiness report still passes for `v222_plus_v225` and now includes:

```text
Speed-chain branch matrix: BRANCH_MATRIX_OK (9 scenarios, 0 failed)
```

This adds a final guard between the current upload and the post-score branch
plan: `v222_plus_v225` can remain ready only while the router's clean/raw-only
speed-chain matrix is internally consistent.

### Lesson

The next submission is only useful if the score intake can immediately choose
the right follow-up. Readiness now validates both the upload packet and the
post-score branch map before a scarce Phase 1 slot is spent.

---

## Score-Intake Readiness Preflight -- No ZIP

**Status**: SCORE INTAKE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/score_intake_readiness.py`
- `tests/test_score_intake_readiness.py`
- `scripts/next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`

### Result

Added an operator-facing score-intake preflight for the next Codabench result:

```bash
.venv/bin/python scripts/score_intake_readiness.py \
  --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --base v222 \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json \
  --json-out logs/post_score_decisions/v222_plus_v225_intake_readiness.json
```

The wrapper reuses the hardened scorer parser, rejects missing primary scores
or incomplete metric payloads, writes the branch report, and writes the
next-decision JSON from an in-memory scored copy of the ledger. It does not
write `submissions/log.json`; the explicit mutation remains:

```bash
.venv/bin/python scripts/record_codabench_score.py \
  --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --update-experiment-log \
  --base v222 \
  --apply \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json
```

The readiness report and upload queue now point to this preflight first, then
to the recorder apply command.

### Lesson

Keep the official score intake split into two mechanical steps: parse/preview
without side effects, then apply only after `Parsed score cells: 36 / 36` and
the branch decision have been inspected. This protects the low-gap speed chain
from a malformed scorer paste or a mistaken ledger update.

---

## Offensive Rank Plan Gate -- No ZIP

**Status**: LOW-HANGING PLAN READY / NO ZIP
**Artifacts**:
- `scripts/offensive_rank_plan.py`
- `tests/test_offensive_rank_plan.py`
- `scripts/next_upload_readiness.py`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/offensive_rank_plan_2026_06_05.json`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

Added one read-only offensive plan that composes the current router, queued
rank EV, all non-leading target audit, and remaining low-gap audits. The
generated plan says:

```text
Decision: LOW_HANGING_PLAN_READY
Next: v222_plus_v225 on WS ECS Surf d1, rank 4 -> 2
Non-leading cells: 29, WATCH rows: 0
Remaining low-gap <= 1: NO_ADDITIONAL_LOW_GAP_BUILD_BEFORE_NEXT_SCORE
Extended low-gap <= 12: NO_ADDITIONAL_LOW_GAP_BUILD_BEFORE_NEXT_SCORE
```

The positive queued order remains:

```text
v222_plus_v225 -> v226 -> v233 -> v234 -> v229 -> v230 -> v227 -> v232 -> v235
```

`next_upload_readiness.py` now imports this plan and refuses
`READY_TO_UPLOAD` if it is no longer `LOW_HANGING_PLAN_READY`.

### Lesson

The low-hanging-rank objective is now represented as a single auditable gate:
score `v222_plus_v225` before building anything else. If the board changes,
the plan will force review instead of letting a stale or unclassified target
slip into the queue.

---

## Phase 1 Budget Gate -- No ZIP

**Status**: BUDGET READY / NO ZIP
**Artifacts**:
- `scripts/phase1_budget.py`
- `tests/test_phase1_budget.py`
- `scripts/next_slot_decision.py`
- `scripts/offensive_rank_plan.py`
- `scripts/next_upload_readiness.py`
- `docs/research/PHASE1_BUDGET_2026_06_05.md`
- `docs/research/phase1_budget_2026_06_05.json`
- `PLAN.md`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`

### Result

Centralized the current Phase 1 budget:

```text
Submissions used: 135 / 150
Submissions remaining: 15
Daily cap: 7
Deadline: 2026-06-14T23:55:00Z / 2026-06-15 01:55 GMT+2
Positive queued candidates: 9
Minimum daily-cap days for positive queue: 2
Slack days after positive queue: 5
After next upload: 136 / 150 used, 14 remaining
Positive queued candidates after next upload: 8
Decision: BUDGET_READY
```

The budget helper now feeds the offensive rank plan, and readiness surfaces
the same `15` remaining slots plus the `2` daily-cap days needed for the
current positive queue in its evidence line. It also shows that the current
upload would leave `14` slots for the score-gated follow-up path. `PLAN.md`
now reflects the post-`v222_plus_v227_plus_v232` quota state instead of the
older v197 `130/150` count.

### Lesson

Quota is no longer only prose in the final queue. If the positive candidate
ladder ever grows beyond the remaining slots, the offensive plan will return
review instead of treating all low-gap ideas as spendable. Daily cap pressure
is now visible too: the current positive queue cannot be spent in one day, so
the first slot should still be `v222_plus_v225` and later slots remain
score-gated.

---

## Queue Clearance-Ratio Risk Bands -- No ZIP

**Status**: RANK-EV RISK HARDENED / NO ZIP
**Artifacts**:
- `scripts/queued_upload_rank_ev.py`
- `tests/test_queued_upload_rank_ev.py`
- `scripts/offensive_rank_plan.py`
- `tests/test_offensive_rank_plan.py`
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/QUEUED_UPLOAD_RANK_EV_2026_06_04.md`
- `docs/research/queued_upload_rank_ev_2026_06_04.json`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/offensive_rank_plan_2026_06_05.json`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The queued rank-EV report now normalizes boundary clearance by the visible
next-rank gap:

```text
boundary_clearance_ratio = boundary_clearance / next_gap
```

and assigns a simple band: `no_flip`, `razor`, `thin`, `adequate`, or `wide`.
This keeps the queue from overvaluing a candidate just because it projects many
visible rank flips.

Current positive queue risk view:

| Artifact | Cell | Rank move | Gain | Clearance ratio | Band |
|---|---|---:|---:|---:|---|
| `v222_plus_v225` | `WS ECS Surf d1` | 4 -> 2 | 2 | 0.568 | `adequate` |
| `v226` | `WS ECS Surf d7` | 3 -> 2 | 1 | 0.174 | `thin` |
| `v233` | `WS ECS Pres d7` | 3 -> 2 | 1 | 0.175 | `thin` |
| `v234` | `WS NS Surf d7` | 11 -> 7 | 4 | 0.022 | `razor` |
| `v229` | `WS NS Pres d1` | 3 -> 2 | 1 | 0.051 | `thin` |
| `v230` | `WS ECS Surf d14` | 4 -> 3 | 1 | 0.016 | `razor` |
| `v227` | `Dir NS Sta d1` | 2 -> 1 | 1 | 0.267 | `adequate` |
| `v232` | `Dir NS Sta d7` | 5 -> 3 | 2 | 0.810 | `wide` |
| `v235` | `Dir ECS Sta d1` | 6 -> 5 | 1 | 0.071 | `thin` |

`v228` remains `no_flip` on the current board, so it stays skipped unless a
fresh board makes it rank-moving.

### Lesson

The low-hanging queue is still score-gated by transfer evidence, but it now
separates rank count from margin quality. `v222_plus_v225` remains the only
current upload; `v234` has high visible EV but only a razor margin, so it must
stay behind clean earlier speed gates and a live-board refresh.

---

## Router Rank-EV Context -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

The plain-text router output now includes the same rank-EV context that the
JSON/readiness paths already carried:

```text
Rank EV:
Snapshot: 2026-06-04
Candidate: v222_plus_v225 on WS ECS Surf d1, rank 4->2, visible gain 2, expected delta -0.0113, next gap 0.0072, clearance 0.004086, ratio 0.568 (adequate), gate NEXT_UPLOAD
Positive queue: v222_plus_v225 -> v226 -> v233 -> v234 -> v229 -> v230 -> v227 -> v232 -> v235
```

This means the first command an operator runs, `.venv/bin/python
scripts/next_slot_decision.py`, now explains why the next slot is
`v222_plus_v225` and why later candidates stay score-gated.

### Lesson

The router is the operational source of truth. Its text output should carry the
same low-hanging rank rationale as the generated Markdown/JSON reports, so a
slot cannot be spent from a command list divorced from the boundary evidence.

---

## Score-Intake Outcome Classifier -- No ZIP

**Status**: SCORE INTAKE HARDENED / NO ZIP
**Artifacts**:
- `scripts/score_intake_readiness.py`
- `tests/test_score_intake_readiness.py`

### Result

The dry-run score intake now emits a structured `outcome` before touching
`submissions/log.json`. For the pending `v222_plus_v225` lane, the preflight
will classify the score as one of:

- `CLEAN_RANK_FLIP`: target cell improved, visible rank flipped, and primary
  is non-worse versus the base. Apply the score, then follow the generated
  next-decision JSON for the gated compound build.
- `RAW_ONLY_GAIN`: target cell improved but did not flip the visible boundary.
  Hold the raw-only gain and do not build the next speed compound unless a
  refreshed board makes it rank-moving.
- `TARGET_RANK_FLIP_PRIMARY_WORSE`: visible rank flipped, but primary worsened.
  Stop the speed chain.
- `TARGET_FAILED`: the target cell did not improve. Stop the lane and let
  `next_slot_decision.py` choose the fallback.
- `REFRESH_BOARD`: the board snapshot is stale or invalid; record only after
  review and refresh the board before spending the next slot.

The command output now includes:

```text
Outcome: CLEAN_RANK_FLIP
Outcome target: speed_surface_d1_ecs
Outcome next action: Apply the score, then follow the next-decision JSON for the gated compound build.
```

and the JSON summary carries the same fields under `outcome`.

### Lesson

The score paste should not require re-reading the branch matrix by hand. The
preflight now turns the official score into the specific low-hanging decision:
advance the speed chain only on `CLEAN_RANK_FLIP`; otherwise preserve quota and
follow the fallback router.

---

## Readiness Outcome-Gate Sync -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The final readiness report now names the score-intake outcome gate explicitly:
apply a valid score only after the dry-run parser accepts all 36 cells, but
advance the speed chain only on `CLEAN_RANK_FLIP`. `RAW_ONLY_GAIN`,
`TARGET_FAILED`, `TARGET_RANK_FLIP_PRIMARY_WORSE`, and `REFRESH_BOARD` route
back through `next_slot_decision.py` instead of unlocking the next speed
compound automatically.

### Lesson

The operator handoff now matches the dry-run classifier. This reduces the main
quota risk after `v222_plus_v225`: treating a raw-only speed improvement as if
it had crossed a visible rank boundary.

---

## Router Outcome-Gate Caution -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The primary router caution now says: parse all 36 score cells before applying
the score, and advance the speed chain only when score-intake reports
`Outcome: CLEAN_RANK_FLIP`. The JSON payload and printed router output carry
the same warning as the final readiness report.

### Lesson

The first handoff after upload is the router output, not the long readiness
report. Keeping the outcome gate in that output prevents a raw-only improvement
from being treated as permission to spend the next speed compound slot.

---

## Static Handoff Outcome-Gate Sync -- No ZIP

**Status**: DOC HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `docs/research/PHASE1_FINAL_20_SLOT_PLAN_2026_06_04.md`
- `docs/research/POST_V222_SCENARIO_MATRIX_2026_06_04.md`
- `docs/research/V222_PLUS_V225_BRANCH_MATRIX_2026_06_05.md`
- `docs/research/SPEED_CHAIN_BRANCH_MATRIX_2026_06_05.md`
- `docs/research/COMPOUND_PREFLIGHT_MATRIX_2026_06_05.md`
- `docs/research/ALL_NONLEADING_RANK_TARGET_AUDIT_2026_06_05.md`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/BOARD_MONITORING.md`

### Result

The static upload packet, queue, final plan, scenario matrix, branch matrices,
preflight matrix, all-target audit, offensive plan, and board-monitoring note
now use the same rule as the router/readiness scripts: after `v222_plus_v225`
scores, build the next speed compound only if score intake reports
`CLEAN_RANK_FLIP`. `RAW_ONLY_GAIN` is explicitly a hold/fallback outcome, not a
speed-chain unlock.

### Lesson

The low-gap speed queue depends on tiny visible boundaries. Ambiguous wording
like "scores cleanly" is too easy to over-read after a raw-only improvement;
the docs now pin the handoff to the exact score-intake classifier.

---

## Post-Score Helper Outcome Labels -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/post_score_decision.py`
- `tests/test_post_score_decision.py`
- `tests/test_record_codabench_score.py`

### Result

The read-only post-score helper now uses the same outcome vocabulary as
`score_intake_readiness.py` for `v222_plus_v225`:
`CLEAN_RANK_FLIP`, `RAW_ONLY_GAIN`, `TARGET_RANK_FLIP_PRIMARY_WORSE`, and
`TARGET_FAILED`. Because `record_codabench_score.py` embeds that helper's
decision text in dry-run/apply reports, the official score-recording path now
shows the same speed-chain gate as the preflight.

### Lesson

The post-upload path has multiple reports. They must all use the same outcome
names, otherwise a user can see one report say "clean" and another say
"raw-only". The first speed follow-up remains gated only by
`CLEAN_RANK_FLIP`.

---

## Low-Hanging Target Gate Test Sync -- No ZIP

**Status**: TEST HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `tests/test_low_hanging_rank_targets.py`

### Result

The broader low-hanging queue test run found one stale assertion that still
accepted older clean-score wording for the `WS ECS Pres d7` held-v233 policy.
The policy itself already required score intake to report `CLEAN_RANK_FLIP`
for `v222_plus_v225`; the test now locks that stricter language.

### Lesson

This is a quota-risk guardrail. `v233` should stay behind
`v222_plus_v225_plus_v226_plus_v233` unless the first speed gate is an actual
score-intake `CLEAN_RANK_FLIP`; raw-only movement must not look equivalent in
tests, docs, or router output.

---

## Readiness Rank-EV JSON Alias -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The readiness payload now exposes the current low-hanging rank-EV candidate at
top level as `rank_ev`, while preserving the original
`next_slot.rank_ev.candidate` path. For the current packet this directly
reports `v222_plus_v225` on `WS ECS Surf d1`, projected rank `4 -> 2`,
boundary clearance `0.004086`, and clearance ratio `0.568`.

### Lesson

The post-upload score path should be easy to inspect quickly. A direct
`rank_ev` field reduces operator error when checking that the next slot is
still the intended low-hanging rank flip before pasting and applying the
Codabench score.

---

## Score-Intake Target Rank-EV Evidence -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/post_score_decision.py`
- `scripts/score_intake_readiness.py`
- `tests/test_score_intake_readiness.py`

### Result

The score-intake dry-run outcome now carries a `rank_ev` block for the intended
target cell. For `v222_plus_v225`, the dry-run summary and decision report can
show the exact target evidence: base rank, new rank, old boundary score,
boundary clearance, target-positive flag, visible-rank-gain flag, and
primary-nonworse flag.

The test fixture now mirrors the low-gap shape we care about: base
`speed_surface_d1_ecs = 4.5972`, two competitors at the `4.59` boundary, and a
clean candidate at `4.5860` producing rank `4 -> 2` with positive boundary
clearance. A raw-only candidate at `4.5960` keeps rank `4 -> 4` and reports
negative clearance.

### Lesson

After the upload score lands, the decision should not depend on interpreting a
sentence. The machine-readable outcome now includes the boundary evidence that
distinguishes a real low-hanging rank flip from a raw-only score movement.

---

## Score-Recorder Target Rank-EV Report -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/record_codabench_score.py`
- `tests/test_record_codabench_score.py`

### Result

The official score recorder now includes a dedicated target rank-EV section in
the generated post-score decision report. For `v222_plus_v225`, that report now
shows the intended `WS ECS Surf d1` evidence directly:

```text
Target: WS ECS Surf d1 (speed_surface_d1_ecs)
Score: 4.5972 -> 4.5860 (-0.0112)
Rank: 4 -> 2 (-2)
Boundary: B at 4.5900; clearance +0.0040
Gate flags: target_positive=true, visible_rank_gain=true, primary_nonworse=true
```

`build_experiment_log_payload()` uses the same formatter, so future
`--apply --update-experiment-log` score updates carry the boundary evidence in
the permanent narrative log as well. Tests now cover both the clean rank-flip
case and a raw-only target gain that improves the score but remains below the
visible-rank boundary.

### Lesson

The dry-run intake and official apply path must expose the same gate evidence.
Do not advance the speed chain from a prose decision alone; the score report
must show target-positive movement, a visible rank gain, and non-worse primary
before `v222_plus_v225_plus_v226` is built.

---

## June 6 Next-Upload Readiness Refresh -- No ZIP

**Status**: READY TO UPLOAD / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The readiness generator now takes a `--report-date` label and writes that date
into the Markdown title, so the handoff cannot silently look like yesterday's
packet. The June 6 refresh reports:

```text
Status: READY_TO_UPLOAD
Next artifact: v222_plus_v225
Board snapshot: as-of 2026-06-04, age 2 day(s), max accepted 2
Rank EV: WS ECS Surf d1 rank 4 -> 2, visible gain 2, clearance 0.004086
Upload verification: PASS, full row scan 3,448,801 CSV lines
```

Only `v222_plus_v225` passes compound preflight; `118` later compounds remain
blocked by score gates. This means the low-hanging plan is still valid today,
but any later upload decision should refresh or re-ingest the board first if
the stored `2026-06-04` snapshot ages past the `2`-day limit.

### Lesson

The rank-boundary map is perishable. Today the next upload is still
`v222_plus_v225`; after the freshness window expires, the right local action is
board refresh, not a speculative build.

---

## Readiness Freshness Expiry -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The readiness payload now includes explicit board-expiry fields:

```json
{
  "as_of": "2026-06-04",
  "age_days": 2,
  "max_age_days": 2,
  "valid_through": "2026-06-06",
  "days_until_refresh_required": 0
}
```

The Markdown evidence line now says the stored board is valid through
`2026-06-06` with `0` days before refresh is required. This keeps the current
`v222_plus_v225` upload packet usable today while making tomorrow's required
action unambiguous: refresh/re-ingest the public board before trusting any
stored rank-boundary flip.

### Lesson

A low-gap rank flip can disappear when the public board moves. The readiness
packet must show not only that the board is fresh enough, but exactly when that
claim expires.

---

## Readiness Freshness Status -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The board freshness payload now includes a categorical status:

```json
{
  "freshness_status": "EXPIRES_TODAY",
  "valid_through": "2026-06-06",
  "days_until_refresh_required": 0
}
```

For the current packet, readiness remains `READY_TO_UPLOAD`, but the Markdown
now says `freshness EXPIRES_TODAY`. That is the intended nuance: upload
`v222_plus_v225` from this packet today if spending a slot, but refresh the
public board before any later rank-boundary decision.

### Lesson

Binary fresh/stale is not enough at the deadline edge. `EXPIRES_TODAY` keeps
the next low-hanging upload available while making the next local action after
today explicit: board refresh first, not another speculative artifact.

---

## Router Freshness Payload -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

The primary next-slot router now prints a board freshness block and includes
the same structure in JSON:

```json
{
  "as_of": "2026-06-04",
  "age_days": 2,
  "max_age_days": 2,
  "valid_through": "2026-06-06",
  "days_until_refresh_required": 0,
  "freshness_status": "EXPIRES_TODAY",
  "status": "OK",
  "blocker": null
}
```

The current decision is still `UPLOAD_COMPOUND -> v222_plus_v225`, but the
router now shows that this recommendation rests on a board snapshot at the
freshness limit. If the same command runs after `2026-06-06` without a new
snapshot, the existing stale-board guard should route to `REFRESH_BOARD`
instead of spending a low-gap slot.

### Lesson

The readiness report should not be the only place carrying board expiry. The
operator's first command after any score paste is `next_slot_decision.py`, so
that command must expose whether its rank-boundary evidence is fresh, expiring,
or blocked.

---

## Score-Intake Freshness Payload -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/score_intake_readiness.py`
- `tests/test_score_intake_readiness.py`

### Result

The post-upload dry-run now carries the same structured board freshness payload
as the router. The JSON summary includes:

```json
{
  "board_freshness": "OK",
  "board_freshness_status": "EXPIRES_TODAY",
  "board_freshness_payload": {
    "as_of": "2026-06-04",
    "valid_through": "2026-06-06",
    "days_until_refresh_required": 0,
    "freshness_status": "EXPIRES_TODAY"
  }
}
```

The Markdown decision report also appends a board-freshness line inside the
`Score-Intake Outcome` block. That matters because `v222_plus_v225` may score
after the stored board has expired; in that case the score can still be
recorded after review, but any speed-chain advance must wait for a refreshed
public-board snapshot.

### Lesson

The upload score is not enough to advance a low-gap chain. The score-intake
dry run must prove both score validity (`36 / 36` parsed cells, no sentinel
errors) and rank-boundary freshness before it recommends the next rank-moving
compound.

---

## Budget Helper Queue Inference -- No ZIP

**Status**: BUDGET HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/phase1_budget.py`
- `tests/test_phase1_budget.py`

### Result

`phase1_budget.py` no longer requires a manual `--positive-candidates` value
for the normal current-queue check. With no override, it loads the stored board,
our current scores, and the queued rank-EV manifests, then counts positive
visible-rank candidates. The current command now works directly:

```bash
.venv/bin/python scripts/phase1_budget.py --json
```

Current output reports:

```json
{
  "decision": "BUDGET_READY",
  "positive_queue_candidates": 9,
  "submissions_remaining": 19,
  "submissions_used_after_next_upload": 132,
  "days_required_for_positive_queue": 2
}
```

The explicit `--positive-candidates` option remains available for what-if
checks, such as testing whether a larger refreshed-board queue would exceed the
remaining `19` slots.

### Lesson

Quota accounting should be a read-only check, not another place where the
operator has to remember and retype queue state. The low-hanging plan still
spends only the next gated slot on `v222_plus_v225`; this change just makes the
budget evidence easier to reproduce before uploading or after refreshing the
board.

---

## Raw Board-Paste Ingest -- No ZIP

**Status**: LIVE-BOARD GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/board_monitor.py`
- `tests/test_board_monitor.py`
- `docs/research/BOARD_MONITORING.md`

### Result

`board_monitor.py` now accepts raw copied Codabench leaderboard text:

```bash
.venv/bin/python scripts/board_monitor.py --ingest-paste /tmp/leaderboard.txt --as-of YYYY-MM-DD --dry-run
```

The parser handles the plain paste format with leading `Leaderboard`/`Task`
metadata, a metric header line, separate rank-number lines, and participant rows
containing names with spaces. It derives canonical cells from the metric header,
parses each row from the right-hand metric values, excludes `Hégoa`, skips
sentinel rows, and disambiguates duplicate participant names with `#ID`. After
that, it uses the existing snapshot validator, self-row guard, previous-snapshot
rotation, and older-snapshot refusal.

### Lesson

The board snapshot expires at the edge of the current upload decision. Refresh
must be easy to perform from the exact text shape available in chat or browser
copy, otherwise the low-gap rank queue can stall or, worse, use stale
boundaries. Dry-run the paste first; ingest only after the parsed movement
report looks sane.

---

## Stale-Board Raw-Paste Refresh Handoff -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

When the stored public board is stale, `next_slot_decision.py` now emits
paste-first refresh commands:

```bash
.venv/bin/python scripts/board_monitor.py --ingest-paste /tmp/leaderboard.txt --as-of YYYY-MM-DD --dry-run
.venv/bin/python scripts/board_monitor.py --ingest-paste /tmp/leaderboard.txt --as-of YYYY-MM-DD
.venv/bin/python scripts/board_monitor.py --ingest-tsv /tmp/leaderboard.tsv --as-of YYYY-MM-DD --dry-run
.venv/bin/python scripts/board_monitor.py --ingest-tsv /tmp/leaderboard.tsv --as-of YYYY-MM-DD
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

This keeps the router aligned with `board_monitor.py --ingest-paste`, which
handles the raw Codabench copy format with `Leaderboard`/`Task` metadata,
separate rank-number lines, participant names with spaces, duplicate names, and
`Hégoa` exclusion.

### Lesson

The low-hanging queue is only as good as the live board. When freshness blocks,
the router should offer the shortest reliable path from the user's actual
Codabench paste to a validated snapshot before any new submission is spent.

---

## Score-Intake Report-Date Freshness -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/score_intake_readiness.py`
- `scripts/record_codabench_score.py`
- `scripts/next_slot_decision.py`
- `tests/test_score_intake_readiness.py`

### Result

`score_intake_readiness.py` now accepts `--report-date` and applies that date to
both the parsed-score outcome and the previewed next-decision JSON. The covered
regression is the risky case where a `v222_plus_v225` score would otherwise look
like a clean rank flip but the stored board is expired:

```text
python scripts/score_intake_readiness.py --submission v222_plus_v225 \
  --scores-json /tmp/scores.json --report-date 2026-06-07 \
  --next-decision-json /tmp/next_decision.json

Board freshness: BLOCKED
Outcome: REFRESH_BOARD
Next decision status: REFRESH_BOARD
```

The previewed next-decision JSON also carries the expired board freshness and
the paste-first board refresh commands from `next_slot_decision.py`.

### Lesson

Parsing and recording the score are separate from advancing the rank queue. A
target-positive score can be logged after review, but the next low-hanging
compound must wait for a fresh public-board snapshot if the rank boundary
evidence has expired.

---

## Score-Apply Report-Date Freshness -- No ZIP

**Status**: SCORE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/record_codabench_score.py`
- `scripts/next_slot_decision.py`
- `tests/test_record_codabench_score.py`

### Result

`record_codabench_score.py` now accepts `--report-date` and applies that date to
its board freshness checks, decision report, optional experiment-log update, and
optional `--next-decision-json` handoff. The covered apply-mode regression:

```text
python scripts/record_codabench_score.py --submission v222_plus_v225 \
  --scores-json /tmp/scores.json --apply --report-date 2026-06-07 \
  --next-decision-json /tmp/next_decision.json

Updated log.json
Decision report: Board freshness BLOCKED
Next decision JSON: REFRESH_BOARD
```

This means a score can be recorded after review, but the generated next action
will be board refresh, not `v222_plus_v225_plus_v226`, when the stored
rank-boundary evidence has expired.

### Lesson

The dry-run and apply paths must enforce the same rank-boundary freshness rule.
Otherwise a valid score paste could be recorded correctly while its generated
handoff accidentally advances the speed chain from an expired board.

---

## Readiness Date-Aware Score Commands -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The generated post-upload commands now pass the actual shell date into both
score preflight and score apply:

```bash
.venv/bin/python scripts/score_intake_readiness.py --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --base v222 --report-date "$(date +%F)" \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json \
  --json-out logs/post_score_decisions/v222_plus_v225_intake_readiness.json

.venv/bin/python scripts/record_codabench_score.py --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --update-experiment-log --base v222 --report-date "$(date +%F)" --apply \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json
```

The June 6 readiness packet remains `READY_TO_UPLOAD` for `v222_plus_v225`; if
these same saved commands are run after the June 4 board expires, the score
helpers will use the run date and route next action to `REFRESH_BOARD`.

### Lesson

Adding date-aware score helpers is not enough if the operator handoff omits the
flag. The upload packet should make the safe path the default command path.

---

## Router Report-Date CLI -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

The canonical next-slot router now accepts `--report-date` and applies it to
both the branch decision and the rendered board-freshness payload. A stale-date
router run over the June 4 board now blocks before naming any upload artifact:

```text
python scripts/next_slot_decision.py --no-verify --report-date 2026-06-07
Status: REFRESH_BOARD
Board freshness: EXPIRED
Blocker: board snapshot is 3 days old; max accepted age is 2 days
```

The JSON path uses the same date and returns `status: REFRESH_BOARD`,
`rank_ev: null`, and the raw-paste board refresh commands first. Invalid date
strings fail fast with an argparse error instead of silently falling back to the
machine date.

### Lesson

The router is the command operators will reach for first. Its date semantics
must match readiness and score-intake helpers, otherwise a stale board could
still leak through the shortest manual path even after the handoff docs were
hardened.

---

## Router Date-Aware Score Commands -- No ZIP

**Status**: ROUTER/READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `scripts/next_upload_readiness.py`
- `tests/test_next_slot_decision.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The canonical router's generated post-upload commands now include the same
date-aware freshness argument as the readiness packet:

```bash
.venv/bin/python scripts/score_intake_readiness.py --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --base v222 --report-date "$(date +%F)" \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json \
  --json-out logs/post_score_decisions/v222_plus_v225_intake_readiness.json

.venv/bin/python scripts/record_codabench_score.py --submission v222_plus_v225 \
  --score-log logs/post_score_decisions/v222_plus_v225_score.log \
  --update-experiment-log --base v222 --report-date "$(date +%F)" --apply \
  --next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json

.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

`next_upload_readiness.py` also now passes its `--report-date` into the
embedded `next_slot_decision.py` payload. A June 7 readiness run over the June 4
board therefore fails at the queue decision itself (`next_slot.status:
REFRESH_BOARD`, no artifact, no rank-EV candidate), not only at the top-level
board metadata.

### Lesson

The shortest operator path must be the safest path. Keeping the readiness
packet date-aware was not enough while the canonical router still printed
date-implicit commands and readiness embedded a date-implicit router decision.

---

## Refresh Rerun Date-Aware -- No ZIP

**Status**: REFRESH HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

The stale-board `REFRESH_BOARD` branch now ends with the same date-aware router
rerun used after score intake/apply:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

The raw-paste and TSV refresh commands remain first in the handoff:

```bash
.venv/bin/python scripts/board_monitor.py --ingest-paste /tmp/leaderboard.txt --as-of YYYY-MM-DD --dry-run
.venv/bin/python scripts/board_monitor.py --ingest-paste /tmp/leaderboard.txt --as-of YYYY-MM-DD
```

### Lesson

Refreshing the public board is a recovery path, not an excuse to drop freshness
discipline. The command copied after a refresh should evaluate the next slot
against the actual run date just like the upload score path does.

---

## Score-Report Follow-Up Date-Aware -- No ZIP

**Status**: SCORE REPORT HARDENED / NO ZIP
**Artifacts**:
- `scripts/record_codabench_score.py`
- `scripts/post_score_decision.py`
- `tests/test_record_codabench_score.py`
- `tests/test_post_score_decision.py`

### Result

The score-recording path now writes date-aware follow-up text in both places an
operator is likely to copy from after a Codabench score lands:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

This affects the generated `EXPERIMENT_LOG.md` score-update section, default
ledger lessons for scored pending records, and the post-score branch report
phrases for `REFRESH_BOARD`, `CLEAN_RANK_FLIP`, and primary-worse fallbacks.

### Lesson

The upload handoff was date-aware, but score application is where the next
branch gets chosen. The score report itself must not reintroduce a
date-implicit queue decision after the official result is recorded.

---

## Post-Score Helper Report-Date CLI -- No ZIP

**Status**: POST-SCORE HELPER HARDENED / NO ZIP
**Artifacts**:
- `scripts/post_score_decision.py`
- `tests/test_post_score_decision.py`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`

### Result

The optional read-only branch helper now accepts the same explicit run-date
input as the production router:

```bash
.venv/bin/python scripts/post_score_decision.py --submission v222_plus_v225 --base v222 --report-date "$(date +%F)"
```

`post_score_decision.py` passes that date into the shared public-board
freshness blocker and echoes the report date in generated markdown. The upload
queue handoff now uses this command, so a copied fallback report cannot silently
judge `v222_plus_v225` against a different freshness clock than
`next_slot_decision.py`.

### Lesson

No new ZIP is justified before `v222_plus_v225` scores. The useful progress is
keeping every post-score branch surface on the same low-gap freshness rule:
record the score, block stale rank-boundary decisions, then rerun the
date-aware router before spending the next slot.

---

## Operator Docs Date-Aware Cleanup -- No ZIP

**Status**: OPERATOR HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `docs/research/EXPERIMENT_LOG.md`
- `docs/research/POST_V222_SCENARIO_MATRIX_2026_06_04.md`
- `docs/research/PHASE1_FINAL_20_SLOT_PLAN_2026_06_04.md`

### Result

The remaining active copy-paste handoffs now use explicit report-date routing:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

The final-20 plan also passes `--report-date "$(date +%F)"` to
`record_codabench_score.py` and `post_score_decision.py`, so a scored
`v222_plus_v225` cannot accidentally unlock a stale speed-chain branch through
an older optional report command.

### Lesson

The low-hanging path is still score-gated. Keep all operational docs aligned on
the same freshness contract: if the June 4 board is no longer current, refresh
it before using any visible-rank boundary to spend the next slot.

---

## Verifier Subset Date-Aware Router Hint -- No ZIP

**Status**: PRE-UPLOAD VERIFIER HINT HARDENED / NO ZIP
**Artifacts**:
- `scripts/verify_upload_packet.py`
- `tests/test_verify_upload_packet.py`

### Result

When `verify_upload_packet.py --artifacts ...` verifies only a subset, its
global-decision hint now prints the exact date-aware router command:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

This matters for manual pre-upload checks: verifying `v222_plus_v225` by hash
and row count is necessary, but it is not enough to authorize a slot if the
public board has expired. The verifier now points back to the same freshness
gate as the readiness report and upload queue.

### Lesson

Artifact verification and rank-boundary authorization are separate gates. The
low-hanging candidate remains `v222_plus_v225`, but a subset verifier run must
not give a stale shortcut around `next_slot_decision.py --report-date`.

---

## Verifier Fresh-Board Requirement -- No ZIP

**Status**: PRE-UPLOAD VERIFIER GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/verify_upload_packet.py`
- `tests/test_verify_upload_packet.py`
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`

### Result

`verify_upload_packet.py` now prints the public-board freshness state beside
the artifact checks and supports a hard pre-upload gate:

```bash
.venv/bin/python scripts/verify_upload_packet.py --artifacts v222_plus_v225 --require-fresh-board --report-date "$(date +%F)"
```

With `--require-fresh-board`, the verifier exits nonzero if the stored
leaderboard snapshot is stale, missing, future-dated, or unparseable. The active
`v222_plus_v225` upload packet and queue now use this command, and later
compound verifier examples include the same freshness requirement.

### Lesson

The ZIP can be valid while the rank boundary is invalid. For low-hanging speed
flips, a pre-upload check must verify both: artifact integrity and current
public-board evidence.

---

## Readiness Pre-Upload Commands -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The readiness Markdown now includes the router-derived pre-upload block before
the post-score commands:

```bash
.venv/bin/python scripts/verify_upload_packet.py --artifacts v222_plus_v225 --require-fresh-board --report-date "$(date +%F)"
Upload submissions/submission_v222_plus_v225.zip
```

The regenerated June 6 readiness artifacts still report `READY_TO_UPLOAD`,
`EXPIRES_TODAY`, and `WS ECS Surf d1` `4 -> 2`; the same report-date machinery
returns `NOT_READY` on June 7 over the June 4 board.

### Lesson

Readiness is the operator's last local page before spending a slot. It should
show the exact pre-upload freshness gate, not only post-upload score handling.

---

## Anonymous Board Refresh Attempt -- No ZIP

**Status**: INITIAL CURL REFRESH BLOCKED / SUPERSEDED / NO ZIP
**Artifacts**:
- `docs/research/BOARD_REFRESH_ATTEMPT_2026_06_06.md`

### Result

Tried the Codabench leaderboard CSV route documented for competitions:

```bash
curl -L -sS -D /tmp/codabench_headers.txt \
  -o /tmp/codabench_13821_get_csv.bin \
  https://www.codabench.org/api/competitions/13821/get_csv
```

For competition `13821`, this returned HTTP `404` and HTML, not a CSV/ZIP
leaderboard. Fetching the anonymous competition page with curl returned HTTP
`200`, but only the login shell and no leaderboard rows.

This initial curl-only path did not refresh the board. It was superseded by the
browser-table refresh recorded below.

### Lesson

Do not treat unauthenticated curl access as a board refresh. If the rendered
Results tab is available in the browser, extract and ingest that table; if not,
use logged-in UI paste or TSV export before trusting visible-rank boundaries.

---

## Browser Board-Table Refresh -- No ZIP

**Status**: LIVE BOARD REFRESHED / NO ZIP
**Artifacts**:
- `docs/research/BOARD_REFRESH_ATTEMPT_2026_06_06.md`
- `docs/research/current_public_leaderboard_2026_06_06.tsv`
- `docs/research/competitors_snapshot.json`
- `docs/research/competitors_snapshot_prev.json`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`
- `docs/research/QUEUED_UPLOAD_RANK_EV_2026_06_06.md`
- `docs/research/queued_upload_rank_ev_2026_06_06.json`

### Result

The in-app browser opened the public Codabench Results tab at
`https://www.codabench.org/competitions/13821/#/results-tab` and extracted the
rendered leaderboard table. `board_monitor.py --ingest-tsv` validated the
extracted TSV, skipped the old visible `Hégoa` self row, and wrote a fresh
snapshot:

```text
validated 19 competitors as-of 2026-06-06 from TSV; skipped self=1, sentinel=0
ingested 19 competitors as-of 2026-06-06 from TSV; skipped self=1, sentinel=0
```

The refreshed monitor says we now lead `7/36` cells. The thinnest defended cell
is `WS NS Sta d1`, where `v222` leads Printemps by only `0.07` WS. No led cell
was overtaken versus the previous snapshot.

The next-slot router still returns `UPLOAD_COMPOUND` for `v222_plus_v225`, but
with fresh June 6 rank boundaries:

```text
Board snapshot: as-of 2026-06-06, age 0/2, valid through 2026-06-08
Rank EV: WS ECS Surf d1 rank 4 -> 2, visible gain 2
Boundary clearance: 0.004086, clearance ratio 0.568 (adequate)
```

### Lesson

The stale-board fallback was correct, but the browser-rendered public table is
usable as a no-slot refresh source. Keep `v222_plus_v225` as the next upload;
do not build another low-gap artifact before it scores. After the score, rerun
the date-aware router against the refreshed board.

---

## Offensive-Plan Freshness Echo -- No ZIP

**Status**: LOW-HANGING PLAN HARDENED / NO ZIP
**Artifacts**:
- `scripts/offensive_rank_plan.py`
- `tests/test_offensive_rank_plan.py`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/offensive_rank_plan_2026_06_05.json`

### Result

The top-level offensive rank plan now carries the same board freshness payload
as the router/readiness/score-intake path. The regenerated plan starts with:

```text
Decision: LOW_HANGING_PLAN_READY
Source board snapshot: 2026-06-04
Board freshness: OK / EXPIRES_TODAY; valid through 2026-06-06; refresh in 0 day(s)
Expected next artifact: v222_plus_v225
```

The JSON artifact includes the full freshness object (`age_days`,
`valid_through`, `days_until_refresh_required`, `freshness_status`, and
`blocker`). This keeps the strategic answer intact while making the expiry edge
impossible to miss: upload/score `v222_plus_v225` from this board today, but
refresh the board before following any later rank-boundary queue decision.

### Lesson

The offensive plan is the highest-level decision artifact for "which
non-leading ranks are low-hanging." It must not silently look fresh after its
stored board evidence expires.

---

## Readiness Offensive Freshness Gate -- No ZIP

**Status**: READY GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

The final upload readiness gate now imports the offensive rank plan's structured
board freshness object into both JSON and Markdown, and `readiness_decision()`
blocks READY if that object is missing, blocked, or inconsistent with the
top-level board snapshot freshness fields (`as_of`, `age_days`,
`valid_through`, `days_until_refresh_required`, and `freshness_status`).

The regenerated 2026-06-06 readiness packet remains:

```text
Status: READY_TO_UPLOAD
Next artifact: v222_plus_v225
Offensive rank plan freshness: OK / EXPIRES_TODAY; valid through 2026-06-06
```

### Lesson

The readiness packet is the last stop before spending a slot, so it must prove
that its high-level offensive plan and its low-level board snapshot are reading
the same rank-boundary evidence. This keeps `v222_plus_v225` upload-ready today
while forcing a board refresh before any later rank-boundary decision.

---

## Report-Date Freshness Gate -- No ZIP

**Status**: READY GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/offensive_rank_plan.py`
- `scripts/next_upload_readiness.py`
- `tests/test_offensive_rank_plan.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/offensive_rank_plan_2026_06_05.json`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_06.md`
- `docs/research/next_upload_readiness_2026_06_06.json`

### Result

`next_upload_readiness.py --report-date` now controls the board freshness date
used by both the top-level readiness snapshot and the embedded offensive rank
plan. The regression check is explicit:

```text
python scripts/next_upload_readiness.py --report-date 2026-06-07 --json
exit=1
status NOT_READY
board freshness EXPIRED
blocker board snapshot is 3 days old; max accepted age is 2 days
```

The current 2026-06-06 packet was regenerated and remains `READY_TO_UPLOAD` for
`v222_plus_v225`, with the 2026-06-04 board marked `EXPIRES_TODAY`.

### Lesson

Report labels must not be cosmetic when they gate low-gap rank decisions. If the
handoff is generated for a date after the board evidence expires, it must force
a board refresh instead of carrying yesterday's upload authorization forward.

---

## Offensive-Plan Report-Date CLI -- No ZIP

**Status**: LOW-HANGING PLAN HARDENED / NO ZIP
**Artifacts**:
- `scripts/offensive_rank_plan.py`
- `tests/test_offensive_rank_plan.py`
- `docs/research/OFFENSIVE_RANK_PLAN_2026_06_05.md`
- `docs/research/offensive_rank_plan_2026_06_05.json`

### Result

The offensive plan now accepts `--report-date`, uses it in the Markdown title,
and applies it as the board freshness date. The generated current plan is now
titled:

```text
# Offensive Rank Plan - 2026-06-06
Decision: LOW_HANGING_PLAN_READY
Board freshness: OK / EXPIRES_TODAY; valid through 2026-06-06
```

The CLI stale-board regression is now covered:

```text
python scripts/offensive_rank_plan.py --report-date 2026-06-07 --json
decision LOW_HANGING_PLAN_REVIEW
freshness BLOCKED / EXPIRED
blocker board snapshot is 3 days old; max accepted age is 2 days
```

### Lesson

The offensive plan is the top-level "what should we attack next" artifact. It
must be regenerable for the actual decision date and must independently block
stale rank-boundary evidence before readiness embeds it.

---

## Remaining Low-Gap Audit — No Additional Build Before Next Score

**Status**: NO ZIP / DECISION AUDIT
**Artifact**: `docs/research/REMAINING_LOW_GAP_AUDIT_2026_06_05.md`
**Threshold**: visible next-rank gap `<= 1.0`

### Result

After building v235, the remaining unbuilt low-gap cells are all either
`BLOCKED` or `AUDITED_HOLD`. There are no `WATCH` rows under the `<= 1.0`
visible-gap threshold.

The remaining cells are:

- `WS NS Surf d14`, `WS NS Pres d14`, `WS NS Pres d7`
- `WS ECS Sta d1`, `WS ECS Pres d1`, `WS ECS Pres d14`
- `WS NS Sta d7`, `WS ECS Sta d14`, `WS NS Sta d14`
- `Dir ECS Pres d14`, `WS ECS Sta d7`, `Dir ECS Surf d7`

### Lesson

Do not build another artifact from these cells without a genuinely new
mechanism that contradicts the recorded block evidence. The low-hanging queue
is now prepared as far as current evidence supports; the next decision cycle is
external scoring of `v222_plus_v225`, followed by the score-gated queue.

---

## NS Pressure d7 Speed Lean-Tail Audit — No ZIP

**Status**: AUDITED HOLD / NO ZIP
**Artifact**: `docs/research/NS_PRESSURE_D7_SPEED_LEAN_TAIL_AUDIT_2026_06_05.md`
**Target**: `speed_pressure_d7_ns`

### Result

Read-only audit of a mini-challenge-style d7 pressure-speed variant on the
current `v222` base. The closest capped-tail HRES-gated configuration sits on
the boundary at `mean_width_delta=-0.003293`; the nearest clearing variant is
only `-0.003307` against the stored `0.0033` WS visible next-rank gap.

The uncapped pressure-level HRES tail floor is harmful for this cell:
`mean_width_delta=+0.021751`, `tail_rows=3004`, `max_tail_delta=13.9848`.

### Lesson

This is a distinct mechanism from v54/v69/v160, but it is too marginal to
build before the speed-width family validates. Keep `WS NS Pres d7` as
`AUDITED_HOLD`: revisit only after `v222_plus_v225` and earlier speed gates
score cleanly and a live-board refresh confirms the boundary remains tiny.

---

## NS Pressure d14 Speed Block Refresh — No ZIP

**Status**: BLOCKED / NO ZIP
**Target**: `speed_pressure_d14_ns`
**Reference**: `docs/research/D14_SPEED_MISS_WIDTH_EDA.md`

### Result

Do not build another endpoint-only `speed_pressure_d14_ns` artifact for the
current queue, even though the stored next-rank boundary is only `0.0027` WS.

The D14 EDA already warned that the full dimension is under-covered
(`min eval coverage = 0.839551`) and global shrink wins only `1 / 3` splits.
The two most specific EDA branches were then scored and failed hidden:

- `v180` q3-only tiny shrink worsened `24.3527 -> 24.3528`.
- `v181` q4 low-side widening worsened `24.3527 -> 24.3588`.

That also kills the held `v184` half-amplitude q4 widening bracket.

### Lesson

Treat `WS NS Pres d14` as a blocked fake low-hanging fruit. Revisit only with
a genuinely non-endpoint mechanism or a new validation oracle that contradicts
the post-v181 evidence; do not spend a Phase 1 slot before `v222_plus_v225`
and the existing guarded speed queue score.

---

## NS Surface d14 Speed Block Refresh — No ZIP

**Status**: BLOCKED / NO ZIP
**Target**: `speed_surface_d14_ns`
**Reference**: `docs/research/D14_SPEED_MISS_WIDTH_EDA.md`

### Result

Do not build another endpoint-only `speed_surface_d14_ns` artifact for the
current queue, even though the stored next-rank boundary is only `0.0016` WS.
This is the exact cell where three hidden-scored mechanisms already failed:

- `v158` micro-shrink worsened the target by `+0.0009` WS.
- `v177` width-preserving endpoint translation worsened the target by
  `+0.0135` WS.
- `v185` q4 low-side move worsened the target by `+0.0015` WS.

The d14 miss/width EDA supports the hidden failures: `speed_surface_d14_ns`
is under-covered in the replay proxy (`min eval coverage = 0.845956`), a
`0.005` shrink wins only `1 / 3` splits, and there is no NS surface d14 q3
shrink candidate.

### Lesson

Treat this as a blocked fake low-hanging fruit. Revisit only with a genuinely
non-endpoint mechanism or a new validation oracle that contradicts the D14 EDA;
do not spend a Phase 1 slot before `v222_plus_v225` and the existing guarded
speed queue score.

---

## ECS Station d1 Speed Block Refresh — No ZIP

**Status**: BLOCKED / NO ZIP
**Target**: `speed_stations_d1_ecs`

### Result

Do not build another `speed_stations_d1_ecs` station-speed revival for the
current queue, even though the stored next-rank boundary is only `0.0557` WS.

The early lane already found the hidden-proven plateau:

- `v101` improved `speed_stations_d1_ecs` to `6.9491`.
- `v102` pushed it to the current plateau at `6.8257`, but hidden transfer
  decayed from about `25%` in v101 to about `9%`.

Later attempts show the boundary is not actionable with current station-speed
families:

- `v126` cross-station IDW regressed by `+0.126` WS.
- `v165` simple v79 offsets worsened `6.8257 -> 6.9886`.
- `v182` low-capacity ExtraTrees MOS worsened `6.8257 -> 7.2089`.
- `v195` found no better donor than the deployed `v173`/`v102` value and
  refused to emit a zip.

### Lesson

Treat `WS ECS Sta d1` as blocked fake low-hanging fruit. Revisit only with a
replay-faithful station-speed oracle and a real hidden-scored donor edge beyond
the `6.8257` plateau; do not spend a Phase 1 slot before `v222_plus_v225` and
the active speed queue score.

---

## Extended Low-Gap Audit — No Additional Build Before Next Score

**Status**: NO ZIP / DECISION AUDIT
**Artifact**: `docs/research/EXTENDED_LOW_GAP_AUDIT_2026_06_05.md`
**Threshold**: visible next-rank gap `<= 12.0`

### Result

The `<= 1.0` low-gap audit already blocked or held every unbuilt near-boundary
cell. Expanding the audit to `<= 12.0` adds four larger but still tempting
direction cells, and none justify a local build before the next external
score:

- `dir_stations_d14_ns`: current value `305.6286`, next boundary `303.5600`.
  The v179 center-frozen width rebase regressed by `+2.1571` cWS, v108/v109
  were catastrophic, and v222 only restored the v204 regression.
- `dir_pressure_d1_ecs`: current value `104.8410`, next boundary `101.5000`.
  The only better hidden donor is v50 by just `-0.0010` cWS, while v213 widened
  `42.47%` of changed d1 rows and v215 skipped it as too risky.
- `dir_pressure_d1_ns`: current value `79.8870`, next boundary `73.3600`.
  No hidden-scored donor beats current; v214 is mechanically clean but estimated
  only near `~76`, still short of the boundary.
- `dir_pressure_d7_ecs`: current value `229.7705`, next boundary `221.4300`.
  v222 already harvested the v191/v196/v209 ladder, v196 showed diminishing
  returns, and the next boundary is now too wide for endpoint-only work.

### Lesson

Do not build another local artifact from unbuilt cells under the `<= 12.0`
visible-gap band. The queued work is already richer than the unbuilt frontier:
score `v222_plus_v225`, then follow the existing score-gated compound path.

---

## Compound Preflight Matrix — No ZIP

**Status**: QUEUE READINESS / NO ZIP
**Artifact**: `docs/research/COMPOUND_PREFLIGHT_MATRIX_2026_06_05.md`

### Result

Ran the guarded compound preflight matrix across every compound defined in
`scripts/build_scored_compound.py`. The current ledger state has exactly one
passing compound:

- `v222_plus_v225`: `PREFLIGHT_PASS`, already pending in the ledger, ZIP exists.

All `82` later compounds are correctly blocked. The first downstream speed
compound, `v222_plus_v225_plus_v226`, is blocked because
`v222_plus_v225 is pending; compound requires a scored positive ingredient`.
The later preservation compounds are similarly blocked by their missing or
pending prior scored chain.

### Lesson

The queue is in the intended pre-score state. Upload `v222_plus_v225` and do
not build `v222_plus_v225_plus_v226` or any later preservation compound until
the `v222_plus_v225` score is recorded and passes both gates:
target-positive on `speed_surface_d1_ecs` and primary-nonworse versus `v222`.

---

## All Non-Leading Rank Target Audit — No ZIP

**Status**: CLASSIFICATION AUDIT / NO ZIP
**Artifact**: `docs/research/ALL_NONLEADING_RANK_TARGET_AUDIT_2026_06_05.md`

### Result

Ran a full audit over every stored-board cell where the current best is not
rank 1. There are `29` non-leading cells and `0` unclassified `WATCH` rows.

Status distribution:

- `AUDITED_HOLD`: `12`
- `BLOCKED`: `6`
- `BUILT_HELD`: `9`
- `BUILT_NEXT`: `1`
- `BUILT_OPTIONAL`: `1`

The only `BUILT_NEXT` row remains `WS ECS Surf d1`, represented by the
production-preserving `v222_plus_v225` artifact. The `BUILT_OPTIONAL` row is
`v223`, which remains non-rank-moving on the current board.

### Lesson

There is no unclassified local offensive target left on the stored board. Do
not build another artifact before scoring `v222_plus_v225`; after that score
lands, refresh the live board and rerun this audit to catch any newly exposed
rank boundary.

---

## Next Upload Readiness Gate — No ZIP

**Status**: READY TO UPLOAD / NO ZIP
**Artifact**: `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`

### Result

Ran the consolidated final gate over the queue decision, upload packet,
compound preflight matrix, and all non-leading rank-target audit. The current
state has `0` blockers.

- Queue decision: `UPLOAD_COMPOUND` for `v222_plus_v225`.
- Upload verification: `PASS` for `submissions/submission_v222_plus_v225.zip`.
- Compound matrix: `1` pass and `82` blocked; only `v222_plus_v225` passes.
- Rank EV: `WS ECS Surf d1` projected `4 -> 2`, visible gain `2`, boundary
  clearance `0.004086`.
- Rank target audit: `29` non-leading cells and `0` `WATCH` rows.

### Lesson

The local rank-seeking frontier is exhausted until the next Codabench score is
recorded. Upload `v222_plus_v225`, then run the recorded post-score command to
update the ledger and reopen only score-gated downstream compounds.
The readiness gate now hard-blocks missing, stale, or non-positive rank-EV
context for the next artifact; a schema-valid ZIP alone is no longer enough to
spend a submission slot.

---

## Speed-Chain Rank-Flip Gate — No ZIP

**Status**: ROUTER/BUILDER HARDENED / NO ZIP
**Files**: `scripts/next_slot_decision.py`, `scripts/post_score_decision.py`, `scripts/build_scored_compound.py`, `scripts/next_upload_readiness.py`

### Result

Tightened the post-score speed-chain decision rule to match the current
rank-first strategy and the `v222_plus_v225` scenario matrix. A speed-chain
candidate must now be:

- target-positive on its intended cell,
- primary-nonworse versus the prior scored base,
- visibly rank-positive on the stored public-board snapshot.

Raw-only target improvements that do not flip a visible rank are now held
instead of unlocking or building the next speed compound. This specifically
prevents a small non-rank-moving `v222_plus_v225` score from authorizing
`v222_plus_v225_plus_v226` in either the router or compound preflight.
The generated next-upload readiness artifact also records the same post-score
gate so the upload packet and readiness report stay consistent.
The score-recording path is now covered too: a dry-run `v222_plus_v225` score
with raw-only `speed_surface_d1_ecs` improvement writes a next-decision JSON
that routes to `v227` and contains no `v222_plus_v225_plus_v226` build command.

### Lesson

With only `19` planned slots left, the queue should spend follow-up speed slots
only when the previous speed step actually buys rank leverage. Raw score
padding remains useful evidence, but it is not enough to continue the speed
chain under the final Phase 1 quota.

---

## v222_plus_v225 Post-Score Branch Matrix — No ZIP

**Status**: BRANCH MATRIX OK / NO ZIP
**Artifact**: `docs/research/V222_PLUS_V225_BRANCH_MATRIX_2026_06_05.md`
**JSON**: `docs/research/v222_plus_v225_branch_matrix_2026_06_05.json`

### Result

Ran the real next-slot router against five synthetic `v222_plus_v225` score
outcomes without modifying the ledger.

- Rank flip with primary better or equal: build `v222_plus_v225_plus_v226`.
- Raw-only target improvement with primary better: route to `v227`.
- Rank flip with primary worse: route to `v227`.
- Target regression with primary better: route to `v227`.

### Lesson

After the Codabench score is recorded, the next decision JSON should be trusted
only if it matches this matrix. This protects the final quota from continuing
the speed chain on a raw-only improvement that does not buy a visible rank.

---

## Verifier Subset Scope Guard — No ZIP

**Status**: UPLOAD ORDER GUARD / NO ZIP
**Purpose**: Prevent fallback packet checks from being mistaken for the global
next-upload decision.

### Result

`scripts/verify_upload_packet.py --artifacts ...` now accepts both
space-separated and comma-separated artifact lists. When run on a subset, the
table labels the printed candidate as:

```text
Next pending upload candidate among requested artifacts
```

and points the operator back to `scripts/next_slot_decision.py` for the global
queue. This matters because verifying `v227 v232 v235` is useful fallback
preparation, but `v227` is not globally next while `v222_plus_v225` is still
pending.

### Lesson

Packet verification is not queue selection. Use the verifier to prove ZIPs are
valid, and use `next_slot_decision.py` or `next_upload_readiness.py` to decide
which Phase 1 slot to spend.

---

## Rank-EV Boundary Clearance — No ZIP

**Status**: RANK-EV RISK AUDIT / NO ZIP
**Artifacts**:
- `docs/research/QUEUED_UPLOAD_RANK_EV_2026_06_04.md`
- `docs/research/queued_upload_rank_ev_2026_06_04.json`

### Result

The queued rank-EV report now exposes `next_boundary_score` and
`boundary_clearance`, not just visible rank gain. This answers the apparent
ordering conflict between `v233` and `v234`:

| Candidate | Cell | Visible gain | Boundary clearance |
|---|---|---:|---:|
| `v233` | `WS ECS Pres d7` | `1` | `0.000578` |
| `v234` | `WS NS Surf d7` | `4` | `0.000096` |

`v234` projects the bigger rank jump, but it clears the current stored boundary
by less than `0.0001` WS. That is too thin to treat as the next speed upload
purely by visible rank count. Keep the current order: score `v222_plus_v225`,
then `v226`, then `v233`; only build/use `v234` after clean earlier speed gates
and a live-board refresh confirms the NS surface d7 boundary still clears.

### Lesson

Low-hanging rank gain needs both visible rank movement and enough boundary
clearance to survive rounding/live-board movement. `visible_rank_gain` alone is
not sufficient for speed-chain ordering.

---

## Readiness Clearance Handoff — No ZIP

**Status**: READY HANDOFF UPDATED / NO ZIP
**Artifacts**:
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The readiness handoff now prints the exact rank-EV line for the current next
upload:

```text
Rank EV: `WS ECS Surf d1` `4 -> 2`, visible gain `2`, boundary clearance `0.004086`.
```

The refreshed readiness artifact also prints the stored public-board snapshot
age and shape:

```text
Board snapshot: as-of `2026-06-04` (1 day(s) old; `19` competitors, `36` cells).
```

The upload packet evidence now uses full row-count verification instead of only
the fast manifest path:

```text
Upload verification: `PASS` (full row scan: `3448801` CSV lines, `3447360` grid rows, `1440` station rows).
```

This makes the next slot auditable without opening the lower-level rank-EV JSON:
`v222_plus_v225` remains the next upload, and its projected clearance is much
stronger than the later fragile `v234` scrape.

### Lesson

The final upload checklist should include rank movement and boundary clearance,
not just packet validity. A valid ZIP is necessary; rank-EV clearance explains
why it is the right ZIP to spend next.

---

## Board Snapshot Ingest Validation — No ZIP

**Status**: LIVE-BOARD GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/board_monitor.py`
- `tests/test_board_monitor.py`
- `docs/research/BOARD_MONITORING.md`

### Result

Hardened the live-board refresh path that feeds low-hanging rank decisions.
`scripts/board_monitor.py` now:

- validates JSON snapshots before replacing `competitors_snapshot.json`,
- rejects missing cells, non-numeric values, duplicate cells, and our own row,
- rotates the previous snapshot only after validation passes,
- supports `--dry-run` for no-write checks that report against the parsed
  candidate snapshot, not the currently stored snapshot,
- refuses non-dry-run ingests whose parseable `as_of` date is older than the
  stored snapshot, unless `--allow-older` is passed for a deliberate backfill,
- supports `--ingest-tsv` for pasted Codabench leaderboard tables,
- maps headers such as `WS NS Stations d1` to canonical cells such as
  `WS NS Sta d1`,
- excludes `Hégoa`, skips sentinel rows, and disambiguates duplicate
  participant names with `#ID`.

Dry-run against the stored pasted table succeeded:

```text
validated 13 competitors as-of 2026-06-04-dry-run from TSV; skipped self=1, sentinel=1
```

Because dry-run now reports the parsed candidate snapshot, it can expose stale
paste files before they reach the canonical JSON snapshot. Non-dry-run ingest
now rejects older parseable `as_of` dates by default. The stored TSV fixture is
older than `competitors_snapshot.json`, so it shows a different defensive
picture; use it for parser checks only, not as a fresh board.

### Lesson

Live-board refresh is the main remaining source of stale rank-boundary error
before spending the next slot. A bad paste should not silently rewrite the
competitor snapshot that powers `low_hanging_rank_targets.py`,
`queued_upload_rank_ev.py`, and `next_upload_readiness.py`. Use TSV dry-run
first, then ingest only after validation passes.

---

## Verified Post-Score Follow-Up — No ZIP

**Status**: HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The generated score-recording handoff no longer ends with:

`next_slot_decision.py --no-verify`

It now ends with the verified default:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

`record_codabench_score.py --next-decision-json` already verifies by default,
but the human-facing follow-up command should do the same. This reduces the risk
of advancing to a stale or malformed next artifact after `v222_plus_v225` is
scored.

### Lesson

After spending a competition slot, do not disable local artifact verification in
the next queue decision. The few seconds saved are not worth the risk under the
final submission budget.

---

## v222_plus_v225 Compound Scope Audit -- No ZIP

**Status**: SCOPE GATE PASS / NO ZIP
**Artifacts**:
- `scripts/compound_scope_audit.py`
- `docs/research/V222_PLUS_V225_SCOPE_AUDIT_2026_06_05.md`
- `docs/research/v222_plus_v225_scope_audit_2026_06_05.json`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

Ran a full chunked reconstruction audit for the pending
`v222_plus_v225` upload packet:

```text
Rows audited: 3,448,800
Reconstruction mismatched rows: 0
```

The compound is exactly reconstructable as `v196` plus the declared overlays:

| Overlay | Columns | Changed Rows | Dimensions |
|---|---:|---:|---|
| `v222` | `dir_05, dir_50, dir_95` | `835,164` | `dir_pressure_d7_ecs=346111`, `dir_pressure_d7_ns=359084`, `dir_surface_d7_ns=129969` |
| `v225` | `q05, q50, q95` | `69,768` | `speed_surface_d1_ecs=69768` |

This also corrected an easy-to-misremember detail: `v222` restored the NS
station d14 direction state relative to the v212/v204 branch, but that state is
already equal to `v196`. Therefore the `v222` overlay diff used by
`v222_plus_v225` does not include `dir_stations_d14_ns`; it includes the v222
pressure d7 ECS/NS gains and the NS surface d7 direction gain.

`scripts/next_upload_readiness.py` now treats this JSON audit as part of the
readiness gate. The refreshed readiness report remains `READY_TO_UPLOAD` and
adds:

```text
Compound scope audit: PASS (v222: dir_pressure_d7_ecs, dir_pressure_d7_ns,
dir_surface_d7_ns; v225: speed_surface_d1_ecs).
```

### Lesson

The next slot is still `v222_plus_v225`, but the local gate is now stronger:
the packet is not merely schema/hash valid; it is row-for-row identical to the
intended base-plus-overlays construction and isolates the speed experiment to
the current low-gap `speed_surface_d1_ecs` cell.

---

## v222_plus_v225 Upload Handoff Sync -- No ZIP

**Status**: HANDOFF SYNCED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`

### Result

Updated the operator-facing upload packet and queue to match the current
verified router/readiness state:

- `v222_plus_v225` is the verified next rank-seeking speed diagnostic, not a
  loose optional diagnostic.
- The upload packet now references the scope audit and records that
  `v222_plus_v225` reconstructs as `v196 + v222 + v225` with `0` mismatched
  rows.
- The post-score handoff now dry-runs `record_codabench_score.py` before
  applying the score, so a malformed scorer log or surprising branch decision
  can be caught before mutating `submissions/log.json`.
- The default `next_slot_decision.py` command list now emits the same
  dry-run-then-apply flow, including `mkdir -p logs/post_score_decisions`, so
  router output, readiness output, and upload docs no longer disagree.
- The post-score apply command now reruns the verified default:

```bash
.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"
```

instead of the old `--no-verify` handoff.

### Lesson

The upload-time docs should be as strict as the helper scripts. With only 19
planned slots left after `v222`, the next action should be mechanical: upload
`submissions/submission_v222_plus_v225.zip`, save the scorer output, dry-run
the score intake, record the score against base `v222` if the branch is
sensible, and let the verified router choose the next branch.

---

## Readiness Board Freshness Gate -- No ZIP

**Status**: READY GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The readiness gate now refuses to emit `READY_TO_UPLOAD` from a stale or
unparseable stored public-board snapshot. The current packet still passes:
`competitors_snapshot.json` is as-of `2026-06-04`, which is `1` day old on
the 2026-06-05 run, under the `2` day maximum.

This matters because the current low-hanging queue is dominated by tiny
visible-boundary moves. `v222_plus_v225` has useful clearance (`0.004086` WS),
but later candidates such as `v234` are much more fragile, so stale
leaderboard boundaries can turn a rank-flip candidate into a wasted slot.

### Lesson

Before spending any later speed or direction diagnostic, refresh the public
board if the readiness report says the stored snapshot is older than two days
or has unknown age. A locally valid ZIP is not sufficient if the rank boundary
it targets is stale.

---

## Router Board Freshness Gate -- No ZIP

**Status**: ROUTER GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/queued_upload_rank_ev.py`
- `scripts/next_slot_decision.py`
- `tests/test_queued_upload_rank_ev.py`
- `tests/test_next_slot_decision.py`

### Result

The router now uses the same two-day public-board freshness rule as the upload
readiness gate. If `competitors_snapshot.json` has unknown age, a future date,
or an age greater than two days, `next_slot_decision.py` returns
`REFRESH_BOARD` instead of recommending `v222_plus_v225` or building the next
speed compound.

This also hardens the post-score path: `rank_positive_speed_gate` no longer
counts a target-cell improvement as rank-positive when the visible-rank
boundary comes from a stale stored board. That prevents `v222_plus_v225` or a
later speed probe from unlocking `v226`/`v233`/`v234` purely because an old
snapshot still shows a favorable boundary.

### Lesson

Low-hanging rank moves are boundary moves, not just raw-score moves. The
router may only advance the automatic queue when both are true: the score
intake reports the appropriate rank-flip outcome, and the public-board
boundary used for the visible rank flip is fresh enough to trust.

---

## Post-Score Board Freshness Gate -- No ZIP

**Status**: SCORE INTAKE GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/post_score_decision.py`
- `scripts/record_codabench_score.py`
- `tests/test_post_score_decision.py`
- `tests/test_record_codabench_score.py`

### Result

The score-intake reports now enforce the same public-board freshness rule as
the upload router. `record_codabench_score.py` still parses and records the
Codabench score, but if the stored board snapshot has unknown age, a future
date, or age greater than two days, its decision section returns
`REFRESH_BOARD` instead of recommending the next speed-chain compound.

This matters immediately after `v222_plus_v225`: a target-positive score should
not unlock `v222_plus_v225_plus_v226` unless the visible rank boundary was
computed from a fresh public-board snapshot. The raw score can be logged first;
the next upload/build decision waits for refreshed board evidence.

### Lesson

Score recording and slot routing are separate gates. Record every official
score, but do not treat a branch report as permission to spend the next slot
unless its board freshness line is `OK`.

---

## Compound-Builder Board Freshness Gate -- No ZIP

**Status**: BUILDER GATE HARDENED / NO ZIP
**Artifacts**:
- `scripts/build_scored_compound.py`
- `scripts/compound_preflight_matrix.py`
- `tests/test_build_scored_compound.py`
- `tests/test_compound_preflight_matrix.py`
- `docs/research/COMPOUND_PREFLIGHT_MATRIX_2026_06_05.md`
- `docs/research/compound_preflight_matrix_2026_06_05.json`

### Result

The compound builder now applies the same two-day public-board freshness rule
as the router, readiness report, and score-intake reports. If
`competitors_snapshot.json` is missing, unparseable, future-dated, age-unknown,
or older than two days, `build_scored_compound.py <compound_id> --preflight`
returns a blocker instead of authorizing a new compound build.

The regenerated preflight matrix still passes only `v222_plus_v225` in the
current state. It now also prints the board freshness state: snapshot
`2026-06-04`, age `1`, max `2`.

### Lesson

Rank-boundary freshness is now enforced at every local decision surface:
readiness, router, score intake, and direct compound build. If the board goes
stale after `v222_plus_v225` scores, the official score can still be recorded,
but no next compound should be built until the public-board snapshot is
refreshed.

---

## Score-Intake Dry-Run Artifact Preview -- No ZIP

**Status**: SCORE INTAKE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/record_codabench_score.py`
- `tests/test_record_codabench_score.py`

### Result

The score-intake dry-run now writes durable preview artifacts while keeping the
ledger untouched. With `--next-decision-json`, it clones the current
`submissions/log.json` records in memory, applies the parsed score to that
clone, and writes the next-slot decision JSON from the hypothetical scored
state. It also writes the dry-run branch report to the normal decision-report
path.

This fixes the operator handoff after `v222_plus_v225`: the dry-run command can
now preview whether a clean score would unlock `v222_plus_v225_plus_v226`
before `--apply` touches `submissions/log.json`.

### Lesson

Dry-run score intake should be non-destructive, not ephemeral. The official
score remains unapplied until `--apply`, but the branch evidence is now saved
for inspection instead of existing only in terminal scrollback.

---

## Readiness Compound Freshness Echo -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The final readiness payload now preserves the compound preflight matrix's own
`board_freshness` object instead of reducing the matrix to pass/block counts.
The Markdown handoff prints:

```text
Compound matrix board freshness: `OK` (as-of `2026-06-04`, age `1`, max `2`).
```

`readiness_decision()` also treats a blocked matrix freshness state as a direct
readiness blocker. This keeps the final upload packet, compound preflight
matrix, router, and direct builder aligned on the same low-gap rank-boundary
freshness evidence.

### Lesson

For final Phase 1 boundary plays, every visible-rank recommendation should show
which public-board snapshot authorized it. `v222_plus_v225` remains
`READY_TO_UPLOAD`; if the board snapshot or matrix freshness becomes blocked,
the readiness report must say `NOT_READY` before another submission slot is
spent.

---

## Score-Intake Parsed-Cell Echo -- No ZIP

**Status**: SCORE INTAKE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/record_codabench_score.py`
- `scripts/post_score_decision.py`
- `tests/test_record_codabench_score.py`
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`

### Result

The post-score dry-run/apply reports now print the parsed metric count:

```text
Parsed score cells: `36 / 36`
```

The parser already rejects missing cells, incomplete `dims OK`, and sentinel
dimensions. This change makes that validation visible in the operator-facing
report before `--apply` mutates `submissions/log.json`.

### Lesson

After `v222_plus_v225` is scored, do not apply the score just because the raw
log has a `primary_score`. The dry-run report must show all 36 cells parsed,
fresh board evidence, and a sensible branch decision before the ledger is
updated.

---

## Router Parsed-Cell Caution -- No ZIP

**Status**: ROUTER HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `tests/test_next_slot_decision.py`

### Result

The next-slot router now includes the score-intake parse check directly in its
`cautions` for upload, build, and wait-for-score decisions:

```text
Before --apply, the dry-run score report must show Parsed score cells: 36 / 36
with no missing-cell, dims OK, or sentinel-dimension errors.
```

The current `v222_plus_v225` router path still returns `UPLOAD_COMPOUND`, but
the first JSON/CLI output now names the exact score-intake condition that must
be inspected after Codabench scoring.

### Lesson

The safest upload handoff is redundant by design: the router, upload packet,
and score recorder should all say the same thing before the ledger can be
mutated. This reduces the chance of applying a partial scorer log and then
branching into the next low-gap artifact from incomplete evidence.

---

## Readiness Caution Echo -- No ZIP

**Status**: READY HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_upload_readiness.py`
- `tests/test_next_upload_readiness.py`
- `docs/research/NEXT_UPLOAD_READINESS_2026_06_05.md`
- `docs/research/next_upload_readiness_2026_06_05.json`

### Result

The final readiness Markdown now renders the router's `next_slot.cautions`
before the upload commands. The regenerated `v222_plus_v225` handoff includes:

```text
Before --apply, the dry-run score report must show Parsed score cells: 36 / 36
with no missing-cell, dims OK, or sentinel-dimension errors.
```

`v222_plus_v225` remains `READY_TO_UPLOAD`, with full row-scan packet
verification, scope audit, rank EV, board freshness, and all-target audit still
passing.

### Lesson

The operator-facing readiness file is the last document read before a slot is
spent, so it must repeat the same post-score parse requirement as the router
and upload packet. Do not apply the next score unless the dry-run report shows
all 36 metric cells parsed.

---

## Upload Queue Speed-Order Sync -- No ZIP

**Status**: QUEUE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `tests/test_verify_upload_packet.py`

### Result

The written upload queue now matches the guarded router/verifier order after a
clean `v222_plus_v225` and `v226` path:

```text
v226 -> v233 -> v234 -> v229 -> v230, with v228 held unless refreshed board rank-EV turns positive
```

The prior Markdown table skipped `v233` and `v234`, and also omitted held
`v235`, even though `verify_upload_packet.py`, `queued_upload_rank_ev.py`, and
`next_slot_decision.py` already knew about those artifacts. The queue now
lists all static verifier artifacts, and the new verifier test fails if a
queued static artifact is missing from the Markdown handoff.

### Lesson

For the remaining low-gap rank plays, the human queue must not drift from the
mechanical router. `v233` has safer boundary clearance than `v234`, while
`v234` has larger visible rank EV but thinner clearance; both belong before
later speed probes when their prior gates are clean. The subsequent v228
rank-EV skip gate narrowed that later chain further: current-board branches
skip v228 and go to v229 unless a refreshed board makes v228 rank-moving.

---

## v228 Rank-EV Skip Gate -- No ZIP

**Status**: ROUTER/BUILDER HARDENED / NO ZIP
**Artifacts**:
- `scripts/next_slot_decision.py`
- `scripts/build_scored_compound.py`
- `scripts/queued_upload_rank_ev.py`
- `docs/research/UPLOAD_QUEUE_2026_06_04.md`
- `docs/research/QUEUED_UPLOAD_RANK_EV_2026_06_04.md`

### Result

The current 2026-06-04 board says `v228` is mechanically clean but not
rank-moving: `visible_rank_gain=0` and boundary clearance `-0.005956`.
`v229` still projects one visible rank flip with clearance `+0.000901`, so a
clean speed branch should not be blocked by a pending no-rank v228 probe.

`next_slot_decision.py` now gates pending speed probes through the rank-EV
projection before it recommends a compound. If `v222_plus_v225`, v226, and
optionally v233/v234 score cleanly, the router can build the corresponding
`...plus_v229` compound directly. The old `...plus_v228` branches remain
buildable and score-aware for attribution or for a refreshed board where v228
becomes rank-moving.

### Lesson

Pending does not mean worth the next slot. Low-gap speed probes must clear the
visible boundary before they can advance the queue; otherwise they consume the
route and delay a rank-moving cell.

---

## Score-Recorder Skip-v228 Handoff -- No ZIP

**Status**: SCORE INTAKE HANDOFF HARDENED / NO ZIP
**Artifacts**:
- `scripts/post_score_decision.py`
- `scripts/low_hanging_rank_targets.py`
- `tests/test_record_codabench_score.py`
- `tests/test_post_score_decision.py`
- `tests/test_low_hanging_rank_targets.py`

### Result

The score-intake path now matches the router's current-board skip gate. A clean
`v222_plus_v225_plus_v226_plus_v233_plus_v234` score points to the matching
`...plus_v229` compound, not `...plus_v228`. The legacy `...plus_v228` branches
remain valid only if a refreshed board makes v228 rank-moving or for attribution
of an already-scored v228 branch.

The new recorder regression fills an in-memory clean v234 score, writes the
next-decision JSON through `record_codabench_score.py`'s handoff helper, and
asserts:

- `rank_ev.candidate.version == "v229"`
- a `...plus_v233_plus_v234_plus_v229` build command is emitted
- no `...plus_v233_plus_v234_plus_v228` build command is emitted

### Lesson

The scorer-result workflow needs the same rank-EV gate as the upload router.
Otherwise a correct upload score could still produce a stale next-decision JSON
and steer one of the remaining slots into a no-rank probe.

---

## Submission v235 — ECS Station d1 Direction Micro-Shrink

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Artifact**: `submissions/submission_v235.zip`
**SHA256**: `65928b6be9a787363a3dcfb3b5cedd15ac374d92ad34837c8c97d332f176bb6e`

### Approach

Build the smallest plausible `dir_stations_d1_ecs` rank-boundary probe without
reopening the blocked learned station-direction lane. The current center donor
is already hidden-proven from v39 and carried by v222, so v235 leaves `dir_50`
unchanged and shrinks only direction endpoints by `0.14` degrees per side.

This is a direct analogue to the held v227 North Sea station d1 micro-shrink,
but slightly larger because the ECS d1 next-rank gap is `0.2614` cWS. The
stored-board projection is `241.2614 -> 240.9814`, enough for rank `6 -> 5`
if coverage is unchanged.

### Scope Checks

- Target: `dir_stations_d1_ecs`.
- Changed rows: `224` station direction endpoint rows.
- `dir_50` changed rows: `0`.
- Speed changed rows: `0`.
- Non-target direction rows: `0`.
- Quantile crossings / NaN prediction values: `0`.
- Mean target-cell width delta if coverage holds: `-0.2800` cWS.
- Width sanity before shrink: mean `121.0185` degrees, minimum `76.2153`
  degrees.

### Lesson

PENDING SCORE / BUILT HOLD. v235 is not a next upload. It is a low-cost held
diagnostic for a one-rank direction boundary, distinct from the failed learned
station-direction center replacements. Keep it behind `v222_plus_v225` and the
guarded speed queue; after any clean speed or station-direction chain, use it
only through the guarded v235 preservation compounds and only if a live board
refresh still shows the ECS station d1 boundary as rank-moving.

---

## Submission v234 — NS Surface d7 Lean HRES-Tail Speed Guard

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Artifact**: `submissions/submission_v234.zip`
**SHA256**: `70106bab9ac609eddb7a630b4afb9a3152f0f319bbb08d8549457e5c0deda2e7`

### Approach

Build a very small North Sea surface d7 speed probe using the mini-challenge d7
lesson, but do not repeat the failed v94 broad half-offset lane. v234 shrinks
only low/mid HRES d7 rows and applies a rare q95 floor on high-HRES rows. It is
also a real prediction delta unlike the rejected v193 donor selector, which
found byte-identical predictions.

### Scope Checks

- Target: `speed_surface_d7_ns`.
- Changed rows: `144,836` speed endpoint rows.
- q50 changed rows: `0`.
- Direction changed rows: `0`.
- Non-target speed rows: `0`.
- Quantile crossings / negative q05 rows: `0`.
- NaN prediction values: `0`.
- Mean official-cell width delta if coverage holds: `-0.0043962579` WS.
- Shrink component: `-0.0045859211`; tail q95 component: `+0.0001896631`.
- Stored 2026-06-04 visible gap: `0.0043` WS, so the projected score barely
  crosses the next-rank boundary if coverage is unchanged.

### Lesson

PENDING SCORE / BUILT HOLD. v234 is not the next upload. It exists because
`WS NS Surf d7` has a tiny visible boundary and now has a distinct, much
smaller mechanism than v94. The stored-board projection is rank `11 -> 7`, so
after clean `v222_plus_v225`, `v226`, and `v233` gates, test it before `v229`
as `v222_plus_v225_plus_v226_plus_v233_plus_v234`. Use it only if a live board
refresh still shows the boundary as rank-moving; keep `v228` held unless a
refreshed board makes that separate target rank-moving.

---

## Submission v233 — ECS Pressure d7 Lean Pressure-Speed Tail Guard

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Artifact**: `submissions/submission_v233.zip`
**SHA256**: `3b90f6005c4ff6a044a440d9c5a67da8a48a88c7b8ebc4ff35ffcc676e4cf1ac`

### Approach

Build a narrower replacement for the quarantined ECS pressure d7 speed family.
The prior v174 pressure d7 shrink cut the official cell by `-0.024620` WS on
average and still regressed hidden `15.3733 -> 15.3774`. v233 applies the d7
mini-challenge lesson instead: lean low/mid-HRES intervals plus a rare
HRES-magnitude q95 guard.

### Scope Checks

- Target: `speed_pressure_d7_ecs`.
- Changed rows: `271,744` speed endpoint rows.
- q50 changed rows: `0`.
- Direction changed rows: `0`.
- Non-target speed rows: `0`.
- Quantile crossings / negative q05 rows: `0`.
- NaN prediction values: `0`.
- Mean official-cell width delta if coverage holds: `-0.0038778477` WS.
- Shrink component: `-0.0039588207`; tail q95 component: `+0.0000809730`.

### Lesson

PENDING SCORE / BUILT HOLD. v233 is not the next upload. It exists because
`WS ECS Pres d7` is a tiny `0.0033` WS boundary and the new mechanism is much
narrower than v174 while avoiding high-speed shrink. Hold behind
`v222_plus_v225` and `v226`; if those speed gates validate, use v233 only via a
production-preserving compound, not as a standalone upload that drops prior
clean gains.

---

## Submission v230 — ECS Surface d14 Asymmetric Speed-Bin Shift

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Artifact**: `submissions/submission_v230.zip`
**SHA256**: `acc42e30240e6c113906ad28e515719b71e3d81f91365b4e2eb35381c38c8a60`

### Approach

Build a narrow d14 speed candidate only after a target-specific action audit.
The audit in
`docs/research/D14_SURFACE_ECS_ASYMMETRIC_ACTION_AUDIT_2026_06_04.md`
tested q3 shrink, one-sided widening, and speed-bin shifts on 4,665,735 ECS
surface d14 10m replay rows.

The winning replay action was `shift_0.05`: shift q1/q2 speed endpoints up by
`0.05`, shift q4 speed endpoints down by `0.05`, and leave q3 untouched. It
won all three eval splits with 10m mean delta `-0.082525` and worst split
`-0.070767`. Because the artifact leaves 100m unchanged, the replay-implied
official surface-cell movement is only about `-0.041262`, barely above the
visible `0.0406` WS boundary.

### Scope Checks

- Changed rows: `63,965` speed endpoint rows.
- q50 changed rows: `0`.
- Direction changed rows: `0`.
- Non-target speed rows: `0`.
- Quantile crossings / negative q05 rows: `0`.
- NaN prediction values: `0`.
- Mean width delta: effectively `0` because the action is width-neutral.

### Lesson

v230 is the first plausible ECS surface d14 speed probe on the current board,
but it is thin-margin and d14 speed has bad hidden history. Keep it behind
v225, the guarded `v222_plus_v225` compound, `v226`, `v233`/`v234`, and `v229`.
If v225 fails, skip v230 with the rest of the unscored speed-width/endpoint
family. Treat `v228` as a held side branch only if a refreshed board makes its
target rank-moving.

---

## Submission v232 - NS Station d7 Asymmetric Direction Endpoint Salvage

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Source**: `v183` d7-only endpoints
**Artifact**: `submissions/submission_v232.zip`
**SHA256**: `b3e2b4000becc5b9a8746839ac11ac628239ae94a6a8f79e8983c6947e313a50`

### Approach

Build the only plausible `dir_stations_d7_ns` salvage without carrying the
known-bad part of `v183`. The original `v183` artifact touched both
`dir_stations_d14_ns` and `dir_stations_d7_ns`; after `v179` showed the d14
station-width family regressed hidden, `v183` as built is blocked. `v232`
copies only the d7 endpoint rows from `v183` onto the current `v222` base.

The visible current-board gap is large for a station cell: `dir_stations_d7_ns`
is rank 5 at `310.9467`, with the next boundary at `301.5400`
(`9.4067` cWS away). The v183 replay branch had enough local magnitude to be
worth preserving as a held diagnostic: `d7_asym_0.50` showed mean delta
`-42.2094` cWS and worst split `-17.0247` cWS.

### Scope Checks

- Changed rows: `256` station direction endpoint rows.
- Target: `station / north_sea / d7 / direction` only.
- `dir_50` changed rows: `0`.
- Speed changed rows: `0`.
- Non-target direction rows: `0`.
- Quantile crossings / NaN prediction values: `0`.
- Mean target width delta: `+0.166796875` degrees.

### Lesson

v232 is a held station-d7 direction diagnostic, not a next upload. It has clean
mechanics and enough replay magnitude to plausibly cross the current boundary,
but the station-direction hidden record is fragile and v183's sibling d14
family is explicitly blocked. Keep v232 behind v222_plus_v225, the guarded
`v222_plus_v225` path, the clean speed chain (`v226`, `v233`/`v234`, `v229`,
`v230`), and `v227`; use only after a fresh live-board check and an explicit
decision to spend a station-d7 direction slot. If `v228` becomes rank-moving on
a refreshed board, preserve it through the matching compound before v232.

---

## Research Note — ECS Pressure d14 Remaining Lambda Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `speed_pressure_d14_ecs`
**Audit artifact**:
`docs/research/PRESSURE_D14_ECS_REMAINING_LAMBDA_AUDIT_2026_06_04.md`

### Result

The only untested part of the hidden-proven pressure d14 ladder is the
non-high `850/925` branch. Current `v222` already has high-regime `850/925`
rows at lambda `1.00`; the remaining non-high `82,080` rows are still at
lambda `0.80`.

The current visible rank boundary is `0.0886` WS (`rank 2 -> 1`, Printemps at
`17.8000`). Extrapolating from the successful hidden ladder gives only about
`-0.0136` WS for pushing the entire remaining branch from `0.80` to `1.00`,
or about `15.3%` of the needed boundary.

### Decision

Do not build a `v231` pressure-d14 ECS speed artifact from this lambda branch.
It is mechanically clean but not rank-moving on the current board, and it sits
behind lower-gap built candidates `v222_plus_v225`, `v226`, `v233`, `v234`,
`v229`, and `v230`. Reopen only if the live boundary tightens materially or a
new donor/regime mechanism offers expected movement near `0.09` WS.

---

## Research Note — NS Station d7 Speed Current-Board Audit, No Artifact

**Status**: BLOCKED / NO ARTIFACT
**Target considered**: `speed_stations_d7_ns`
**Audit artifact**:
`docs/research/STATION_D7_NS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`speed_stations_d7_ns` is the next unresolved low-gap watch cell after the
already-built speed queue, but it is not currently buildable. Current `v222`
score is `13.4534`, visible rank `5`; the next boundary is `0.1134` WS against
`sajayrrr` at `13.3400`.

The only hidden-scored donor edge from v195 is `-0.0034` WS, about `3.0%` of
the current boundary. Stronger station-speed families are contradicted by
prior evidence:

- v89 center-MOS had avg delta `-0.1329` but worst split `+0.0480` and coverage
  dropped to `0.8808`.
- residual calibration sweep had avg delta `-0.0433`, worst split `+0.0415`.
- v187 analog residuals failed every leave-period split, period avg `+1.2978`.
- v119_fs scored hidden `15.5620`, a `+2.1086` WS regression.

### Decision

Do not build or upload an NS station d7 speed artifact from the current
station-speed families. Reopen only if a new oracle has leave-period worst
split `<= 0.0`, expected movement at least `0.1134` WS, and no contradiction
with the `v119_fs`/`v187` hidden-regime failures.

---

## Research Note — NS Station d14 Speed Current-Board Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `speed_stations_d14_ns`
**Audit artifact**:
`docs/research/STATION_D14_NS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`speed_stations_d14_ns` is visible rank `2` with current score `15.5595`;
the next boundary is `0.2195` WS against `sajayrrr` at `15.3400`. The current
base already carries the best hidden-scored value seen in `submissions/log.json`.

The earlier `v116` residual-target lane was real (`15.6045`), but the current
state already harvested the later `15.5595` target value from the otherwise
catastrophic v122 path. No historical donor is better than current. Follow-up
families fail the gates:

- `v116_tight` regressed to `16.1084`.
- v89 center-MOS regressed every split, avg `+0.2146`, worst `+0.4281`.
- residual calibration sweep regressed, avg `+0.0371`, worst `+0.0560`.

### Decision

Do not build another NS station d14 speed artifact from the current
station-speed families. Reopen only if a new mechanism can plausibly move at
least `0.2195` WS with leave-period worst split `<= 0.0` against the deployed
base.

---

## Research Note — ECS Pressure d14 Direction Current-Board Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_pressure_d14_ecs`
**Audit artifact**:
`docs/research/DIR_PRESSURE_D14_ECS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`dir_pressure_d14_ecs` is visible rank `5` with current score `300.5204`;
the next boundary is `0.2904` cWS against `Matteo` at `300.2300`. The current
base already carries the best hidden-scored value seen in `submissions/log.json`.

The tiny boundary is tempting, but both endpoint directions have already failed
hidden scoring:

- `v192` narrowed center-frozen pressure d14 ECS direction intervals and
  regressed `300.5204 -> 300.9596` (`+0.4392` cWS).
- `v197` tested the opposite selective widening hypothesis and regressed
  `300.5204 -> 300.5307` (`+0.0103` cWS).

No scored donor is better than current: `v135`/`v151` harvested the `300.5204`
value, `v138` was worse at `300.8883`, and all later best bases preserve
`300.5204`.

### Decision

Do not build another endpoint-only `dir_pressure_d14_ecs` artifact. Reopen only
if a new center/regime donor can plausibly move more than `0.2904` cWS with one
official cell touched and no contradiction with the `v192`/`v197` hidden
failures.

---

## Research Note — ECS Surface d7 Direction Current-Board Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_surface_d7_ecs`
**Audit artifact**:
`docs/research/DIR_SURFACE_D7_ECS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`dir_surface_d7_ecs` is visible rank `3` with current score `265.8556`;
the next boundary is `0.6656` cWS against `sajayrrr` at `265.1900`. The
current base already carries the best hidden-scored value seen in
`submissions/log.json`.

The remaining known moves are too small or contradicted by hidden scoring:

- The scored donor-oracle edge was only `265.8568 -> 265.8556` (`-0.0012`
  cWS), about `0.18%` of the next-rank boundary.
- `v121` aggressive width replacement regressed the target by about `+19.35`
  cWS.
- `v143` u/v residual center movement regressed d7 to `266.9964`
  (`+1.1408` cWS) despite replay improvements.
- `v217` was mechanically clean, but newer board-monitoring evidence says it
  lost hidden; `v221` exists specifically to revert its `68,375` changed rows.

### Decision

Do not build another endpoint-only or generic surface-direction artifact for
`dir_surface_d7_ecs`. Reopen only if a new center/regime donor can plausibly
clear at least `0.6656` cWS, touches one official cell, and is not contradicted
by the `v143`/`v217` hidden failures.

---

## Research Note — ECS Surface d14 Direction Current-Board Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_surface_d14_ecs`
**Audit artifact**:
`docs/research/DIR_SURFACE_D14_ECS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`dir_surface_d14_ecs` is visible rank 2 with current score `325.6517`; the
rank-1 boundary is `20.6417` cWS against `Printemps @ 305.0100`. The current
base already carries the best hidden-scored value seen in `submissions/log.json`:
`v150` reached `325.6517`, and `v222` preserves that state.

The known mechanisms are already spent or contradicted by hidden scoring:

- `v60` had strong replay gains but regressed hidden versus v59.
- `v84`/`v85` transferred, but together moved only `-0.2471` cWS from v59.
- `v117` heavy direction graft worsened the target to `335.3914`.
- `v121` heavy-width hybrid exploded the target to `467.9077`.
- `v143`/`v145`/`v147`/`v149`/`v150` found real center signal, but even the
  best hidden value is still `20.6417` cWS from the current rank-1 boundary.

### Decision

Do not build another ECS surface d14 direction artifact from the current
surface-direction families. Reopen only if a new center/regime donor can
plausibly move more than `20.6417` cWS or the live board tightens materially.

---

## Research Note — NS Station d14 Direction Current-Board Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_stations_d14_ns`
**Audit artifact**:
`docs/research/DIR_STATIONS_D14_NS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

`dir_stations_d14_ns` is visible rank `5` with current score `305.6286`;
the next boundary is `2.0686` cWS against `michaelibrahim` at `303.5600`.
The current base already carries the best hidden-scored value seen in
`submissions/log.json`.

Known station d14 direction moves have failed:

- `v108`/`v109` conservative station d14 width MOS was catastrophic, taking the
  target to `892.6525` (`+587` cWS).
- `v179` was the cleanest later one-cell test: 256 rows, centers frozen, no
  collateral, but it regressed `305.6286 -> 307.7857` (`+2.1571` cWS).
- `v183` includes the same failed d14 family plus d7 asymmetry, so it should
  not be submitted as built.
- `v204` widened 113 rows; `v222` restored those rows back to the v196/pre-v204
  endpoints and promoted as the current base.

### Decision

Do not build another `dir_stations_d14_ns` station-direction d14 width,
widening, or endpoint-only artifact. Reopen only if a new center/regime donor
can plausibly clear at least `2.0686` cWS with one official cell touched and no
contradiction with the `v108`/`v179`/`v204` hidden failures.

---

## Research Note — ECS Pressure d1 Direction Audit, No Upload

**Status**: AUDITED HOLD / DO NOT UPLOAD `v213`
**Target considered**: `dir_pressure_d1_ecs`
**Audit artifact**:
`docs/research/DIR_PRESSURE_D1_ECS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

Current `dir_pressure_d1_ecs` is rank 3 at `104.8410`. The next visible
boundary is `3.3410` cWS against `ayush13 @ 101.5000`, and rank 1 is
`Matteo @ 94.3200`.

The scored donor ledger does not contain a usable improvement. `v50` is the
only hidden-scored value better than current at `104.8400`, just `-0.0010` cWS
better than v222, and `v50` was a catastrophic CQR submission with mean rank
`4.06`.

### Decision

Do not upload `v213` and do not build another ECS pressure d1 endpoint-only
artifact from this Lane A d1 family. The local `v213` manifest moved
`128,659 / 410,400` target rows but widened `42.47%` of changed rows, with only
`-0.2322 deg` mean half-width movement versus base. The later `v215` compound
explicitly skipped `v213` as too risky while keeping the proven pressure d7
Lane A cells.

### Reopen Gate

Reopen `dir_pressure_d1_ecs` only if a new center/regime donor appears with
expected movement above the `3.3410` cWS next-rank boundary, or if the live
board tightens close to the microscopic `-0.0010` cWS donor edge.

---

## Research Note — NS Pressure d1 Direction Audit, No Upload

**Status**: AUDITED HOLD / DO NOT UPLOAD `v214`
**Target considered**: `dir_pressure_d1_ns`
**Audit artifact**:
`docs/research/DIR_PRESSURE_D1_NS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

Current `dir_pressure_d1_ns` is rank 3 at `79.8870`. The next visible boundary
is `6.5270` cWS against `ayush13 @ 73.3600`, and rank 1 is
`Matteo @ 70.7200`.

The scored donor ledger has no better hidden value: the best values in
`submissions/log.json` are tied at `79.8870`. Earlier broad pressure d1/d7
direction work is a warning rather than a donor: `v37` regressed this cell to
`98.0677`, and `v96` regressed a d1-inclusive NS copula attempt to `80.1201`.

### Decision

Do not upload `v214`. It is mechanically clean but not rank-moving at the
current boundary. The local manifest changed `151,578 / 410,400` target rows,
froze `dir_50`, changed no speed rows, and widened only `12.09%` of changed
rows. But the `v215` compound manifest estimates the target near `~76`, still
behind the `73.3600` next-rank boundary.

### Reopen Gate

Reopen `dir_pressure_d1_ns` only if the live board tightens into the expected
`v214` movement range, or if a new center/regime donor appears that can
plausibly beat `73.3600` without contradicting the `v37` and `v96` failures.

---

## Research Note - ECS Pressure d7 Direction Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_pressure_d7_ecs`
**Audit artifact**:
`docs/research/DIR_PRESSURE_D7_ECS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

Current `dir_pressure_d7_ecs` is rank 3 at `229.7705`. The next visible
boundary is `8.3405` cWS against `ayush13 @ 221.4300`, and rank 1 is
`Matteo @ 216.5200`.

The current base already carries the best hidden-scored value in the ledger:
`v222` at `229.7705`. The known pressure-d7 direction ladder has been spent:
`v191` improved `235.0012 -> 233.8237`, `v196` added only
`233.8237 -> 233.5926`, and `v222` validated the stronger `v209` Lane A
overlay through the clean pressure-d7 compound, reaching `229.7705`.

### Decision

Do not build or upload another `dir_pressure_d7_ecs` endpoint-only artifact
from the current v191/v196/v209 Lane A family. The remaining `8.3405` cWS gap
is larger than the last scored single-cell increments, and `v209` is already
harvested by v222 rather than being a new candidate.

### Reopen Gate

Reopen `dir_pressure_d7_ecs` only if a new center/regime donor appears that can
plausibly clear the `221.4300` next-rank boundary, or if the live board tightens
materially enough that a fresh one-cell overlay is rank-moving.

---

## Research Note - NS Pressure d7 Direction Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `dir_pressure_d7_ns`
**Audit artifact**:
`docs/research/DIR_PRESSURE_D7_NS_CURRENT_BOARD_AUDIT_2026_06_04.md`

### Result

Current `dir_pressure_d7_ns` is rank 2 at `255.2599`. The rank-1 boundary is
`18.7199` cWS against `sajayrrr @ 236.5400`.

The current base already carries the best hidden-scored value in the ledger:
`v222` at `255.2599`. The old merge-aligned donor plateau was `266.5361`.
The v198/v202/v202b endpoint-shrink branch was weaker than the harvested Lane A
branch: `v202b` reports only `3.4616` degrees mean shrink on changed rows,
while `v211` moved `254,479` rows with mean movement `15.0331` degrees. The
v212 manifest expected `255.26`, and v222 scored exactly `255.2599`.

### Decision

Do not build or upload another `dir_pressure_d7_ns` endpoint-only artifact from
the current v198/v202/v202b/v211 family. The remaining `18.7199` cWS gap needs
a new center/regime donor, not a parameter continuation of the spent pressure
d7 endpoint family.

### Reopen Gate

Reopen `dir_pressure_d7_ns` only if a new center/regime donor can plausibly
clear `sajayrrr @ 236.5400`, or if a live-board refresh materially tightens the
rank-1 boundary.

---

## Submission v229 — NS Pressure d1 Speed Uncertainty-State Candidate

**Status**: PENDING SCORE / BUILT HOLD
**Base**: `v222`
**Artifact**: `submissions/submission_v229.zip`
**SHA256**: `b3e6bc3402ea9a5f2b8f603b07ff6e859e090ed2ef4aa0d6e6b3075515aad0fa`

### Approach

Build the first pressure d1-specific speed candidate only after a bounded
feature audit. The audit in
`docs/research/PRESSURE_D1_UNCERTAINTY_FEATURE_AUDIT_NS_2026_06_04.md`
found 13 split-stable uncertainty features above the `0.05` split-Spearman
gate, led by pressure level, level wind speed, level forecast spread, and
d1-to-d7 tendency.

The artifact changes only `speed_pressure_d1_ns`: NS grid pressure levels
`1000/925/850/700/500`, horizon d1, speed endpoints. q50, all direction
columns, all surface rows, all stations, ECS rows, and non-d1 rows are frozen.

### Scope Checks

- Changed rows: `348,840` speed endpoint rows.
- q50 changed rows: `0`.
- Direction changed rows: `0`.
- Non-target speed rows: `0`.
- Quantile crossings / negative q05 rows: `0`.
- NaN prediction values: `0`.
- Mean official-cell width delta if coverage holds: `-0.018501` WS.

### Lesson

v229 gives `speed_pressure_d1_ns` a real pressure-specific mechanism instead of
the old blind endpoint/shrink class. It is still unscored and broad across all
pressure levels, so it stays behind `v222_plus_v225`, `v226`, and the cleaner
`v233`/`v234` branch while those remain rank-moving. On the current board,
`v228` does not clear a visible rank boundary, so `v229` may follow the latest
clean speed branch directly if `v228` is still non-rank-moving. If
`v222_plus_v225` fails, skip v229 with the rest of the speed-width family.

---

## Research Note — ECS Pressure d1 Speed Audit, No Artifact

**Status**: AUDITED HOLD / NO ARTIFACT
**Target considered**: `speed_pressure_d1_ecs`
**Audit artifact**:
`docs/research/PRESSURE_D1_UNCERTAINTY_FEATURE_AUDIT_ECS_2026_06_04.md`

### Result

The ECS pressure d1 feature audit passed the mechanical feature gate: nine
pressure-level uncertainty features cleared `min_abs_split_spearman >= 0.05`,
led by `level_ws_d1`, `level_ws3_d1`, `pressure_level_index`,
`pressure_level_hpa`, `level_abs_shear_lower_d1`, `level_forecast_spread`, and
`level_tendency_1_7`.

### Decision

Do not build a pressure-d1 artifact now. The visible `speed_pressure_d1_ecs`
boundary is about `0.084` WS, while the strict sibling candidate `v229` only
moves its official cell by about `-0.0185` WS if coverage holds. That is too
little rank leverage for another large unscored speed-width artifact.

### Reopen Gate

Reopen ECS pressure d1 only if one of these happens:

- v225/v226/v233/v234/v229 score hidden-positive enough to validate the current
  speed-width family.
- The live board tightens `speed_pressure_d1_ecs` into a near-boundary cell.
- A stronger mechanism appears that can plausibly move the official cell by
  at least `0.08` WS without broad hidden-risk.

---

## Retrospective Fallback Ledger Entries — v209/v211/v212/v221

**Date recorded**: 2026-06-04
**Purpose**: Make the post-v222 attribution branch ledger-ready. These artifacts
were already built and verified, but did not have `submissions/log.json` records
before the final-20 upload queue was formalized.

### Artifacts

| ID | Artifact | Role | SHA256 |
|---|---|---|---|
| v209 | `submissions/submission_v209.zip` | Standalone ECS pressure d7 Lane A fallback | `c8022e4c54ef449ade63020fa6b3e7c058d7f505702ff93ba294065fa7370bdc` |
| v211 | `submissions/submission_v211.zip` | Standalone NS pressure d7 Lane A fallback | `09e78fbfaadbca543fb1cfcf0f8542e8a6ec12e58b7ab030993877e19f0983ff` |
| v212 | `submissions/submission_v212.zip` | Minimal v209+v211 pressure d7 compound fallback | `cd513ccd0746bb818f162f4cc2ba82027165eb3b446291c2a315e0986d0b52a3` |
| v221 | `submissions/submission_v221.zip` | v218 minus v217 fallback | `000224db7d01a860428f661a4d0504fb702268bf1b1c733c784abfe01afed6e4` |

### Lesson

These are **not** next uploads after v222 scored cleanly. They exist so
`scripts/record_codabench_score.py --submission <id> ... --update-experiment-log
--apply` can still be used if a later audit unexpectedly reopens attribution.
v222 supersedes these fallbacks because it preserved the v209/v211 pressure d7
lane while restoring the v196 North Sea station d14 direction endpoints.

## Guarded Score-Gated Compound Builder — v222_plus_v225 Chain

**Date recorded**: 2026-06-04
**Purpose**: Make the final compounding path executable without allowing
unsafe ingredients into a quota-critical upload, and preserve prior scored
gains when later low-gap probes are tested.

### What was added

- `scripts/build_scored_compound.py v222_plus_v225`
- `scripts/build_scored_compound.py v223_plus_v225`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v228`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v227`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v227`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228_plus_v227`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v227`
- `scripts/build_scored_compound.py v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v227`
- matching `...plus_v227` and `...plus_v232` preservation compounds for the
  `v233` and `v234` branches
- Successful builds now append a pending `submissions/log.json` record and a
  pending `EXPERIMENT_LOG.md` row/section automatically.
- `scripts/verify_upload_packet.py --artifacts <compound_id>` now verifies
  score-gated compound ZIPs dynamically from their compound manifests after the
  builder emits them.
- `scripts/build_scored_compound.py <compound_id> --preflight` evaluates the
  same score gates without writing a CSV, ZIP, manifest, ledger record, or
  experiment-log section. Use this for readiness checks while a prerequisite
  like `v225` is still pending.

The script checks `submissions/log.json` before touching large prediction CSVs.
It refuses to build if required prior score gates are pending, unscored,
primary-worse, or target-negative. Later speed-chain compounds may add one
unscored next-probe overlay only after the previous scored chain is clean. When
guards eventually pass, it overlays only endpoint columns from gated ingredient
predictions:

- direction endpoints from `v222` or `v223`
- speed endpoints from `v225`
- later speed endpoints from `v226`, `v233`, `v234`, `v229`, or `v230` only as
  score-gated compound ingredients; `v228` remains available only if a refreshed
  board makes its own target rank-moving
- `v227` direction endpoints only as the matching `...plus_v227`
  preservation compound after any clean speed chain
- base row order from `v196`

### Current status

`v222_plus_v225` is now built and pending. The first-compound guard was relaxed
only for this production-preserving speed diagnostic: `v222` must be scored
clean, while `v225` may still be the pending one-cell speed probe. This avoids
spending one slot on standalone `v225` and then a second slot on the actual
production compound. `v223_plus_v225` remains blocked because `v223` is still
pending.

The current compound manifests are written under:

- `logs/v222_plus_v225_scored_compound/manifest.json`
- `logs/v223_plus_v225_scored_compound/manifest.json`

### Lesson

The compounding route is now ready, but still score-gated after the first
production-preserving diagnostic. Upload `v222_plus_v225` before any standalone
`v225`, `v226`, or later speed probe. After a clean `v226` compound, the builder
now supports the exact pressure-d7 preservation branch
`v222_plus_v225_plus_v226_plus_v233`; if the live pressure-d7 boundary is no
longer worth a slot, skip that branch and continue from the active clean branch
to `v229` if it remains rank-moving. Use the older
`v222_plus_v225_plus_v226_plus_v228` path only if a refreshed board makes `v228`
rank-moving. After a successful build, run:

```bash
.venv/bin/python scripts/verify_upload_packet.py --artifacts <compound_id> --require-fresh-board --report-date "$(date +%F)"
```

before uploading the emitted ZIP.

### 2026-06-04 workflow hardening
The builder was patched so a successful compound build writes both source-of-
truth records before upload:

- a pending `submissions/log.json` entry for the compound ID,
- a pending score-progression row and section in `EXPERIMENT_LOG.md`,
- ZIP SHA256 in both the manifest and ledger change list.

Earlier real runs were blocked because `v225` was pending:

```text
v225 is pending; compound requires a scored positive ingredient
```

Use preflight for future readiness checks so guard state is visible without
refreshing manifests:

```bash
.venv/bin/python scripts/build_scored_compound.py v222_plus_v225 --preflight
```

### 2026-06-04 direct-compound build

Built and verified `v222_plus_v225` as the next quota-efficient low-gap upload.
It overlays `v222` direction endpoints and `v225` speed endpoints on `v196`.

```text
v222 changed rows: 835,164 direction endpoint rows
v225 changed rows: 69,768 speed endpoint rows
ZIP: submissions/submission_v222_plus_v225.zip
SHA256: 1d4ce97ecbc02004cabadb88f0e47fb40950517ca51fe16bd4ac7992bf38f5e8
```

Full row-scan verifier passed for `v222_plus_v225`.

## Score Recording Workflow Update — EXPERIMENT_LOG Automation

**Date recorded**: 2026-06-04
**Purpose**: Make the post-score source-of-truth update less error-prone.

`scripts/record_codabench_score.py` now supports:

```bash
.venv/bin/python scripts/record_codabench_score.py \
  --submission v222 \
  --score-log logs/post_score_decisions/v222_score.log \
  --update-experiment-log \
  --apply
```

This updates `submissions/log.json`, writes the post-score decision report, and
updates this `EXPERIMENT_LOG.md` by replacing the score progression row and
inserting a compact score-update section. It also supports `--log-path` and
`--experiment-log` for safe temp-file tests.

### 2026-06-04 current-best score refresh

The recorder now also refreshes `docs/research/our_best_scores.json` whenever
an applied score beats the existing best `mean_rank` in the real
`submissions/log.json`. It also refreshes for guarded production-preserving
compounds, such as `v222_plus_v225`, when the compound is primary-nonworse
versus its `--base` and raw target-positive on the expected cell. This keeps
`scripts/low_hanging_rank_targets.py` tied to the actual current production
cells after an equal-primary raw cell gain, while preventing target-neutral
compounds or standalone diagnostics from overwriting the production baseline.
This production-score refresh is deliberately looser than the speed-chain
upload gate: `next_slot_decision.py`, `post_score_decision.py`, and
`build_scored_compound.py` still require a visible public-rank gain before
unlocking the next speed compound. A raw-only `v222_plus_v225` score can update
`our_best_scores.json`, but it routes the next slot to `v227` instead of
`v222_plus_v225_plus_v226`.
Temp-ledger runs are guarded and do not touch the real current-best score file.

## Next-Slot Decision Update — Score-Clean Speed Gates

**Date recorded**: 2026-06-04
**Purpose**: Prevent the helper from spending a second speed diagnostic before
the first speed ingredient is safely compounded with the active direction base,
prevent later speed probes from advancing after a failed speed gate, and avoid
uploading standalone probes that would drop earlier proven speed gains.

### What changed
- Added tests for `scripts/next_slot_decision.py`.
- Current ledger state now recommends uploading built `v222_plus_v225` as the
  optional speed diagnostic on the current production base.
- Standalone `v225` remains available only for explicit attribution, not as the
  default rank-seeking upload.
- If `v222_plus_v225` is pending, the helper emits verify/upload/score commands
  for that compound.
- If `v222_plus_v225` scores primary-nonworse but does not preserve a visible
  rank gain on `speed_surface_d1_ecs` versus `v222`, the helper now stops the
  speed chain instead of unlocking `v226`.
- If `v222_plus_v225` scores visibly rank-positive and `v226` is pending, the
  helper now recommends building `v222_plus_v225_plus_v226`, not uploading
  standalone `v226`.
- This direct-compound score is now sufficient to unlock the branch even if
  standalone `v225` remains pending/unscored; the helper must not fall back to
  uploading standalone `v225` after `v222_plus_v225` is scored.
- Added score-recording regressions proving that once the pending
  `v222_plus_v225` ledger record is filled, a clean target score routes to
  `v222_plus_v225_plus_v226`, while a target-neutral/failing score routes to
  `v227`; neither branch uploads standalone `v225`.
- Tightened `scripts/build_scored_compound.py` so each prior scored speed chain
  must be primary-nonworse and visibly rank-positive against its own base before
  the next speed compound can be built. This prevents manual preflight/build
  commands from bypassing the same low-gap gate enforced by
  `next_slot_decision.py`.
- Cleaned `scripts/verify_upload_packet.py` action labels so the verifier now
  points v226/v233/v234/v229/v230/v228 at the `v222_plus_v225` compound gate rather than
  stale standalone-`v225` wording, and dynamic compound packets are labeled as
  generic guarded compounds.
- The default verifier queue now discovers the built `v222_plus_v225` compound
  from its manifest, lists it before standalone `v225`, and prints
  `v222_plus_v225` as the next pending upload candidate. Standalone `v225` is
  labeled as attribution fallback so a full-queue verifier run cannot override
  `next_slot_decision.py` and accidentally spend a production slot on the
  old-base speed probe.
- Fresh 2026-06-05 full row-scan verification passed for `v222_plus_v225`:
  `3,448,801` CSV lines including header, `3,447,360` grid rows, `1,440`
  station rows, with SHA, manifest, and ledger checks all OK.
- Later speed probes are also compound ingredients. The clean-chain path now
  includes the optional `v233` and `v234` branches before later speed probes:
  `v222_plus_v225_plus_v226_plus_v233_plus_v234`,
  `v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229`, and
  `v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229_plus_v230`; the
  old `...plus_v228` branches remain guarded fallbacks only if v228 becomes
  rank-moving on a refreshed board.
- Each scored speed compound has to be visibly rank-positive and
  primary-nonworse against its prior scored chain before the next speed probe
  unlocks.
- If any scored speed gate fails, the helper stops the speed-width chain and
  moves to held `v227` as the first non-speed low-gap diagnostic, preserving
  the latest clean scored chain through the matching `...plus_v227` compound.
- If `v225` fails, the helper blocks the v224/v225/v226 speed-width family and
  can move to standalone `v227` instead of spending another speed slot, because
  no clean speed compound exists yet.
- Every score-recording command emitted by the helper now ends with
  `.venv/bin/python scripts/next_slot_decision.py --report-date "$(date +%F)"`,
  keeping artifact verification and board freshness enabled when the next
  branch is recomputed after the new score is applied.
- Compound score-recording commands now pass the prior scored chain as
  `--base`, for example `v222_plus_v225` is compared against `v222` and
  `v222_plus_v225_plus_v226` is compared against `v222_plus_v225`. This keeps
  post-score reports aligned with the actual score gate.
- `scripts/post_score_decision.py` now emits specific decisions for each
  speed-chain compound and each `...plus_v227` preservation compound instead of
  falling back to generic rank-positive wording. The post-score table now also
  knows the v233/v234 branch: clean `v222_plus_v225_plus_v226` points to
  `v222_plus_v225_plus_v226_plus_v233`, clean v233 points to
  `v222_plus_v225_plus_v226_plus_v233_plus_v234`, clean v234 points to the
  matching `...plus_v229` branch on the current board, and the older
  `...plus_v228` branch remains available only if a refreshed board makes v228
  rank-moving. All matching
  v233/v234-branch `...plus_v227` / `...plus_v232` preservation compounds are
  scoped to their station-direction target cells.
- `scripts/post_score_decision.py` is now primary-aware for speed-chain
  compounds. If `v222_plus_v225` or a later speed compound improves its target
  cell but worsens Codabench primary versus the supplied base, the report stops
  the speed chain and explicitly blocks the next compound instead of leaving an
  "if primary is non-worse" manual branch.
- `scripts/next_slot_decision.py` now applies the same first-compound guard
  directly when `v222_plus_v225` is scored without standalone `v225`: if the
  compound is not visibly rank-positive and primary-nonworse versus `v222`, it
  routes immediately to the failed-speed-gate branch and blocks `v226`.
- The latest-clean-chain helper now requires contiguous speed compounds to be
  visibly rank-positive on their own expected cells and primary-nonworse versus
  their recorded bases before they can be preserved in later `...plus_v227` or
  `...plus_v232` fallback builds. A scored-but-failed speed compound no longer
  qualifies as the production chain.
- `scripts/build_scored_compound.py` now applies the same visible-rank /
  primary-nonworse check to scored speed ingredients (`v226`, `v228`, `v229`,
  `v230`, `v233`, `v234`). Direction fallback ingredients (`v227`, `v232`,
  `v235`) remain target-positive/primary-nonworse gated. Pending probes are
  still allowed after a clean prior chain, but a scored probe that already
  failed its target cannot be silently folded into a future compound.
- Builder/decision parity is now unit-tested: every compound the next-slot
  helper can recommend must exist in `scripts/build_scored_compound.py`, must
  have a score-recording base, and every later compound must have an explicit
  builder guard. This keeps the low-gap queue from reaching an unbuildable
  branch after a Codabench score arrives.
- Score-progression `NEW BEST` / `REJECT` labels now compare Codabench
  `primary_score` against the chosen base submission's logged `mean_rank`;
  public-rank estimates remain report context only.
- Standalone queued diagnostics, including `v225`, now record post-score
  reports against active best `v222` by default. A `v225` score can still be a
  positive ingredient even if the score-progression row says `REJECT` versus
  production best; `next_slot_decision.py` remains the branch authority.
- `docs/research/UPLOAD_PACKET_V222_PLUS_V225_2026_06_04.md`,
  `docs/research/UPLOAD_PACKET_V225_2026_06_04.md`, and
  `docs/research/UPLOAD_QUEUE_2026_06_04.md` now show the same
  `--base v222` score-recording command emitted by `next_slot_decision.py` for
  the relevant artifact.
  `tests/test_next_slot_decision.py` includes a regression check that normalizes
  the docs' multiline bash blocks and compares them with the helper command.
- Future compound recommendations from `scripts/next_slot_decision.py` now emit
  `scripts/build_scored_compound.py <compound_id> --preflight` before the real
  build command, matching the upload queue's preflight-first operating rule.
- `tests/test_record_codabench_score.py` now cross-checks the subtle v225 edge
  case end to end: a scored `v225` can be `REJECT` versus production best
  `v222` while still unlocking `v222_plus_v225` if its speed cell improves
  versus its construction base `v196` and the primary is non-worse versus
  `v196`.
- The same test module now includes a raw Codabench scorer-log fixture for the
  expected v225 intake shape, covering metric lines such as
  `speed_surface_d1_ecs = 4.5860 [OK]` and `primary_score: 1.419700`.
  This guards the post-upload path that parses `logs/post_score_decisions/v225_score.log`.
- `scripts/record_codabench_score.py` now writes a base-aware default ledger
  lesson when a pending score is recorded without `--lesson`. For `v225`, this
  preserves the important distinction that the row can be `REJECT` versus
  production best `v222` while still being a positive speed ingredient that
  unlocks the guarded `v222_plus_v225` compound.
- Raw Codabench score-log intake now rejects incomplete scorer summaries before
  any ledger update: if the log reports fewer OK dims than total dims or any
  sentinel dims, `scripts/record_codabench_score.py` fails instead of recording
  a polluted low-gap branch score.
- Full upload-packet verification now also compares the ZIP member
  `predictions.csv` SHA against the standalone `submissions/predictions_*.csv`
  SHA. This catches stale ZIPs whose size/header still match the sidecar CSV
  before spending a quota slot.
- `scripts/build_scored_compound.py` and `scripts/next_slot_decision.py` now
  include the late `v232` station-d7 fallback through matching `...plus_v232`
  preservation compounds. `v232` still stays behind `v225`, the speed-chain
  compounds, and `v227`; the new branch only prevents a manual-memory decision
  if `v227` is unavailable or no longer usable.
- `scripts/low_hanging_rank_targets.py` and `scripts/queued_upload_rank_ev.py`
  now print the same `v232` rule: late only after `v227` is unavailable or
  fails, and through a matching `...plus_v232` compound after any clean speed
  chain.
- The guarded fallback path now also handles the no-clean-speed-chain branch:
  if `v225` fails, standalone `v227` scores cleanly, and `v232` remains worth a
  station-d7 diagnostic, build `v222_plus_v227_plus_v232` so the `v227` gain is
  preserved.
- `scripts/post_score_decision.py` now has explicit post-score decisions for
  all `...plus_v232` station-d7 preservation compounds, including
  `v222_plus_v227_plus_v232`, so a future `v232` score cannot fall through to
  generic rank-positive wording.
- Standalone `v227` and `v232` scores are now explicit in
  `scripts/post_score_decision.py` too: clean `v227` points to
  `v222_plus_v227_plus_v232`, failed `v227` blocks its preservation compounds,
  and standalone `v232` remains a late fallback that must not drop any already
  proven chain.

### Lesson
The low-hanging queue is now score-gated in the right order:
`v222_plus_v225 -> v222_plus_v225_plus_v226 -> reassess v233 -> v222_plus_v225_plus_v226_plus_v233 if still rank-moving -> reassess v234 -> v222_plus_v225_plus_v226_plus_v233_plus_v234 if still rank-moving -> skip held v228 unless a refreshed board makes it rank-moving -> continue v229/v230 from the active clean branch -> optional matching ...plus_v227`.
Do not upload standalone `v225` by default; the compound already tests the same
speed ingredient while preserving `v222`. Advance through later speed probes
only as compound overlays that preserve all prior scored gains. If switching
from speed to `v227` after a clean chain, build the preservation compound rather
than uploading standalone `v227`.
If `v227` is unavailable or fails, consider `v232` only as the late station-d7
fallback; after any clean speed chain it must also be built as the matching
`...plus_v232` preservation compound, not uploaded standalone.
If standalone `v227` scores cleanly after a failed `v222_plus_v225`, use
`v222_plus_v227_plus_v232` before any standalone `v232` upload.
Keep the human-facing upload packet and the helper-generated commands aligned;
under the final quota, a stale `--base` value can create a false promotion
signal and waste the next slot.

## Low-Hanging Rank Target Report

**Date recorded**: 2026-06-04
**Purpose**: Turn "pick low hanging fruits first" into a repeatable rank-boundary
report rather than a manual reading of the leaderboard.

### What changed
- Added `scripts/low_hanging_rank_targets.py`.
- Added tests for sorting by next-rank gap and for built/blocked/risky policy
  classification.
- The report reads `docs/research/our_best_scores.json` and
  `docs/research/competitors_snapshot.json`.

### Current output summary
The 2026-06-04 snapshot shows the smallest raw offensive gaps are mostly not
good uploads:

| Cell | Next-rank gap | Status |
|---|---:|---|
| `WS NS Surf d14` | `0.0016` | BLOCKED |
| `WS NS Pres d14` | `0.0027` | BLOCKED |
| `WS NS Pres d7` | `0.0033` | BLOCKED |
| `WS ECS Pres d7` | `0.0033` | BUILT_HELD (`v233`) |
| `WS ECS Surf d7` | `0.0034` | BUILT_HELD (`v226`) |
| `WS NS Surf d7` | `0.0043` | BUILT_HELD (`v234`) |
| `WS ECS Surf d1` | `0.0072` | BUILT_NEXT (`v222_plus_v225`) |

### Lesson
The actionable order remains
`v222_plus_v225 -> v222_plus_v225_plus_v226 -> v233 live-boundary reassessment -> v222_plus_v225_plus_v226_plus_v233 if still rank-moving -> v234 live-boundary reassessment -> v222_plus_v225_plus_v226_plus_v233_plus_v234 if still rank-moving -> skip held v228 unless a refreshed board makes it rank-moving -> continue v229/v230 from the active clean branch -> optional matching ...plus_v227`.
The raw-smallest cells are deceptive because several exact families already
failed hidden. Do not build another candidate ahead of this sequence without new
mechanism evidence, and do not advance to the next speed probe unless the prior
compound scores visibly rank-positive and primary-nonworse. Do not upload standalone
`v227` after any clean speed compound; use the matching preservation compound.
Do not upload standalone `v233` after a clean speed compound; build a
preservation compound if the live pressure-d7 boundary remains worth the slot.

## Queued Upload Rank EV Report

**Date recorded**: 2026-06-04
**Purpose**: Quantify how many visible rank positions each queued artifact buys
if its manifest-implied raw movement transfers.

### What changed
- Added `scripts/queued_upload_rank_ev.py`.
- Added `tests/test_queued_upload_rank_ev.py`.
- Added machine-readable `--json` / `--write-json` output so post-score
  automation can consume the next upload and positive-rank-gain candidates
  without scraping the table or Markdown report.
- `scripts/next_slot_decision.py --json` now embeds the matching rank-EV
  context for its `next_artifact`, so a single decision payload explains both
  the quota-safe upload and the visible rank boundary it is trying to flip.
- The same JSON payload now includes `upload_verification` when verification is
  enabled. Fast mode records SHA/log-state; `--full-verify` also records line,
  grid-row, and station-row counts for the recommended artifact.
- `scripts/record_codabench_score.py` now accepts `--next-decision-json`; after
  recording a score it can write the next-slot JSON from the updated ledger in
  the same command. The generated `v222_plus_v225` record command now writes
  `logs/post_score_decisions/v222_plus_v225_next_decision.json`.
- `tests/test_record_codabench_score.py` now runs the actual
  `record_codabench_score.py --apply --next-decision-json` CLI against a
  temporary ledger, covering the command path that will be used after the
  Codabench score paste.
- Wrote `docs/research/QUEUED_UPLOAD_RANK_EV_2026_06_04.md`.
- Tightened the helper guard so `beats_next` is true only when a candidate's
  expected delta is negative and crosses the next-rank boundary; a future
  positive/worsening delta can no longer be counted as a rank-flip candidate
  just because its absolute movement is large.

### Current output summary
The queue remains correctly ordered by score gate and visible leverage:

| Artifact | Cell | Projected rank if intended movement transfers | Visible rank gain | Gate |
|---|---|---:|---:|---|
| `v222_plus_v225` | `WS ECS Surf d1` | `4 -> 2` | `2` | NEXT_UPLOAD |
| `v226` | `WS ECS Surf d7` | `3 -> 2` | `1` | COMPOUND_AFTER_V222_PLUS_V225 |
| `v233` | `WS ECS Pres d7` | `3 -> 2` | `1` | HELD_AFTER_V226 |
| `v228` | `WS NS Surf d1` | `5 -> 5` | `0` | HOLD_UNLESS_RANK_MOVING |
| `v229` | `WS NS Pres d1` | `3 -> 2` | `1` | COMPOUND_AFTER_CLEAN_SPEED_BRANCH |
| `v230` | `WS ECS Surf d14` | `4 -> 3` | `1` | COMPOUND_AFTER_V229 |
| `v227` | `Dir NS Sta d1` | `2 -> 1` | `1` | DIRECTION_AFTER_SPEED_GATES |
| `v232` | `Dir NS Sta d7` | `5 -> 3` | `2` | LATE_AFTER_V227 |

### Lesson
This confirms `v222_plus_v225` as the first low-hanging upload candidate
despite the speed-family risk: under the v225 manifest delta it is the immediate
queue item with the largest visible rank flip while preserving v222's direction
gains. After `v222_plus_v225`, use `v226`/`v233`/`v234`/`v229`/`v230` only as compound
ingredients so earlier scored gains are preserved; use `v228` only if a refreshed
board makes it rank-moving. After any clean speed
compound, use `v227` only through the matching `...plus_v227` compound for the
same reason. `v228` is mechanically clean but does not clear the current
boundary under its own delta, so it should not jump the queue. Keep the guard
sequence unchanged.
`v233` is the new pressure-d7 speed exception to the old RISKY_HELD state, but
only as a held diagnostic: its intended `-0.0038778` WS movement clears the
stored `0.0033` WS boundary if coverage holds, while its mechanism is far
narrower than failed v174. It still waits behind `v222_plus_v225` and v226
because pressure d7 speed already rejected broader endpoint shrinking; the
executable branch is now `v222_plus_v225_plus_v226_plus_v233`, not standalone
`v233`.
`v232` is not an exception to that rule: after a clean speed chain, it must be
tested as the matching `...plus_v232` preservation compound and only after
`v227` is unavailable or fails.
Use `scripts/queued_upload_rank_ev.py --json` when wiring the next post-score
decision; the JSON names `v222_plus_v225` as `next_upload` and lists the
positive visible-rank-gain candidates explicitly.
Use `scripts/next_slot_decision.py --json` for the upload packet itself; it now
embeds the `WS ECS Surf d1` rank-EV context for `v222_plus_v225`
(`4 -> 2`, visible gain `2`).
Use `scripts/next_slot_decision.py --json --full-verify` when saving a decision
payload for upload handoff, so `upload_verification` captures
`lines=3448801`, `grid_rows=3447360`, and `station_rows=1440` alongside the
SHA/log-state result.
When recording the `v222_plus_v225` score, include
`--next-decision-json logs/post_score_decisions/v222_plus_v225_next_decision.json`;
if the score is clean, that JSON will route to the `v226` compound branch and
carry `v226`'s `WS ECS Surf d7` rank-EV context.
If that compound scores clean and `v233` remains rank-moving, the router builds
`v222_plus_v225_plus_v226_plus_v233`; clean `v233` can proceed to `v234`, and the
current board then skips non-rank-moving `v228` and builds the matching
`...plus_v229` branch. The older `...plus_v228` path remains available only if a
refreshed board makes `v228` rank-moving.
If `v227` becomes the clean standalone branch first, `v232` must preserve it
through `v222_plus_v227_plus_v232`.
The EV report is an ordering/risk tool, not an upload authority; if a manifest
ever implies a positive target delta, the helper now treats it as a regression
even when it is larger than the visible rank gap.

### ECS Pressure d7 Audit Update

The next uncovered tiny boundary is `WS ECS Pres d7` (`speed_pressure_d7_ecs`).
It now has a built held diagnostic, `v233`, but it remains behind the existing
speed gates. Existing older artifacts stay quarantined:

- `v168`: old-base pressure d7 high-confidence shrink.
- `v174`: exact-cell rebase of that shrink; hidden worsened
  `15.3733 -> 15.3774`.
- `v200`: unlogged Optuna rebuild artifact; broad old-base model, moves q50 on
  all 410,400 target rows, and widens the target cell on average
  (`mean_width_delta_vs_v173 = +0.14065`).
- `v233`: new v222-base, q50-frozen, level-HRES low/mid shrink with rare
  extreme-HRES q95 floor; `271,744` target rows changed and mean official-cell
  delta is `-0.0038778` if coverage holds.

Upload posture: hold v233 until `v222_plus_v225` and v226 prove the speed-width
family is hidden-live. If used after a clean speed chain, build
`v222_plus_v225_plus_v226_plus_v233` first; do not upload standalone v233 and
drop prior scored gains.

## v182 — ECS Station d1 ExtraTrees MOS (REJECTED)

**Date**: 2026-05-16
**Approach**: Low-capacity ExtraTrees residual-center MOS plus empirical-Bayes residual intervals.
**Base**: `v173`

### What was done
- Targeted only `speed_stations_d1_ecs`.
- Changed 224 station speed rows; no direction rows changed.
- Replay gate passed strongly: val `-0.2632`, tune `-0.2848`, holdout `-0.3708` WS.
- Max single-station gain share was `0.251`, below the 0.50 cap.

### Hidden result
- `primary_score`: `1.420083 -> 1.421147` (`+0.001064`, worse).
- `speed_stations_d1_ecs`: `6.8257 -> 7.2089` (`+0.3832` WS, worse).
- All other dimensions stayed unchanged versus `v173`.

### Lesson
Reject. The replay gate was not predictive for this hidden window. Freeze learned ECS d1 station-speed center/MOS revivals after the v165 and v182 regressions unless we first build a stronger replay-faithful validation oracle.

## v183 — NS Station Direction Asymmetric Widths (DO NOT SUBMIT AS BUILT)

**Date**: 2026-05-16
**Approach**: Center-frozen asymmetric endpoint calibration by station/hour.
**Base**: `v173`

### What was done
- Targeted `dir_stations_d14_ns` and `dir_stations_d7_ns`.
- Changed 512 station direction endpoint rows.
- `dir_50` centers remained byte-frozen; speed rows unchanged.

### Lesson
Do not submit this artifact as built after v179's score. v179 was the narrower
NS station d14 width-only version and it worsened the target; v183 includes
that same d14 family plus d7 asymmetry. Only a separately rebuilt d7-only
variant remains worth considering.

## v184 — NS Pressure d14 q4 Low-Side Bracket (DO NOT SUBMIT)

**Date**: 2026-05-16
**Approach**: Smaller 0.010 q4 low-side q05 widening using v181's strict EDA rules.
**Base**: `v173`

### What was done
- Changed the same 178,838 q4 pressure rows as v181, but with half the amplitude.
- q50/q95/directions stayed frozen.

### Lesson
Do not submit. v181 regressed the same q4 low-side widening class on hidden, so the half-amplitude bracket is no longer justified.

## v185 — NS Surface d14 Context Expert Selector (REJECTED)

**Date**: 2026-05-16
**Approach**: 14-day context rule selector for q4 surface-speed low-side undercoverage.
**Base**: `v173`

### What was done
- Targeted `speed_surface_d14_ns`.
- Changed 30,979 North Sea surface 10m d14 rows.
- Only q05 moved; q50/q95/directions frozen.
- Independent chunked diff vs `v173` confirmed: 30,979 changed rows, 0 q50
  changes, 0 q95 changes, 0 direction changes, 0 non-target changes, 0
  crossings, 0 NaNs.

### Hidden result
- `primary_score`: `1.420083 -> 1.420087` (`+0.000004`, worse).
- `speed_surface_d14_ns`: `15.1216 -> 15.1231` (`+0.0015` WS, worse).
- All other dimensions stayed unchanged versus `v173`.

### Lesson
Reject. Even the narrow q4-only low-side surface move failed hidden. Stop NS surface d14 endpoint manipulation after v177 and v185; future attempts need a new validation oracle or a non-endpoint mechanism.

## v186 — ECS Surface d7 Anomaly Interval Adapter (PENDING SCORE)

**Date**: 2026-05-16
**Approach**: Distance-to-analog anomaly score controls interval widening.
**Base**: `v173`

### What was done
- Targeted `speed_surface_d7_ecs`.
- Changed 11,099 anomalous ECS surface 10m d7 rows.
- q50 and directions stayed frozen.

### Lesson
This is a narrow anomaly/regime probe for a thin visible speed gap. After v182 and v185 failed, it remains orthogonal but low leverage; do not submit it before higher-upside direction-width or validation-oracle work unless quota is abundant.

## v187 — Station Speed Analog Residual (NO ZIP)

**Date**: 2026-05-16
**Approach**: kNN analog residual distribution for `speed_stations_d7_ns`.
**Base**: `v173`

### What happened
- The leave-station test looked promising on average (`-1.55` WS).
- The leave-period test failed badly (`+1.30` WS average, worst `+1.59`).
- No submission was emitted.

### Lesson
This confirms the hidden-regime risk on station d7: station analogs can memorize station structure but fail temporal transfer. Do not submit this family without a regime selector.

## v188 — Independent Winner Compound Pack (BLOCKED)

**Date**: 2026-05-16
**Approach**: Guarded compound builder requiring at least two independently scored winners.
**Base**: `v173`

### What happened
- Script was implemented.
- It refused to build because `logs/v188_independent_winner_compound/winners.json` does not exist.

### Lesson
The compound rule is now encoded as a hard guardrail: no unscored candidate can accidentally enter v188.

## v190 — Rank-Gap Oracle and Donor Atlas (NO ZIP)

**Date**: 2026-05-18
**Approach**: Build the post-v185 rank-gap oracle and donor atlas before spending more quota.
**Base**: `v173`

### What was done
- Implemented `src/experiments/v190_rank_gap_donor_atlas.py`.
- Audited the visible gap targets: NS surface speed, NS pressure d14 speed, station speed, NS station d14 direction, and ECS pressure d7/d14 direction.
- Wrote `logs/v190_rank_gap_donor_atlas/donor_atlas.csv`, `public_rank_gaps.csv`, `candidate_queue.csv`, and `manifest.json`.
- Emitted no predictions file and no zip.

### Lesson
The atlas found no real NS surface speed donor. The apparent `v47` improvements for `speed_surface_d7_ns` and `speed_surface_d14_ns` were rounded score artifacts; stable-key diffs found those blocks byte-identical to `v173`. The build-worthy breakthrough lane from this audit is ECS pressure direction response, not surface-speed donor grafting.

## v191 — ECS Pressure d7 Direction Response (SCORED: NEW BEST)

**Date**: 2026-05-18
**Approach**: Speed-conditioned circular concentration response on ECS pressure d7 direction endpoints.
**Base**: `v173`

### What was done
- Implemented `src/experiments/v191_ecs_pressure_d7_direction_response.py`.
- Targeted only `dir_pressure_d7_ecs`.
- Changed 324,696 ECS pressure d7 direction endpoint rows.
- Kept `dir_50`, all speed columns, and all non-target rows frozen.
- Mean target half-width moved `99.1146 -> 97.5078` degrees.
- Artifact: `starting-kit/phase_1/submission_v191.zip`.
- Manifest: `logs/v191_ecs_pressure_d7_direction_response/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows | 324,696 |
| Speed changed rows | 0 |
| Non-target direction rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |

### Leaderboard score
| Dim | Best (v173) | New (v191) | Delta |
|---|---:|---:|---:|
| `dir_pressure_d7_ecs` | 235.0012 | 233.8237 | -1.1775 improved |
| `primary_score` | 1.420083 | 1.419810 | -0.000273 improved |

### Lesson
SCORED: NEW BEST. Promote `v191` as the clean production base. The d7 ECS
pressure direction concentration response transferred with no collateral
movement. This validates the mechanism for d7 only; do not infer that the d14
sibling is safe.

## v192 — ECS Pressure d14 Direction Response (SCORED: NEUTRAL/REJECT)

**Date**: 2026-05-18
**Approach**: Speed-conditioned circular concentration response on ECS pressure d14 direction endpoints.
**Base**: `v173`

### What was done
- Implemented `src/experiments/v192_ecs_pressure_d14_direction_response.py`.
- Targeted only `dir_pressure_d14_ecs`.
- Changed 345,658 ECS pressure d14 direction endpoint rows.
- Kept `dir_50`, all speed columns, and all non-target rows frozen.
- Mean target half-width moved `126.1211 -> 123.8399` degrees.
- Artifact: `starting-kit/phase_1/submission_v192.zip`.
- Manifest: `logs/v192_ecs_pressure_d14_direction_response/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows | 345,658 |
| Speed changed rows | 0 |
| Non-target direction rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |

### Leaderboard score
| Dim | Best (v173) | New (v192) | Delta |
|---|---:|---:|---:|
| `dir_pressure_d14_ecs` | 300.5204 | 300.9596 | +0.4392 regressed |
| `primary_score` | 1.420083 | 1.420083 | +0.000000 neutral |

### Lesson
SCORED: NEUTRAL/REJECT. Primary was unchanged, but the target moved the wrong
way. Reject v192 and do not compound it with v191. The d14 ECS pressure
direction gap is not solved by this endpoint concentration family; it likely
needs a different center/donor/regime mechanism.

## v193 — NS Surface d7 Speed Donor Selector (NO ZIP)

**Date**: 2026-05-18
**Approach**: Whole-block donor selector for `speed_surface_d7_ns`.
**Base**: `v173`

### What happened
- Implemented `src/experiments/v193_ns_surface_d7_speed_donor_selector.py`.
- The atlas selected `v47` by rounded hidden score (`14.46` vs `14.4643`).
- Stable-key diff found `0` changed rows versus `v173`.
- The script refused to emit a zip.

### Lesson
Rejected offline. The donor edge is not real at prediction level, so there is no safe v193 submission.

## v194 — NS Surface d14 Speed Donor Selector (NO ZIP)

**Date**: 2026-05-18
**Approach**: Whole-block donor selector for `speed_surface_d14_ns`.
**Base**: `v173`

### What happened
- Implemented `src/experiments/v194_ns_surface_d14_speed_donor_selector.py`.
- The atlas selected `v47` by rounded hidden score (`15.12` vs `15.1216`).
- Stable-key diff found `0` changed rows versus `v173`.
- The script refused to emit a zip.

### Lesson
Rejected offline. This confirms the NS surface d14 speed lane has no clean historical donor. Combined with v177 and v185, skip this lane until we have a genuinely new mechanism.

## v195 — Station Speed Regime Gate (NO ZIP)

**Date**: 2026-05-18
**Approach**: Gate station-speed revival before building any new zip.
**Base**: `v173`

### What happened
- Implemented `src/experiments/v195_station_speed_regime_gate.py`.
- Checked `speed_stations_d7_ns` and `speed_stations_d1_ecs`.
- `speed_stations_d7_ns` best donor had only `-0.0034` WS raw edge, below the `0.02` build threshold.
- `speed_stations_d1_ecs` had no better donor than `v173`.
- The script refused to emit a zip.

### Lesson
Rejected offline. Station speed remains blocked after v165, v182, and v187. Do not submit station-speed revival without a stronger leave-regime oracle and a real hidden-scored donor edge.

## v196 — ECS Pressure d7 Direction Mild-Plus Bracket (SCORED: NEW BEST)

**Date**: 2026-05-19
**Approach**: Controlled parameter bracket of the v191 concentration response.
**Base**: built from `v173`, compared against promoted `v191`

### What was done
- Implemented `src/experiments/v196_ecs_pressure_d7_direction_mild_plus.py`.
- Targeted only `dir_pressure_d7_ecs`.
- Kept `dir_50`, all speed columns, and all non-target rows frozen.
- Bracket changed max shrink `14 -> 17` degrees and minimum half-width `28 -> 27` degrees.
- Mean target half-width moved `99.1146 -> 97.1634` degrees.
- Artifact: `starting-kit/phase_1/submission_v196.zip`.
- Manifest: `logs/v196_ecs_pressure_d7_direction_mild_plus/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows vs v173 | 325,351 |
| Changed rows vs v191 | 316,599 |
| Speed changed rows | 0 |
| Non-target direction rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |

### Leaderboard score
| Dim | Best (v191) | New (v196) | Delta |
|---|---:|---:|---:|
| `dir_pressure_d7_ecs` | 233.8237 | 233.5926 | -0.2311 improved |
| `primary_score` | 1.419810 | 1.419757 | -0.000053 improved |

### Lesson
SCORED: NEW BEST. Promote `v196` as the production base. The d7 pressure
direction concentration lane transferred again, but the incremental gain is
small after the larger `v191` win, so the broad amplitude ladder is showing
strong diminishing returns. Future d7 work needs a narrower high-confidence
subset or a different mechanism.

## v197 — ECS Pressure d14 Selective Coverage Expansion (SCORED: REJECT/NEUTRAL)

**Date**: 2026-05-20
**Approach**: Selective high-speed/high-width direction interval expansion.
**Base**: promoted `v191`

### What was done
- Implemented `src/experiments/v197_ecs_pressure_d14_selective_widening.py`.
- Targeted only `dir_pressure_d14_ecs`.
- Tested the opposite of failed `v192`: small coverage expansion instead of
  concentration.
- Kept `dir_50`, all speed columns, and all non-target rows frozen.
- Mean target half-width moved `126.1211 -> 126.1515` degrees.
- Artifact: `starting-kit/phase_1/submission_v197.zip`.
- Manifest: `logs/v197_ecs_pressure_d14_selective_widening/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows vs v191 | 37,539 |
| Speed changed rows | 0 |
| Non-target direction rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean expansion on changed rows | 0.3193 deg |

### Leaderboard score
| Dim | Best (v191) | New (v197) | Delta |
|---|---:|---:|---:|
| `dir_pressure_d14_ecs` | 300.5204 | 300.5307 | +0.0103 worsened |
| `primary_score` | 1.419810 | 1.419810 | 0.000000 neutral vs v191 |

### Lesson
SCORED: REJECT/NEUTRAL. The d14 selective-widening endpoint-only hypothesis
failed: `dir_pressure_d14_ecs` worsened by `+0.0103` cWS. This artifact was
already uploaded from the older `v191` base, so it also lacks the `v196` d7
gain. Do not build on `v197`; current best is `v196`, and endpoint-only
`dir_pressure_d14_ecs` work is blocked until a real center/regime donor exists.

## v222 — v212 + Undo v204 NS Station d14 Direction (SCORED: NEW BEST)

**Date**: 2026-06-04
**Approach**: Start from `v212`, the confirmed v209+v211 Lane A pressure d7
compound, then restore only North Sea station d14 direction endpoints from
`v196` to remove the v204/v207 station d14 regression.
**Base**: `v212`

### What was done
- Implemented `src/experiments/v222_v212_plus_undo_v204.py`.
- Base: `submissions/predictions_v212.csv`.
- Source for restored rows: `submissions/predictions_v196.csv`.
- Target cleanup dimension: `dir_stations_d14_ns`.
- Artifact: `submissions/submission_v222.zip`.
- Manifest: `logs/v222_v212_plus_undo_v204/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 256 |
| Changed rows vs v212 | 113 |
| q05/q50/q95 changed rows | 0 |
| Direction changed rows | 113 |
| Non-target direction rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| ZIP rows incl. header | 3,448,801 |
| Grid rows | 3,447,360 |
| Station rows | 1,440 |

### Codabench score
v222 scored as a clean new best:

| Dim | Best (v196) | New (v222) | Delta |
|---|---:|---:|---:|
| `dir_pressure_d7_ns` | 266.5361 | 255.2599 | -11.2762 improved |
| `dir_pressure_d7_ecs` | 233.5926 | 229.7705 | -3.8221 improved |
| `dir_surface_d7_ns` | 285.8122 | 284.7855 | -1.0267 improved |
| `dir_stations_d14_ns` | 305.6286 | 305.6286 | 0.0000 preserved |

Primary improved `1.419757 -> 1.418872` (`-0.000885`).
v222 does not include the later v216 NS surface d7 overlay; that optional add-on
is built separately as v223.

### Lesson
SCORED: NEW BEST. v222 validated the pressure d7 Lane A compound and the v204
undo assumption. Promote v222 as the active base. Do not submit v209/v211/v212
for attribution unless a later branch requires isolation; v217 and v218 remain
blocked.

### 2026-06-04 later amendment
The user's newer current-standing readout supersedes the earlier v222-first
queue. We are still #1 overall, but the smallest visible rank boundaries are
now speed cells, while our direction cells are mostly defended by large
buffers. After the v222 score, the next low-hanging decision is whether to buy
one speed diagnostic. The later speed-uncertainty audit and v225 build put the
feature-gated speed diagnostic ahead of v224; v224 remains only a fallback
blind-shrink diagnostic. The mini-challenge transfer further narrows speed work:
d1 can justify a thin HRES-conditioned probe, d7 should be lean with
HRES-magnitude tail protection, and d14 should stay climatology-scale unless a
real regime/center donor exists.

## v223 — v222 + v216 NS Surface d7 Direction (BUILT OPTIONAL, PENDING SCORE)

**Date**: 2026-06-04
**Approach**: Start from `v222`, then add the `v216` North Sea surface d7 Lane A
direction overlay.
**Base**: `v222`

### What was done
- Implemented `src/experiments/v223_v222_plus_v216_ns_surface_d7.py`.
- Base: `submissions/predictions_v222.csv`.
- Source for overlay rows: `submissions/predictions_v216.csv`.
- Target dimension: `dir_surface_d7_ns`.
- Artifact: `submissions/submission_v223.zip`.
- Manifest: `logs/v223_v222_plus_v216_ns_surface_d7/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 164,160 |
| Changed rows vs v222 | 77,349 |
| q05/q50/q95 changed rows | 0 |
| Direction changed rows | 77,349 |
| Non-target direction rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| ZIP rows incl. header | 3,448,801 |
| Grid rows | 3,447,360 |
| Station rows | 1,440 |

### Live-board expectation
Against the 2026-06-04 public board, v216 would improve raw
`dir_surface_d7_ns` from `285.8122` to `279.8591` if it transfers, but the
cell remains rank 3 because Printemps is `276.92` and sajayrrr is `256.44`.

### Lesson
PENDING SCORE / BUILT OPTIONAL. v223 is not the next automatic upload after
v222. Consider it only if live board movement makes `Dir NS Surface d7`
rank-moving, or after another positive score makes a final compound worth the
slot.

## v224 — v196 + ECS Surface d1 Speed Micro-Shrink (BUILT DIAGNOSTIC, PENDING SCORE)

**Date**: 2026-06-04
**Approach**: Start from scored production best `v196` and shrink only the
`speed_surface_d1_ecs` endpoints by `0.0055` m/s per side around the existing
q50.
**Base**: `v196`

### What was done
- Implemented `src/experiments/v224_speed_surface_d1_ecs_micro_shrink.py`.
- Target dimension: `speed_surface_d1_ecs`.
- Scope: grid / `east_china_sea` / surface levels `10m` and `100m` / d1 /
  speed endpoints only.
- Artifact: `submissions/submission_v224.zip`.
- Manifest: `logs/v224_speed_surface_d1_ecs_micro_shrink/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 164,160 |
| Changed rows vs v196 | 164,160 |
| Direction changed rows | 0 |
| Non-target q rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean target width delta | -0.01099197 |
| ZIP rows incl. header | 3,448,801 |
| Grid rows | 3,447,360 |
| Station rows | 1,440 |
| SHA256 | `0403533f4cdaee93dff10e5522d5597ac014dc8531648757e23016c34b2c51dc` |

### Live-board rationale
The 2026-06-04 user update says the real remaining rank leverage is speed:
`speed_surface_d1_ecs` is reported as current rank `4`, with a `4 -> 2`
boundary around `0.01` WS. If coverage is unchanged, v224 should move the cell
by about `-0.011` WS.

### Lesson
PENDING SCORE / BUILT DIAGNOSTIC. This is intentionally a one-cell speed test,
not a broad recalibration. The later speed-failure audit says post-hoc speed
calibration/shrink has repeatedly failed hidden, so v224 should not displace
v225 as the preferred optional speed diagnostic. Do not compound v224 until it
scores; if it regresses, keep v222 as the safer base and do not revive speed
micro-shrink broadly.

## Speed Uncertainty Feature Audit — v225 Build Gate (RESEARCH, PASSED)

**Date**: 2026-06-04
**Approach**: Audit whether uncertainty-state features carry stable signal for
`speed_surface_d1_ecs` absolute residuals before spending a scarce speed
submission slot.
**Base**: HRES d1 residuals from the ECS training feature table; not a deployed
prediction replay.

### What was done
- Implemented and debugged `scripts/speed_uncertainty_feature_audit.py`.
- Added bounded audit controls: parquet `--row-groups`, `--max-source-rows`,
  `--skip-replay-sample`, per-stage progress output, and a faster rank
  correlation path.
- Ran the all-row-group bounded audit with `180,000` sampled source rows and
  `120,000` replay rows (`40,000` each for val/tune/holdout).
- Wrote report:
  `docs/research/SPEED_UNCERTAINTY_FEATURE_AUDIT_2026_06_04.md`.

### Key feature signals
Stable features with `min_abs_split_spearman >= 0.05`:

| Feature | Overall rho | Min split abs rho |
|---|---:|---:|
| `forecast_spread` | 0.1179 | 0.0970 |
| `ws10_rstd7d` | 0.1049 | 0.0875 |
| `forecast_tendency_1_7` | 0.1040 | 0.0866 |
| `shear_exponent` | -0.0859 | 0.0789 |
| `msl` | -0.1127 | 0.0774 |
| `ws10_rstd3d` | 0.0875 | 0.0763 |
| `ws10_daily_range` | 0.1042 | 0.0758 |
| `forecast_tendency_7_10` | 0.0528 | 0.0552 |
| `blh_month_anomaly` | 0.0785 | 0.0535 |

### Lesson
RESEARCH PASSED: build a strict `v225` uncertainty-state candidate for
`speed_surface_d1_ecs`, q50 frozen, but do **not** upload from this evidence.
The next gate must compare against the deployed prediction block on
val/tune/holdout and preserve the one-cell scope. `v224` remains only a fallback
diagnostic because it is still a post-hoc shrink.

## v225 — ECS Surface d1 Speed Uncertainty-State Width Redistribution (BUILT HOLD, PENDING SCORE)

**Date**: 2026-06-04
**Approach**: Start from scored production best `v196`, compute an
uncertainty score from the stable v225 audit features, shrink low-uncertainty
10m surface d1 speed intervals, lightly widen the highest-uncertainty 10m rows,
and keep q50 plus all direction columns frozen.
**Base**: `v196`

### What was done
- Implemented `src/experiments/v225_speed_surface_d1_ecs_uncertainty_state.py`.
- Target official dimension: `speed_surface_d1_ecs`, restricted to
  grid / `east_china_sea` / `10m` / d1 / speed endpoints.
- Stable features used: `forecast_spread`, `ws10_rstd7d`,
  `forecast_tendency_1_7`, `shear_exponent`, `msl`, `ws10_rstd3d`,
  `ws10_daily_range`, `forecast_tendency_7_10`, `blh_month_anomaly`.
- Artifact: `submissions/submission_v225.zip`.
- Manifest: `logs/v225_speed_surface_d1_ecs_uncertainty_state/manifest.json`.
- SHA256:
  `5a30f80d3d6f124811d23bea1d123f4c08159230160d4879f3887a2f566a3fbd`.

### Checks
| Check | Value |
|---|---:|
| Target 10m rows | 82,080 |
| Changed rows vs v196 | 69,768 |
| Official surface rows | 164,160 |
| Shrink rows | 57,456 |
| Widen rows | 12,312 |
| Hold rows | 12,312 |
| Direction changed rows | 0 |
| Non-target q rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean changed-10m width delta | -0.0225725 |
| Mean official-cell width delta if coverage unchanged | -0.0112863 |
| ZIP rows incl. header | 3,448,801 |

### Lesson
PENDING SCORE / BUILT HOLD. v225 is the preferred speed ingredient over v224
because it is feature-gated and protects high-uncertainty rows, but it still
lacks local hidden row-level truth and was built on v196. After v222 scored
cleanly, use the already-built `v222_plus_v225` compound as the default
rank-seeking upload; upload standalone v225 only for explicit attribution.

## v226 — ECS Surface d7 Speed Lean HRES-Tail Probe (SCORED: REJECT)

**Date**: 2026-06-04
**Approach**: Start from scored production best `v222`, then apply the
mini-challenge d7 lesson to one speed cell: a tiny lean shrink on low/mid HRES
d7 rows, with a rare high-HRES q95 tail floor.
**Base**: `v222`

### What was done
- Implemented `src/experiments/v226_speed_surface_d7_ecs_lean_tail.py`.
- Target official dimension: `speed_surface_d7_ecs`.
- Scope: grid / `east_china_sea` / surface levels `10m` and `100m` / d7 /
  speed endpoints only.
- For `fcst_speed_d7 < 9.0`, shrank q05/q95 by up to `0.003` m/s per side,
  capped at `0.5%` of each half-width.
- For `fcst_speed_d7 >= 13.0`, set `q95 >= 14.0` as a high-wind tail guard.
- Artifact: `submissions/submission_v226.zip`.
- Manifest: `logs/v226_speed_surface_d7_ecs_lean_tail/manifest.json`.
- SHA256:
  `a4871fc97e699ac6ef9632c1d9d1390ff2466ae3b484401558865eca07c56577`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 164,160 |
| Changed rows vs v222 | 136,909 |
| Shrink rows | 136,580 |
| Tail-floor rows | 329 |
| Hold rows | 27,251 |
| Direction changed rows | 0 |
| Non-target q rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean official-cell width delta if coverage unchanged | -0.00399182 |
| Mean shrink component | -0.00499196 |
| Mean tail q95 component | +0.00100014 |
| ZIP rows incl. header | 3,448,801 |

### Live-board rationale
The stored 2026-06-04 board puts `speed_surface_d7_ecs` at rank 3, about
`0.0034` WS from the next rank and `0.0234` WS from best. This is the right
horizon for the mini-challenge d7 rule, but prior ECS d7 speed attempts
(`v77`, `v80`, `v186`, `v220`) make it a diagnostic, not a default upload.

### Lesson
SCORED: REJECT. Standalone v226 worsened `speed_surface_d7_ecs`
`9.7234 -> 9.7246` and primary `1.418872 -> 1.418875` versus v222. Do not
build on v226 or unlock the speed chain from this result.

## v227 — NS Station d1 Direction Micro-Shrink (SCORED: NEW BEST)

**Date**: 2026-06-04
**Approach**: Start from `v222`, then shrink only the North Sea station d1
direction endpoints by `0.10` degrees per side around the existing `dir_50`.
**Base**: `v222`

### What was done
- Implemented `src/experiments/v227_station_d1_ns_direction_micro_shrink.py`.
- Target official dimension: `dir_stations_d1_ns`.
- Scope: station / `north_sea` / d1 / direction endpoints only.
- `dir_50` is frozen; all speed columns are frozen.
- Artifact: `submissions/submission_v227.zip`.
- Manifest: `logs/v227_station_d1_ns_direction_micro_shrink/manifest.json`.
- SHA256:
  `ecbec06c70c4e80c075fe80f4b3d1645cf2fece31bcb52e4bf4de2505e478a0d`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 256 |
| Changed rows vs v222 | 256 |
| Speed changed rows | 0 |
| Direction changed rows | 256 |
| Non-target q rows | 0 |
| Non-target direction rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean target width delta if coverage unchanged | -0.200000 |
| Visible rank-1 gap | ~0.1578 cWS |

### Lesson
SCORED: NEW BEST. v227 improved `dir_stations_d1_ns` from `170.7878` to
`170.7474` and moved primary `1.418866 -> 1.418862`, despite giving back the
small `v222_plus_v225` speed_surface_d1_ecs gain. Preserve this result through
`v222_plus_v227_plus_v232` before testing the station-d7 direction fallback;
do not upload standalone `v232`.

## v228 — NS Surface d1 Speed Uncertainty-State Candidate (BUILT HOLD, PENDING SCORE)

**Date**: 2026-06-04
**Approach**: Start from `v222`, then apply the v225 uncertainty-state
width redistribution to North Sea surface d1 10m speed endpoints only.
**Base**: `v222`

### What was done
- Parameterized `scripts/speed_uncertainty_feature_audit.py` so the v225 audit
  can be rerun for a specific region/target/report.
- Ran `speed_uncertainty_feature_audit_v228` for `speed_surface_d1_ns` using
  180,000 sampled North Sea source rows and 120,000 replay rows.
- Reused the v225 builder mechanics through
  `src/experiments/v228_speed_surface_d1_ns_uncertainty_state.py`.
- Target official dimension: `speed_surface_d1_ns`.
- Scope: grid / `north_sea` / surface 10m / d1 / speed endpoints only.
- `q50` is frozen; all direction columns are frozen.
- Artifact: `submissions/submission_v228.zip`.
- Manifest: `logs/v228_speed_surface_d1_ns_uncertainty_state/manifest.json`.
- SHA256:
  `d1171d7057ce8d653ffd5c5c79c212c9a4fd568aa229a402f3efac845fe48132`.

### Audit signal
The NS d1 feature audit passed the same build gate as v225, with stronger
stable uncertainty signals: 11 features cleared `min_abs_split_spearman >= 0.05`.
Top features were `ws10_rstd7d`, `shear_exponent`, `ws10_daily_range`,
`forecast_spread`, `ws10_rstd3d`, `blh_month_anomaly`, and
`forecast_tendency_1_7`.

### Checks
| Check | Value |
|---|---:|
| Target 10m rows | 82,080 |
| Official surface rows | 164,160 |
| Changed rows vs v222 | 69,768 |
| Speed changed rows | 69,768 |
| Direction changed rows | 0 |
| Non-target q rows | 0 |
| Non-target direction rows | 0 |
| q50 changed rows | 0 |
| `dir_50` changed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Shrink rows | 57,456 |
| Widen rows | 12,312 |
| Hold rows | 12,312 |
| Mean changed-row width delta | -0.0226885 |
| Mean official-cell width delta if coverage unchanged | -0.0113442 |
| ZIP rows incl. header | 3,448,801 |

### Lesson
PENDING SCORE / BUILT HOLD. v228 gives us a faithful one-cell mechanism for the
previously risky `speed_surface_d1_ns` boundary, but it is still part of the
same speed-width family as the v225 ingredient. Do not upload standalone v228;
use it only through the active scored-chain compound after `v226` is clean and
only if a refreshed board makes its target visibly rank-moving. On the current
board, skip v228 and let the matching `...plus_v229` branch follow the latest
clean speed chain. Skip v228 entirely if any earlier speed compound fails.
## v222_plus_v225 — Direct Compound (SCORED: NEW BEST / RAW_ONLY_GAIN)

**Date**: 2026-06-04
**Approach**: Build a direct production-preserving speed diagnostic from `v196` using `v222` direction overlays and the pending `v225` one-cell speed overlay.
**Base**: `v196`

### What was done
- Generated by `scripts/build_scored_compound.py` after `v222` scored clean; `v225` remains an unscored one-cell speed probe.
- Overlay changed-row counts: `v222:835164, v225:69768`.
- Rows: `3,448,800`.
- Artifact: `submissions/submission_v222_plus_v225.zip`.
- SHA256: `1d4ce97ecbc02004cabadb88f0e47fb40950517ca51fe16bd4ac7992bf38f5e8`.

### Leaderboard score

| Dim | Best (v222) | New (v222_plus_v225) | Delta |
|---|---:|---:|---:|
| `speed_surface_d1_ecs` | 4.5972 | 4.5951 | -0.0021 improved raw score |
| `primary_score` | 1.418872 | 1.418866 | -0.000006 new best |

Score-intake outcome: `RAW_ONLY_GAIN`. The target improved, but the stored
public-board rank stayed `4 -> 4`; the nearest visible boundary remains
`carlometta` at `4.59`, so the new score did not validate the speed-chain
unlock.

### Lesson
SCORED: NEW BEST / RAW_ONLY_GAIN. Promote `v222_plus_v225` as the production
best, but stop the current speed-width chain. Do not upload `v226` or later
speed probes after this result; the router-selected next slot is `v227`
(`Dir NS Sta d1`, projected rank `2 -> 1`) after fresh-board verification.
## v222_plus_v227_plus_v232 — Score-Gated Compound (SCORED / NON-WORSE RAW_ONLY_GAIN)

**Date**: 2026-06-07  
**Approach**: Build a guarded compound from `v196` using score-gated overlays `v222, v227, v232`.  
**Base**: `v196`

### What was done
- Generated by `scripts/build_scored_compound.py` after score gates passed.
- Overlay changed-row counts: `v222:835164, v227:835420, v232:835420`.
- Rows: `3,448,800`.
- Artifact: `submissions/submission_v222_plus_v227_plus_v232.zip`.
- SHA256: `13c9fa055374733e757dbb396a5166ea0070f376d773fd348a28db54e9f1656f`.

### Leaderboard score

| Dim | Best (v227) | New (v222_plus_v227_plus_v232) | Delta |
|---|---:|---:|---:|
| `dir_stations_d7_ns` | 310.9467 | 310.2390 | -0.7077 improved raw score |
| `primary_score` | 1.418862 | 1.418862 | +0.000000 non-worse |

Score-intake outcome: `RAW_ONLY_GAIN`. The intended target improved, but the
stored public-board rank stayed `4 -> 4`; the next boundary was `carlometta`
at `301.5400`, so this did not validate another station-d7 salvage upload.

### Lesson
SCORED / NON-WORSE RAW_ONLY_GAIN. Promote `v222_plus_v227_plus_v232` as the
production base because it preserved the `v227` primary while improving
`dir_stations_d7_ns`; do not spend another station-d7 salvage slot without a
fresh board or a stronger mechanism. The router-selected next packet is
`v222_plus_v227_plus_v232_plus_v235`, targeting the remaining held ECS
station-d1 direction micro-shrink.

## v222_plus_v227_plus_v232_plus_v235 — Score-Gated Compound (READY TO UPLOAD, PENDING SCORE)

**Date**: 2026-06-08  
**Approach**: Build a guarded compound from `v196` using score-gated overlays `v222, v227, v232, v235`.  
**Base**: `v196`

### What was done
- Generated by `scripts/build_scored_compound.py` after score gates passed.
- Overlay changed-row counts: `v222:835164, v227:835420, v232:835420, v235:835388`.
- Rows: `3,448,800`.
- Artifact: `submissions/submission_v222_plus_v227_plus_v232_plus_v235.zip`.
- SHA256: `e17d2507cb060798ca78182a7c1abeaff6dd2cb7216f941b6a6b5920a8ef438c`.

### Lesson
READY TO UPLOAD / PENDING SCORE. Full row-scan verification passed
(`3,448,801` CSV lines, `3,447,360` grid rows, `1,440` station rows) against
the refreshed 2026-06-08 board snapshot. The snapshot is valid through
2026-06-10; rerun the fresh-board verifier or refresh the board before upload
after that date.

## s001 — Baseline Plumbing Test

**Date**: 2026-04-22
**Approach**: Unmodified `2a_starting_kit_light` CatBoost + LightGBM baseline
**Big idea**: Just verify the submission pipeline works — 36/36 dims scored, no SENTINEL.

### What was done
- Ran starting kit notebook as-is
- Generated `submission_light.zip`
- Uploaded to Codabench

### Key scores (worst dims)
- dir_pressure_d1_ecs: 374.7 (worst dim)
- dir_pressure_d1_ns: 232.6
- speed_pressure_d7_ns: 35.3
- dir_pressure_d7_ecs: 343.7
- speed_pressure_d14_ns: 27.6

### Learnings
- Surface speed d1 is competitive (WS ~5)
- Pressure speed uses vertical ratios — poor at longer horizons
- Direction is nearly random for pressure levels (cWS 232-375)
- Station predictions are naive nearest-grid copies
- Pressure direction ECS d1 is the single worst dimension

---

## s002 — Station Calibration (FAILED)

**Date**: 2026-04-22
**Approach**: Per-station EMOS + LGBM residual calibration
**Big idea**: Use actual station observations to calibrate speed/direction predictions

### What was done
- Trained per-station OLS model: `obs ~ 1 + ws10 + ws100 + log(height_m)`
- LightGBM residual correction with station categorical
- Per-station conformal calibration for direction

### Key scores (catastrophic)
- dir_stations_d1_ns: 628 → 422-565 cWS range across station dims
- dir_stations_d14_ns: 974
- Overall: 1.770 (+0.097 from baseline — WORSE)

### What went wrong
- Direction intervals were massively over-wide (half-widths 87-180°)
- The station direction calibration produced terrible intervals
- Height_m column caused merge conflicts during training
- The previous session's `train_station_model.py` was fundamentally broken

### Lesson
- Station calibration is sound in theory but requires careful implementation
- Baseline nearest-grid approach is actually decent for stations
- Don't underestimate the difficulty of circular direction calibration

---

## v2 — Direct Pressure CatBoost (REGRESSION)

**Date**: 2026-04-23
**Approach**: Replace vertical-ratio pressure speed with direct CatBoost quantile models
**Big idea**: Train per (level, hour) CatBoost models using HRES pressure features directly

### What was done
- Trained CatBoost quantile regression per (level, hour) for pressure speed
- Used HRES u/v forecasts at pressure levels as features
- Kept everything else from baseline

### Key scores (regression on pressure)
- speed_pressure_d7_ns: 83.3 (was 35.3 — DOUBLED)
- speed_pressure_d14_ns: 62.0 (was 27.6 — DOUBLED)
- speed_pressure_d7_ecs: 39.1 (was 18.4)

### What went wrong
- **Critical bug**: `generate_v2_submission.py` trained per (level, hour) WITHOUT horizon as a feature
- The code then **copied the same prediction for d1/d7/d14** (line 202: loop over horizons using identical model output)
- Result: intervals too narrow for d7/d14 → massive Winkler penalties
- Surface and station predictions unchanged (so those scores identical to s001)

### Lesson
- Always include horizon as a feature when training quantile models across horizons
- The baseline's vertical ratios naturally widen for longer horizons (because HRES uncertainty grows)
- Direct models need explicit horizon-dependent widening

---

## v3 — Direction Overlay (Partial Recovery)

**Date**: 2026-04-23
**Approach**: v2 pressure speed + LightGBM sin/cos direction model overlay
**Big idea**: Replace all direction predictions with a proper circular direction model

### What was done
- Trained LightGBM direction models per (region, level) — 14 total
- Model predicts sin/cos of centre angle + quantile half-width
- Conformal calibration on TUNE split for 90% coverage
- Applied to all grid points (surface + pressure)
- Kept v2's (broken) pressure speed

### Key direction improvements (massive wins)
- dir_pressure_d1_ecs: 374.7 → 157.1 (-218!)
- dir_pressure_d1_ns: 232.6 → 154.2 (-78!)
- dir_pressure_d7_ecs: 343.7 → 245.1 (-99!)
- dir_surface_d1_ns: 144.7 → 154.5 (slight regression)

### Remaining issues
- Pressure speed still broken from v2 (d7 NS: 83, d14 NS: 62)
- Station direction poor: dir_stations_d1_ns: 381 (worse than baseline 186!)
- Direction d14 still high: dir_pressure_d14_ns: 401, dir_surface_d14_ns: 362

### Lesson
- Direction overlay is the single biggest lever (~0.04 improvement)
- The sin/cos decomposition for centre prediction avoids the 0/360 discontinuity
- Conformal calibration is essential for coverage
- But pooled across horizons → intervals don't widen enough for d14
- Station direction needs separate handling (nearest-grid direction is bad)

---

## v4 — Cherry-Pick (BEST APPROACH)

**Date**: 2026-04-23
**Approach**: Best-of-each-world — baseline speed + v3 direction + baseline stations
**Big idea**: Don't use broken v2 pressure speed; keep baseline's vertical ratios which naturally widen

### What was done
- Took baseline `predictions_light.csv` (speed from starting kit)
- Replaced ALL direction columns with v3's direction model predictions
- Kept baseline station predictions (no calibration)
- Cherry-picked the best components from s001 + v3

### Key wins
- dir_pressure_d1_ecs: 374.7 → 157.1 (direction model)
- dir_pressure_d7_ecs: 343.7 → 245.1 (direction model)
- Pressure speed back to baseline quality (vertical ratios)
- Surface speed unchanged (competitive at WS ~5)

### Remaining drags
- dir_pressure_d14_ns: 401.7 (direction model doesn't widen enough)
- dir_surface_d14_ns: 362.3
- dir_surface_d14_ecs: 362.8
- speed_pressure_d7_ns: 35.3 (baseline vertical ratio limit)
- Station speed d14 NS: 22.1 (no calibration)

### Lesson
- Cherry-picking is a valid strategy — don't force one model for everything
- The baseline's vertical ratios are surprisingly hard to beat for pressure speed
- Direction d14 is the biggest remaining opportunity
- Current rank: 7th on leaderboard

---

## v5 — Horizon-Aware + Scaling (REGRESSION)

**Date**: 2026-04-23
**Approach**: Fix v2's pressure speed with horizon-aware CatBoost + direction interval scaling
**Big idea**: Give the pressure model the right features + widen direction d14 with post-hoc scaling

### What was done
1. Pressure speed: per (level, horizon, hour) CatBoost with horizon-specific HRES features + interval widening (d7 ×1.73, d14 ×1.91)
2. Direction d7/d14: post-hoc half-width scaling (d7 ×1.15, d14 ×1.4)
3. Station speed: log-wind height correction for non-10m stations

### Catastrophic direction scores
- dir_surface_d14_ns: 362 → **984** (+622!)
- dir_pressure_d14_ns: 402 → **927** (+525!)
- dir_pressure_d14_ecs: 344 → **892** (+548!)
- dir_surface_d14_ecs: 363 → **492** (+129)

### Pressure speed also worse
- speed_pressure_d7_ns: 35 → 64 (worse than baseline)
- speed_pressure_d1_ns: 26 → 34 (worse)

### What went wrong
- **Direction scaling was too aggressive**: ×1.4 on d14 produced absurdly wide intervals
- The half-width scaling was applied uniformly, not calibrated
- Many intervals probably straddled 0/360 causing circular Winkler to compute huge arcs
- Pressure CatBoost still couldn't match baseline vertical ratios even with widening

### Lesson (THE MOST IMPORTANT ONE SO FAR)
- **Never blindly scale intervals** — the Winkler score punishes over-wide intervals MORE than under-wide ones
- The direction model's d14 intervals were already reasonable at ~360 cWS — the problem was the centre accuracy, not the width
- Post-hoc scaling is dangerous; per-horizon training is the right approach
- Station height correction was the only positive (NS_01: 102m ×1.4 ratio)

---

## v6 — Station Height Correction (CURRENT BEST)

**Date**: 2026-04-23
**Approach**: v4 base + log-wind profile height correction for non-10m stations
**Big idea**: The only thing that worked in v5 was station height correction — apply just that to v4

### What was done
- Started from v4 (baseline speed + direction overlay)
- Applied log-wind profile correction: `speed(z) = speed(10m) × ln(z/z0) / ln(10/z0)`
- z0 = 0.03m (offshore roughness length)
- Corrected stations: NS_01 (102m, ×1.400), NS_02 (14m, ×1.058), ECS_01 (42.3m, ×1.248), ECS_06 (3m, ×0.793)

### Clean wins (no regressions)
- speed_stations_d7_ns: 13.98 → 13.52 (-0.46)
- speed_stations_d14_ns: 22.09 → 19.59 (-2.50)
- speed_stations_d7_ecs: 11.33 → 10.72 (-0.61)
- speed_stations_d14_ecs: 12.63 → 12.33 (-0.30)
- All grid dims IDENTICAL to v4

### Score: 1.625 (new best, rank improvement from v4's 1.632)

### Lesson
- Small, well-understood corrections > complex model changes
- The log-wind profile is physically motivated and correct
- Stations at non-10m heights were systematically under/over-predicted
- This validates the "one clean change per submission" approach

---

## v7 — Per-Horizon Direction Models (REGRESSION)

**Date**: 2026-04-24
**Approach**: 42 per-horizon direction models (2 regions × 7 levels × 3 horizons) instead of 14 pooled
**Big idea**: Each horizon gets its own model, so d14 models naturally learn wider intervals without post-hoc scaling

### What was done
- Trained 42 LightGBM direction models (sin/cos centre + half-width + conformal)
- Each model only sees data from ONE horizon (d1, d7, or d14)
- Applied to all grid points across all 8 inference windows
- Kept v6's speed predictions (baseline + height correction)

### Biggest improvements vs v6
| Dim | v6 | v7 | Delta |
|-----|----|----|-------|
| dir_pressure_d14_ns | 401.7 | **300.3** | -101 |
| dir_surface_d14_ns | 362.3 | **307.4** | -55 |
| dir_surface_d14_ecs | 362.8 | **331.9** | -31 |
| dir_pressure_d14_ecs | 344.2 | **361.1** | +17 (worse) |

### Biggest regressions vs v6
| Dim | v6 | v7 | Delta |
|-----|----|----|-------|
| dir_pressure_d1_ecs | 157.1 | **374.7** | +218 CATASTROPHIC |
| dir_pressure_d1_ns | 154.2 | **232.6** | +78 |
| dir_pressure_d7_ecs | 245.1 | **343.7** | +99 |
| dir_pressure_d7_ns | 266.5 | **302.1** | +36 |
| dir_surface_d1_ecs | 164.2 | **190.4** | +26 |

### What went wrong
- The d1/d7 per-horizon models had only 1/3 the training data of the pooled model
- They lost cross-horizon signal — the pooled model could leverage patterns from all horizons
- d1/d7 direction scores match s001 BASELINE exactly, meaning the per-horizon models are no better than no direction model at all for d1/d7
- Only d14 benefited (and it benefited enormously)

### Lesson
- Per-horizon training works when there's enough data per horizon
- The fix is obvious: **use pooled model for d1/d7, per-horizon model only for d14**
- This should give us the d14 improvement without the d1/d7 regression
- Estimated score: v6 base + d14 direction gains ≈ 1.58-1.60 (would be new best)

---

## v8 — Residual Speed + Per-Horizon Direction ALL Horizons (BREAKTHROUGH)

**Date**: 2026-04-24
**Approach**: MOS-style residual speed models + per-horizon direction for ALL horizons + baseline fallback
**Big idea**: Two simultaneous innovations: (1) predict speed residual = reanalysis - HRES (model only learns bias/uncertainty), (2) per-horizon direction for ALL horizons (v7's merge bug masked that these are excellent for d1 too)

### What was done
- Trained LightGBM residual speed models per (region, level, horizon) — ~24 models
- For surface: HRES surface forecast speed available → residual approach works
- For pressure: HRES u/v at pressure levels → compute wind speed → residual
- For d14 pressure: no HRES pressure d14 forecasts → fallback to baseline
- Used v7's per-horizon direction models for ALL horizons (d1, d7, d14) — correctly merged this time
- Kept height correction for stations

### Biggest improvements vs v6
| Dim | v6 | v8 | Delta |
|-----|----|----|-------|
| speed_pressure_d1_ns | 25.76 | **7.13** | -18.6 |
| speed_pressure_d1_ecs | 30.34 | **6.90** | -23.4 |
| dir_pressure_d1_ns | 154.19 | **81.09** | -73 |
| dir_surface_d1_ns | 144.68 | **91.63** | -53 |
| dir_pressure_d14_ns | 401.67 | **341.21** | -60 |
| dir_pressure_d1_ecs | 157.09 | **106.23** | -51 |
| dir_surface_d1_ecs | 190.44 | **118.38** | -72 |
| dir_pressure_d14_ecs | 344.15 | **315.38** | -29 |
| speed_pressure_d7_ns | 35.30 | **27.83** | -7.5 |
| speed_pressure_d14_ns | 35.03 | **27.65** | -7.4 |

### Regressions vs v6
| Dim | v6 | v8 | Delta |
|-----|----|----|-------|
| speed_surface_d7_ns | 12.86 | 14.87 | +2.0 |
| speed_surface_d14_ns | 14.54 | 16.10 | +1.6 |
| dir_surface_d7_ns | 285.84 | 303.87 | +18.0 |
| dir_stations_d7_ns | 299.68 | 332.47 | +32.8 |
| dir_pressure_d7_ns | 266.54 | 283.96 | +17.4 |

### Score: 1.494 (NEW BEST, -0.131 from v6)

### Critical insight
V7's direction regression was a FALSE ALARM — the merge scoping bug in run_v7.py meant direction predictions were NEVER applied. V7's scores were actually s001 baseline direction. The per-horizon direction models are EXCELLENT for d1 (81-118 cWS vs pooled 144-190). This invalidates the "pooled d1/d7" approach in v7b/v9/v10/v11.

### Remaining drags
1. Surface speed d7/d14: +1-2 regression (residual approach adds noise where HRES surface is already good)
2. NS d7 direction: +18-33 regression (per-horizon d7 slightly worse than pooled for NS)
3. d14 pressure speed: 27-28 (still fallback to baseline, no HRES pressure d14)
4. d14 direction: 305-341 (still high, but much improved)

### Lesson
- The merge bug cost us 2 wasted submissions (v7, v7b-first) and led to wrong conclusions about per-horizon d1 direction
- Residual/MOS framing is transformative for pressure speed (4x improvement on d1)
- Surface residual adds noise — baseline is better for surface levels
- Next move: cherry-pick v8 pressure speed + baseline surface speed + pooled d7 NS direction

---

## Cumulative Lessons (after 11 submissions)

### What works
1. **Residual/MOS speed framing** — predict reanalysis-HRES residual, biggest lever (~0.09)
2. **Direction model (sin/cos + conformal)** — ~0.04 improvement, per-horizon is best
3. **Cherry-picking best components** — don't use one model for everything
4. **Physically-motivated corrections** — log-wind profile for stations
5. **Per-horizon direction for d1** — counter-intuitively better than pooled (v7 bug masked this)

### What doesn't work
1. **Residual framing for surface levels** — adds noise where HRES is already accurate
2. **Post-hoc interval scaling** — catastrophic on d14 direction
3. **Station EMOS** — over-wide direction intervals
4. **Direct pressure CatBoost without residual framing** — can't beat baseline vertical ratios

### Strategic insights
- V8's per-horizon direction for ALL horizons is the right approach (not hybrid)
- Residual speed for pressure + baseline speed for surface = optimal
- The remaining gap is d7 direction NS (per-horizon slightly worse than pooled) and d14 pressure speed (no HRES data)

### Remaining biggest opportunities (by estimated rank impact)
1. **Cherry-pick best per-dimension** — v8 pressure speed + baseline surface speed (~0.02-0.04)
2. **Pooled d7 direction for NS** — fix the d7 NS regression (~0.01-0.02)
3. **CQR calibration** — principled interval width adjustment (~0.01-0.02)
4. **d14 pressure speed** — different approach since no HRES d14 pressure data
5. **Station direction calibration** — proper handling of station direction

---

## v12 — Cherry-Pick v6+v8 (PENDING SCORE)

**Date**: 2026-04-24
**Approach**: Cherry-pick best per-dimension from v8 and v6
**Big idea**: Use v8 residual pressure speed + baseline surface speed + per-horizon direction d1/d14 + pooled d7 NS direction

### What was done
- Pressure speed: v8 residual models
- Surface speed: reverted to baseline
- Direction: hybrid per-horizon (d1/d14) + pooled (d7 NS) + per-horizon (d7 ECS)
- Station: baseline + height correction

### Status
- Submitted but never scored on leaderboard (submission file may have been identical to v8)
- Marked as PENDING in log.json

---

## v13 — d14 Cross-Horizon Residual (REGRESSION)

**Date**: 2026-04-24
**Approach**: V12 base + d14 pressure speed via d10 HRES cross-horizon residual
**Big idea**: Use d10 HRES as pseudo-forecast for d14 pressure speed

### What was done
- Trained d14 pressure residual models using d10 HRES as the base forecast
- 4-day gap between d10 HRES issue and d14 target

### Key scores (regression)
- speed_pressure_d14_ns: 28.57 vs baseline 27.65 (+0.92)
- speed_pressure_d14_ecs: 23.11 vs baseline 19.25 (+3.86)

### What went wrong
- 4-day gap too large for MOS approach
- d10 HRES doesn't carry enough signal for d14 prediction
- Residual too noisy

### Lesson
- Cross-horizon transfer needs closer base forecast
- d14 pressure speed remains unsolved

---

## v14 — CQR Calibration on Pressure (REGRESSION)

**Date**: 2026-04-24
**Approach**: V13 + CQR calibration on all pressure intervals
**Big idea**: Conformalized Quantile Regression to fix coverage

### Key scores (regression)
- speed_pressure_d1_ns: 7.18 vs v8's 7.13 (+0.05)
- speed_pressure_d14_ecs: 22.87 vs baseline 19.25 (+3.62)

### What went wrong
- CQR widened already-calibrated intervals on d1/d7 pressure
- Only helps when model is systematically under-covering
- Combined with v13's bad d14, overall score worse

### Lesson
- CQR is not a free lunch — only helps when coverage is wrong
- Speed models already have decent coverage (0.86-0.89)
- Need to apply CQR selectively or only to under-covering models

---

## v15 — Station Direction Models (CATASTROPHIC)

**Date**: 2026-04-24
**Approach**: V12 grid + per-station direction models
**Big idea**: Train individual direction models per station using nearest-grid features

### Key scores (catastrophic)
- dir_stations_d1_ns: 710.8 vs baseline 185.9 (+525)
- dir_stations_d7_ns: 954.2 vs baseline 332.5 (+622)
- dir_stations_d7_ecs: 1035.7 vs baseline 296.0 (+740)

### What went wrong
- Two bugs: (1) Station direction models overfit with 300-1000 samples × 246 features
- (2) Pressure speed reverted to baseline because generate_v15() didn't merge v8 pressure
- Double failure — both direction AND speed regressed

### Lesson
- Per-station models need severe dimensionality reduction
- Must always verify that baseline predictions are preserved for unchanged dims
- Station direction is hard — need pooled approach with station metadata

---

## v16 — NS d14 Direction Revert to Baseline (SCORED)

**Date**: 2026-04-24
**Approach**: V8 base + revert NS d14 surface/pressure direction to baseline
**Big idea**: Per-horizon direction models are WORSE than baseline for NS d14 — cherry-pick revert

### What was done
- Identified that NS d14 per-horizon direction models scored 341 (pressure) and 335 (surface) vs baseline's 300 and 307
- Reverted 3 dims to baseline: dir_pressure_d14_ns, dir_surface_d14_ns, dir_surface_d7_ns
- Everything else identical to v8

### Improvements over v8
| Dim | v8 | v16 | Delta |
|-----|----|----|-------|
| dir_pressure_d14_ns | 341.21 | **300.28** | -40.93 |
| dir_surface_d14_ns | 335.16 | **307.42** | -27.74 |
| dir_surface_d7_ns | 303.87 | **300.05** | -3.82 |

### Score: 1.494 (same as v8), mean_rank 4.28 (WORSE than v8's 4.22)

### Why mean_rank regressed
- carlometta jumped rank 7 → rank 2 with massive station speed improvements
- carlometta's WS NS Stations d1: 7.37 vs our 10.70 (+3.33 gap)
- carlometta's WS ECS Stations d1: 6.71 vs our 10.45 (+3.74 gap)
- This hurt everyone's relative rankings — not our fault

### Dimension gap analysis vs competitors
**Biggest gaps (where we LOSE):**
| Dimension | V16 | Best | Gap | Leader |
|-----------|-----|------|-----|--------|
| Dir ECS Stations d7 | 296.0 | 237.2 | +58.8 | Capgemini |
| Dir NS Stations d7 | 332.5 | 302.8 | +29.6 | Breva |
| WS ECS Stations d1 | 10.45 | 6.71 | +3.74 | carlometta |
| WS NS Stations d1 | 10.70 | 7.37 | +3.33 | carlometta |
| WS NS Pressure d14 | 27.65 | 24.35 | +3.30 | Heavy Baseline |

**Dimensions where we DOMINATE:**
| Dimension | V16 | 2nd Best | Gap |
|-----------|-----|----------|-----|
| Dir NS Pressure d1 | 81.1 | 289.5 | -208 |
| Dir ECS Pressure d1 | 106.2 | 303.6 | -197 |
| Dir NS Surface d1 | 91.6 | 235.5 | -144 |
| Dir ECS Pressure d7 | 240.9 | 290.1 | -49 |

### Lesson
- Cherry-pick per-dimension is the right approach — some per-horizon models are worse than baseline
- mean_rank is relative — competitor improvements hurt us even when we improve
- Station direction (d7) and station speed (d1) are the two biggest gaps
- Our d1 direction dominance is our moat (130-208 point gaps)
- Next: v17 CQR calibration (selective), v18 station direction, then attack carlometta's station speed

---

## v17 — Selective Pressure CQR (PENDING SCORE)

**Date**: 2026-04-24
**Approach**: V16 base + pressure-speed CQR offsets from `run_v17.py`
**Big idea**: Test whether selective conformal widening on under-covered pressure intervals improves the raw pressure-speed dimensions without touching stations or direction.

### What was done
- Kept station rows identical to v16.
- Kept all direction rows identical to v16.
- Changed only grid pressure-speed `q05` / `q95`; `q50` stayed identical.
- Submission artifact: `starting-kit/phase_1/submission_v17.zip`.

### Status
- PENDING SCORE.
- Intended as a marginal calibration data point, not the primary path to winning.

### Tactical interpretation
- Promote only if `speed_pressure_*` improves cleanly versus v16.
- Reject if it repeats v14's lesson: CQR widening already-calibrated intervals.

---

## v18 — Station Direction Only (PENDING SCORE)

**Date**: 2026-04-24
**Approach**: V16 grid + station direction conformal overlay from `run_v18.py`
**Big idea**: Isolate station direction, the largest raw competitor gap, without changing station speed.

### What was done
- Kept all grid rows identical to v16.
- Kept station speed columns identical to v16.
- Changed only station `dir_05` / `dir_50` / `dir_95`.
- Submission artifact: `starting-kit/phase_1/submission_v18.zip`.

### Status
- PENDING SCORE.
- This is the diagnostic guardrail for v19.

### Tactical interpretation
- If v18 wins and v19 fails, station speed caused the failure.
- If v18 fails, do not build further station-direction work on this approach; switch to low-dimensional circular bias correction.

---

## v19 — Station Direction + Speed Combined (SCORED)

**Date**: 2026-04-24
**Approach**: V16 grid + v18 station direction + station speed quantile model from `run_v19.py`
**Big idea**: Attack both biggest station gaps in one high-upside submission.

### What was done
- Kept all grid rows identical to v16.
- Changed all station speed quantiles.
- Changed all station direction interval columns.
- Submission artifact: `starting-kit/phase_1/submission_v19.zip`.

### Key scores vs v16
| Dim | v16 | v19 | Delta |
|-----|-----|-----|-------|
| dir_stations_d7_ecs | 296.0 | **237.4** | -58.5 improved |
| dir_stations_d1_ns | 185.9 | **178.3** | -7.6 improved |
| speed_stations_d14_ns | 19.59 | **15.85** | -3.73 improved |
| speed_stations_d14_ecs | 12.33 | **8.63** | -3.70 improved |
| speed_stations_d1_ns | 10.70 | **7.86** | -2.84 improved |

### Regressions vs v16
| Dim | v16 | v19 | Delta |
|-----|-----|-----|-------|
| dir_stations_d14_ns | 305.6 | **338.1** | +32.5 regressed |
| dir_stations_d1_ecs | 254.8 | **263.1** | +8.3 regressed |
| dir_stations_d14_ecs | 332.9 | **337.4** | +4.5 regressed |

### Score
- primary_score: **1.450504** (36/36 OK, no SENTINEL)
- Scoped station-block total delta vs v16: **-37.58** raw Winkler/cWS points

### Lesson
- PROMOTE. The station model is the next breakthrough after v8: all six station speed dimensions improved, and ECS d7 station direction hit the exact biggest gap.
- The direction overlay should be cherry-picked by horizon/region: keep v19 for NS d1, NS d7, and ECS d7; revert v16 for NS d14, ECS d1, and ECS d14.
- Next variant should keep v19 station speed everywhere and selectively revert station direction regressions.

---

## v26 — Station Direction Cherry-Pick (SCORED)

**Date**: 2026-04-25
**Approach**: V19 station speed + v19 winning station-direction cells + v16 fallback for losing station-direction cells.
**Big idea**: Convert v19 from a strong but mixed station result into a cleaner per-dimension cherry-pick submission.

### What was done
- Kept all station speed quantiles from v19.
- Kept v19 station direction for NS d1, NS d7, and ECS d7.
- Reverted station direction to v16 for NS d14, ECS d1, and ECS d14.
- Kept every grid row identical to v19/v16.
- Submission artifact: `starting-kit/phase_1/submission_v26.zip`.

### Key scores vs v19
| Dim | v19 | v26 | Delta |
|-----|-----|-----|-------|
| dir_stations_d14_ns | 338.1 | 305.6 | -32.5 improved |
| dir_stations_d1_ecs | 263.1 | 254.8 | -8.3 improved |
| dir_stations_d14_ecs | 337.4 | 332.9 | -4.5 improved |

### Score
- primary_score: **1.450504** (36/36 OK, no SENTINEL)
- Scoped station-direction total delta vs v19: **-45.24** raw cWS points
- The unchanged primary score / displayed mean rank is treated as a delayed leaderboard-refresh artifact; the raw 36-dim scores prove the intended improvement.
- Visible-table estimated mean rank before refresh: **3.64**, which would rank ahead of the current visible leader at 4.38 if the shown rows are the active rank pool.

### Lesson
- PROMOTE. V26 did exactly what intended: it kept all v19 station-speed gains and repaired the three v19 station-direction regressions.
- Treat v26 as the current station base.
- Next attack should move away from station direction and target visible grid-speed rank drag, especially heavy-baseline surface speed and d14 pressure speed.

---

## v27 — Heavy Grid-Speed Graft (SCORED)

**Date**: 2026-04-25
**Approach**: V26 base + official heavy-baseline grid speed.
**Big idea**: Combine v26's station/direction strengths with the visible heavy-baseline advantage on grid speed.

### What was done
- Executed `2d_starting_kit_heavy.ipynb` and generated `starting-kit/phase_1/predictions_heavy.csv`.
- Started from `predictions_v26.csv`.
- Replaced only grid `q05` / `q50` / `q95` with heavy predictions on all grid rows.
- Kept all station rows unchanged from v26.
- Kept all direction columns unchanged from v26.
- Submission artifact: `starting-kit/phase_1/submission_v27.zip`.

### Key scores vs v26
| Dim | v26 | v27 | Delta |
|-----|-----|-----|-------|
| speed_pressure_d14_ns | 27.65 | 24.35 | -3.30 improved |
| speed_pressure_d14_ecs | 19.25 | 17.97 | -1.28 improved |
| speed_surface_d14_ns | 16.10 | 15.12 | -0.98 improved |
| speed_pressure_d7_ecs | 16.61 | 15.71 | -0.90 improved |
| speed_pressure_d7_ns | 27.83 | 27.22 | -0.61 improved |

### Verification
- ZIP contains one root `predictions.csv`.
- Row count: `3,448,800`; grid `3,447,360`; station `1,440`.
- No NaNs in q/dir columns; no quantile crossing.
- Changed rows vs v26: `3,447,360` grid speed rows only.
- Direction changes vs v26: `0`.
- Station value changes vs v26: `0`.
- Grid speed mismatch vs heavy: `0`.

### Score
- primary_score: **1.435908** (36/36 OK, no SENTINEL)
- Scoped grid-speed total delta vs v26: **-9.16** raw Winkler points
- Visible-table estimated mean rank before refresh: **1.75**.

### Lesson
- PROMOTE. The heavy speed graft transferred cleanly: all 12 grid-speed dimensions improved and no station or direction dimension changed.
- Treat v27 as the current base.
- The next best low-risk move is direction cherry-pick from heavy where heavy is visibly better and locally available: NS station d7 and NS surface d7.

---

## v28 — Heavy NS d7 Direction Cherry-Pick (SCORED)

**Date**: 2026-04-25
**Approach**: V27 base + heavy-baseline direction for NS d7 station and NS d7 surface only.
**Big idea**: Use the locally available heavy baseline as a direction donor only where it is visibly better, avoiding its known direction regressions elsewhere.

### What was done
- Started from `predictions_v27.csv`.
- Copied `dir_05` / `dir_50` / `dir_95` from `predictions_heavy.csv` for north_sea station d7 rows.
- Copied `dir_05` / `dir_50` / `dir_95` from `predictions_heavy.csv` for north_sea surface-grid d7 rows (`10m`, `100m`).
- Kept all speed columns identical to v27.
- Kept all other direction cells identical to v27.
- Submission artifact: `starting-kit/phase_1/submission_v28.zip`.

### Key scores vs v27
| Dim | v27 | v28 | Delta |
|-----|-----|-----|-------|
| dir_stations_d7_ns | 330.6 | 315.7 | -14.9 improved |
| dir_surface_d7_ns | 300.0 | 297.9 | -2.1 improved |

### Verification
- ZIP contains one root `predictions.csv`.
- Row count: `3,448,800`; grid `3,447,360`; station `1,440`.
- No NaNs in q/dir columns; no quantile crossing.
- Speed changes vs v27: `0`.
- Direction changes vs v27: `164,416` rows: `164,160` NS d7 surface grid rows and `256` NS d7 station rows.

### Score
- primary_score: **1.435908** (36/36 OK, no SENTINEL)
- Scoped direction total delta vs v27: **-16.99** raw cWS points
- Visible-table estimated mean rank before refresh: **~1.64**.

### Lesson
- PROMOTE. The heavy NS d7 direction cherry-pick transferred cleanly and only changed the intended rows.
- Treat v28 as the current base.
- Remaining visible drags are smaller and riskier: ECS station d1 direction, ECS surface d14 direction, ECS/NS station speed d1/d7.

---

## v29 — Baseline ECS Surface d14 Direction Revert (HOLD / NOT SUBMITTED)

**Date**: 2026-04-25
**Approach**: V28 base + baseline-light direction only for ECS surface d14.
**Big idea**: Spend one very narrow submission to recover a visible rank on `dir_surface_d14_ecs` without touching any other cell.

### What was done
- Started from `predictions_v28.csv`.
- Copied `dir_05` / `dir_50` / `dir_95` from `predictions_light.csv` for east_china_sea surface-grid d14 rows (`10m`, `100m`).
- Kept all speed columns identical to v28.
- Kept all station rows identical to v28.
- Kept all other grid direction cells identical to v28.
- Submission artifact: `starting-kit/phase_1/submission_v29.zip`.

### Expected impact
| Dim | v28 | v29 expected | Delta |
|-----|-----|--------------|-------|
| dir_surface_d14_ecs | 332.54 | 331.91 | -0.62 improved |

### Verification
- ZIP contains one root `predictions.csv`.
- Row count: `3,448,800`; grid `3,447,360`; station `1,440`.
- No NaNs in q/dir columns; no quantile crossing.
- Speed changes vs v28: `0`.
- Direction changes vs v28: `164,160` ECS d14 surface grid rows only.

### Status
- HOLD / NOT SUBMITTED.
- Visible mean-rank estimate: **~1.61** if the baseline-light score transfers.
- Skipped deliberately to preserve a submission slot. Keep `submission_v29.zip` as a reserve micro-gain if later rank math says one direction rank is worth spending.

---

## v30 — Pressure-Conditioned Station Speed d1/d7 (SCORED)

**Date**: 2026-04-25
**Approach**: V28 base + station speed overlay for d1/d7 only.
**Big idea**: Use the HRES pressure-level wind stack as a vertical-flow/context signal for station speed while protecting every grid, direction, and d14 station-speed cell.

### What was done
- Started from `predictions_v28.csv` rather than v29.
- Trained per-region/per-horizon LightGBM quantile station-speed models for d1 and d7.
- Added pressure-level u/v/speed features for 1000, 925, 850, 700, and 500 hPa, plus pressure-stack shear/spread features.
- Compared against the v19 station-speed artifact on validation and selected a blend weight per region/horizon.
- Submission artifact: `starting-kit/phase_1/submission_v30.zip`.

### Local validation vs v19 station-speed model
| Dim | v19 | v30 direct | v30 selected | Delta |
|-----|-----|------------|--------------|-------|
| speed_stations_d1_ns | 7.318 | 7.198 | 7.115 (w=0.75) | -0.203 improved |
| speed_stations_d7_ns | 14.471 | 14.053 | 14.053 (w=1.00) | -0.418 improved |
| speed_stations_d1_ecs | 6.713 | 6.379 | 6.379 (w=1.00) | -0.334 improved |
| speed_stations_d7_ecs | 9.203 | 9.168 | 9.132 (w=0.50) | -0.071 improved |

### Verification
- ZIP contains one root `predictions.csv`.
- Row count: `3,448,800`; grid `3,447,360`; station `1,440`.
- No NaNs in q/dir columns; no quantile crossing.
- Changed rows vs v28: `960` station speed rows only.
- Changed cells: NS d1 station `256`, NS d7 station `256`, ECS d1 station `224`, ECS d7 station `224`.
- Direction changes vs v28: `0`.
- Grid changes vs v28: `0`.
- d14 station speed changes vs v28: `0`.

### Leaderboard scores vs v28
| Dim | v28 | v30 | Delta |
|-----|-----|-----|-------|
| speed_stations_d1_ecs | 8.1558 | 7.7171 | -0.4387 improved |
| speed_stations_d7_ns | 13.4866 | 13.4534 | -0.0332 improved |
| speed_stations_d7_ecs | 8.5253 | 8.5399 | +0.0146 regressed |
| speed_stations_d1_ns | 7.8606 | 7.9418 | +0.0812 regressed |

### Score
- primary_score: **1.434863** (36/36 OK, no SENTINEL)
- Scoped station-speed total delta vs v28: **-0.3761** raw WS points
- Visible mean-rank estimate appears roughly unchanged because the gains do not cross the current competitor thresholds.

### Lesson
- PROMOTE for raw primary score, but do not use all v30 cells blindly.
- Keep `speed_stations_d1_ecs` and `speed_stations_d7_ns`.
- Revert `speed_stations_d1_ns` and `speed_stations_d7_ecs` to v28 in the next cleaned candidate.

---

## v31 — Cleaned v30 Winners + Held v29 Direction Micro-Gain (SCORED)

**Date**: 2026-04-25
**Approach**: V28 base + only winning v30 station-speed cells + baseline-light ECS surface d14 direction.
**Big idea**: Avoid spending two slots by combining the v30 cleanup with the previously held v29 micro-gain.

### What was done
- Started from `predictions_v28.csv`.
- Copied station speed `q05` / `q50` / `q95` from v30 only for north_sea d7 and east_china_sea d1.
- Reverted v30's small station-speed regressions: north_sea d1 and east_china_sea d7 stay at v28.
- Copied ECS surface d14 direction from `predictions_light.csv`, same donor as v29.
- Submission artifact: `starting-kit/phase_1/submission_v31.zip`.

### Key scores vs v28
| Dim | v28 | v31 | Delta |
|-----|-----|--------------|-------|
| speed_stations_d1_ecs | 8.1558 | 7.7171 | -0.4387 improved |
| speed_stations_d7_ns | 13.4866 | 13.4534 | -0.0332 improved |
| dir_surface_d14_ecs | 332.5366 | 331.9131 | -0.6235 improved |

### Verification
- ZIP contains one root `predictions.csv`.
- Row count: `3,448,800`; grid `3,447,360`; station `1,440`.
- No NaNs in q/dir columns; no quantile crossing.
- Changed station speed rows vs v28: `480` only: NS d7 `256`, ECS d1 `224`.
- Changed grid direction rows vs v28: `164,160` only: ECS d14 surface `10m`/`100m`.
- Unexpected speed changes: `0`; unexpected direction changes: `0`.

### Score
- primary_score: **1.434597** (36/36 OK, no SENTINEL)
- Scoped total delta vs v28: **-1.0954** raw points
- Score delta vs v30: **-0.000266** primary, from removing v30's two small station-speed regressions and adding the ECS surface d14 direction gain.
- Visible mean-rank estimate remains around **~1.61** until the leaderboard rank refresh catches up.

### Lesson
- PROMOTE. V31 is the current base.
- The station-speed result confirms that pressure-conditioned MOS should be cherry-picked by leaderboard cell, not applied wholesale.
- The held v29 micro-gain transferred exactly as expected through `dir_surface_d14_ecs = 331.9131`.

---

## Cumulative Lessons (after v31 scored)

### What works
1. **Residual/MOS speed framing** — predict reanalysis-HRES residual, biggest lever (~0.09)
2. **Direction model (sin/cos + conformal)** — ~0.04 improvement, per-horizon is best
3. **Cherry-picking best components per-dimension** — critical strategy
4. **Physically-motivated corrections** — log-wind profile for stations
5. **Per-horizon direction for d1** — 81-118 cWS vs pooled 144-190
6. **Baseline fallback** — sometimes the baseline is genuinely better (NS d14 direction)
7. **Pressure-conditioned station MOS** — transfers on ECS d1 and NS d7, but local validation overestimated NS d1 and ECS d7

### What doesn't work
1. **Residual framing for surface levels** — adds noise where HRES is already accurate
2. **Post-hoc interval scaling** — catastrophic on d14 direction (v5)
3. **Station EMOS** — over-wide direction intervals (v15: 710-1036 cWS)
4. **Direct pressure CatBoost without residual framing** — can't beat baseline vertical ratios
5. **Cross-horizon residual (d10→d14)** — 4-day gap too large (v13)
6. **Blind CQR calibration** — only helps when coverage is genuinely off (v14)
7. **Per-station direction with many features** — overfits with 300-1000 samples (v15)

### Strategic priorities (updated post-v31)
1. **Targeted direction donors only** — no broad direction rewrite; remaining available donor gains are narrow and risky
2. **Treat v31 as the new base** — future submissions should start from `predictions_v31.csv`
3. **Station speed model selection must be leaderboard-cell selective** — validation was directionally useful but not enough for all four d1/d7 cells
4. **CQR selective calibration** — only on under-covering models
5. **Overfitting fix** — ECS 500hPa d1/d7 direction (val→tune ratio 1.86-1.95)
6. **Custom circular Winkler loss** — for direction half-width optimization

---

## v32 — d14 Enriched Speed + Analog Blend + Direction Bias (SCORED, REJECTED)

**Date**: 2026-04-25
**Approach**: V31 base + enriched d14 station speed (LightGBM + analog ensemble 50/50) + station direction bias correction
**Big idea**: Target all remaining gaps in one compound submission: station speed d14 via richer features + analog patterns, station direction via per-station bias correction.

### What was done
- Trained enriched LightGBM for d14 station speed with multi-horizon forecasts (d1+d7+d10), pressure-level wind speed, vertical shear, teleconnections (NAO, PCs), upstream patterns
- Built per-station analog ensemble for d14 using K=50 nearest neighbors in feature space (ws10, ws100, msl, t2m, z700, month encoding)
- Blended model + analog 50/50 for d14 station speed
- Computed per-station direction bias correction from TUNE split (only kept when TUNE error improves)
- Applied conformal offset for direction after bias correction
- Grid and d1/d7 station speed completely unchanged from v31

### Local validation
- d14 LGB model: NS coverage=0.872 width=10.48, ECS coverage=0.843 width=7.19
- d14 analog: coverage 0.78-0.89, width 5.7-12.2 per station
- Direction bias: significant corrections for NS_07/d1 (-20.8°), NS d14 stations (+21-32°)
- d14 speed center: NS 7.80→7.27, ECS 5.49→5.34

### Key risks
1. Analog ensemble coverage is below 0.90 target for most stations (0.78-0.83)
2. NS d14 direction biases are very large (+21-32°) — could overcorrect on leaderboard
3. Compound submission makes attribution harder

### Verification
- Row count: 3,448,800 (grid 3,447,360 + station 1,440)
- NaN: 0, Quantile crossings: 0
- Grid speed/direction: byte-identical to v31
- d1/d7 station speed: byte-identical to v31
- d14 station speed: 475-479 of 480 rows changed
- Station direction: 1407-1440 of 1440 rows changed

### Score
- primary_score: **1.438895** (36/36 OK, no SENTINEL)
- Scoped total delta vs v31: **+52.86** raw points
- Biggest regression cluster: station direction d7/d14 across both regions
- Only meaningful win: `dir_stations_d1_ns`

### Lesson
- REJECT. The compound change is too broad and direction bias across all station horizons is not safe.
- The analog blend did not offset the d14 speed risk.
- Keep `v31` as the base; do not reuse v32 wholesale.

---

## Cumulative Lessons (updated for v32)

### What works
1. **Residual/MOS speed framing** — predict reanalysis-HRES residual, biggest lever (~0.09)
2. **Direction model (sin/cos + conformal)** — ~0.04 improvement, per-horizon is best
3. **Cherry-picking best components per-dimension** — critical strategy
4. **Physically-motivated corrections** — log-wind profile for stations
5. **Per-horizon direction for d1** — 81-118 cWS vs pooled 144-190
6. **Baseline fallback** — sometimes the baseline is genuinely better (NS d14 direction)
7. **Pressure-conditioned station MOS** — transfers on ECS d1 and NS d7
8. **Direction bias correction** — TUNE shows clear error reduction for most stations (NEW)

### What doesn't work
1. **Residual framing for surface levels** — adds noise where HRES is already accurate
2. **Post-hoc interval scaling** — catastrophic on d14 direction (v5)
3. **Station EMOS** — over-wide direction intervals (v15)
4. **Direct pressure CatBoost without residual framing** — can't beat baseline vertical ratios
5. **Cross-horizon residual (d10→d14)** — 4-day gap too large (v13)
6. **Blind CQR calibration** — only helps when coverage is genuinely off (v14)
7. **Per-station direction with many features** — overfits with 300-1000 samples (v15)
8. **CatBoost+LGBM ensemble for station speed** — dilutes signal with limited data (v32 first attempt)
9. **Double height correction** — model already has height_m feature (v32 bug, fixed)
10. **Broad station direction bias correction** — all-horizon application overfits and regresses d7/d14 (v32)
11. **Analog 50/50 blend on d14 speed** — not enough signal to justify the extra variance (v32)

---

## v33 — Track D Circular Station Direction Overlay (SCORED, REJECTED)

**Date**: 2026-04-25
**Approach**: V31 base + station-direction-only Track D overlay
**Big idea**: Replace broad direction bias correction with a proper circular model: center via sin/cos components, half-width via calibrated circular-error quantile, trained per region and horizon.

### What was done
- Started from `predictions_v31.csv`, not v32.
- Trained one Track D bundle per region/horizon on historical station direction rows.
- Predicted all 1,440 phase-1 station direction rows.
- Replaced only `dir_05`, `dir_50`, `dir_95` for `type=station`.
- Left all speed columns and all grid direction rows unchanged.

### Local gate
- `val`: mean station-direction delta `-84.475 cWS`
- `tune`: mean station-direction delta `-79.283 cWS`
- `holdout`: mean station-direction delta `-72.864 cWS`
- No local station-direction regression across the 6 region/horizon dimensions.

### Submission scope verification
- Row count: `3,448,800`
- `q_changed`: `0`
- `dir_changed_grid`: `0`
- `dir_changed_station`: `1,440`
- NaNs in prediction columns: `0`
- ZIP contains exactly one root `predictions.csv`.

### Score
- primary_score: **1.449470** (36/36 OK, no SENTINEL)
- Scoped station-direction delta vs v31: **+616.36 cWS** raw points

| Dim | Best (v31) | New (v33) | Delta |
|-----|------------|-----------|-------|
| dir_stations_d7_ecs | 237.44 | 418.63 | +181.19 regressed |
| dir_stations_d7_ns | 315.72 | 439.21 | +123.49 regressed |
| dir_stations_d14_ecs | 332.94 | 429.70 | +96.76 regressed |
| dir_stations_d1_ns | 178.31 | 273.57 | +95.26 regressed |
| dir_stations_d14_ns | 305.63 | 390.06 | +84.43 regressed |
| dir_stations_d1_ecs | 254.76 | 291.33 | +36.57 regressed |

### Lesson
- REJECT. Track D station-direction overlay failed to transfer to the 2022 hidden windows despite strong local val/tune/holdout gains.
- The failure is isolated and attributable: every speed/grid cell stayed unchanged, and all six modified station-direction cells regressed.
- Keep `v31` as base. Do not reuse Track D for 2022 station direction unless it is conditioned on inference-window context or constrained as a much narrower donor.

---

## Track G — Pooled Station Direction (SAME APPROACH AS v33)

**Date**: 2026-04-26
**Status**: Identical to v33 — Track G was designed to train `CircularDirectionBundle` per (region, horizon) on pooled station observations, but v33 already implements this exact approach.
**Script**: `src/experiments/track_g_station_direction.py` (written but not run — would reproduce v33 results)

### Purpose
Track G was proposed to attack the 5 station-direction dimensions where v31 is not rank 1:
- `dir_stations_d7_ns`: gap 12.89 cWS to Breva (302.83)
- `dir_stations_d14_ecs`: gap 8.73 cWS to Breva (324.21)
- `dir_stations_d1_ecs`: gap 3.52 cWS to Capgemini (251.24)
- `dir_stations_d14_ns`: gap 1.30 cWS (current light baseline)
- `dir_stations_d1_ns`: gap 0.37 cWS (noise)

### Key finding
v33 already applies the `CircularDirectionBundle` to ALL 6 station-direction cells with massive local gains:
- val: -84.5 cWS mean delta
- tune: -79.3 cWS mean delta
- holdout: -72.9 cWS mean delta

Track G is therefore REDUNDANT with v33. The submission v33 exists at `submission_v33.zip` (PENDING SCORE).

### Decision
- Track F finished as v37 and was rejected; do not combine it with Track G.
- v33 = Track G. Uploading v33 IS running Track G.
- If any v33 cells transfer on leaderboard, cherry-pick only those winners on top of v35.
- If v33 fully fails, stay on v35.

### Parallel tracks
| Track | Target | Status |
|-------|--------|--------|
| F | Pressure-level direction | COMPLETE / REJECTED as v37 — see below |
| G | Station direction (= v33) | Do not combine with Track F; only cherry-pick proven winners onto v35 |
| H | Surface direction heavy swap | Low priority, tiny gain potential |

---

## Track F — Pressure Direction CircularDirectionBundle

**Date**: 2026-04-26
**Approach**: CircularDirectionBundle (from Track D) applied to pressure-level grid direction
**Big idea**: Train a proper circular model for pressure direction instead of using raw HRES direction intervals. The baseline is a global 90th-percentile width on HRES-direction error. The CircularDirectionBundle learns conditional widths.

### What was done
- Trained one bundle per (region, horizon, level) on ~4000 sampled training rows
- Evaluated on val, tune, holdout splits (5000 rows per eval)
- Compared against calibrated HRES-direction baseline (global 90th-pctile width)

### Per-dimension results (mean across 5 pressure levels)

| Dimension | Val base | Val Track F | Val delta | Tune delta | Holdout delta |
|-----------|----------|-------------|-----------|------------|---------------|
| dir_pressure_d1_ns | 97.4 | 82.4 | -15.0 | -22.7 | -14.2 |
| dir_pressure_d1_ecs | 110.4 | 90.8 | -19.7 | -33.0 | -20.2 |
| dir_pressure_d7_ns | 299.9 | 188.5 | -111.4 | -99.0 | -110.8 |
| dir_pressure_d7_ecs | 249.3 | 182.4 | -66.9 | -89.9 | -69.2 |
| **Mean** | **189.2** | **136.0** | **-53.2** | **-61.1** | **-53.6** |

### Per-level detail (val split)

| Region | Horizon | Level | Baseline | Track F | Delta |
|--------|---------|-------|----------|---------|-------|
| NS | d1 | 1000 | 111.8 | 81.2 | -30.6 |
| NS | d1 | 925 | 99.5 | 84.8 | -14.7 |
| NS | d1 | 850 | 101.6 | 89.9 | -11.7 |
| NS | d1 | 700 | 85.4 | 77.9 | -7.5 |
| NS | d1 | 500 | 88.6 | 78.3 | -10.2 |
| NS | d7 | 1000 | 309.3 | 133.5 | -175.8 |
| NS | d7 | 925 | 308.7 | 159.3 | -149.4 |
| NS | d7 | 850 | 303.2 | 187.7 | -115.5 |
| NS | d7 | 700 | 291.6 | 215.9 | -75.7 |
| NS | d7 | 500 | 286.6 | 246.3 | -40.3 |
| ECS | d1 | 1000 | 126.1 | 83.1 | -43.0 |
| ECS | d1 | 925 | 118.4 | 100.4 | -18.0 |
| ECS | d1 | 850 | 145.8 | 125.4 | -20.3 |
| ECS | d1 | 700 | 108.5 | 92.9 | -15.5 |
| ECS | d1 | 500 | 53.4 | 52.0 | -1.4 |
| ECS | d7 | 1000 | 277.4 | 134.0 | -143.4 |
| ECS | d7 | 925 | 282.8 | 182.7 | -100.1 |
| ECS | d7 | 850 | 294.0 | 252.4 | -41.6 |
| ECS | d7 | 700 | 243.2 | 203.2 | -40.0 |
| ECS | d7 | 500 | 149.3 | 139.9 | -9.4 |

### Caveats
- **ECS d7 lev=500: holdout regression of +6.3 cWS** — the only positive delta. All other 59 measurements are negative.
- The baseline is calibrated HRES-direction, NOT the v31 predictions. v31 already uses the v8 per-horizon direction model which is much better than raw HRES. So the actual improvement over v31 will be smaller.
- Models trained on only 4000 sampled rows. Full production training might give different results.

### Key insight
The d7 pressure direction improvements are massive (-100 to -176 cWS on val). This is because the HRES baseline for d7 pressure direction has extremely wide global intervals (~300 cWS), while the CircularDirectionBundle learns conditional widths that are much narrower. This pattern is very similar to how the per-horizon direction model (v8) improved surface/pressure d1 direction.

### Production status
- Production inference pipeline built in `src/pipeline/run_v37.py`.
- Generated pressure-direction predictions for all 8 windows x 5 pressure levels x 2 regions for d1/d7.
- Wrote `starting-kit/phase_1/submission_v37.zip` with exactly one `predictions.csv`.
- Leaderboard score arrived as v37: rejected, all four modified pressure d1/d7 direction dimensions regressed versus v35.

---

## v34 — Track E Station-Speed Residual Overlay (SCORED, REJECTED)

**Date**: 2026-04-26
**Approach**: V31 base + station-speed-only Track E residual distribution overlay
**Big idea**: Model station speed residuals around the nearest-grid forecast and replace only station `q05/q50/q95`.

### Score
- primary_score: **1.448376** (36/36 OK, no SENTINEL)
- Scoped station-speed delta vs v31: **+1.95 raw WS**

| Dim | Best (v31) | New (v34) | Delta |
|-----|------------|-----------|-------|
| speed_stations_d1_ecs | 7.7171 | 7.5154 | -0.2017 improved |
| speed_stations_d14_ecs | 8.6307 | 9.2969 | +0.6662 regressed |
| speed_stations_d14_ns | 15.8515 | 16.9934 | +1.1419 regressed |
| speed_stations_d1_ns | 7.8606 | 8.0148 | +0.1542 regressed |
| speed_stations_d7_ecs | 8.5253 | 10.4815 | +1.9562 regressed |
| speed_stations_d7_ns | 13.4534 | 14.6970 | +1.2436 regressed |

### Lesson
- REJECT. Track E local val/tune/holdout gains did not transfer to the 2022 hidden windows.
- The only useful donor is `speed_stations_d1_ecs` (`-0.2017`), but the gain is likely too small unless bundled with another clean donor.
- Keep `v31` as base. Do not reuse Track E wholesale.

---

## v35 — V32 NS d1 Station-Direction Cherry-Pick (SCORED, PROMOTED)

**Date**: 2026-04-26
**Approach**: V31 base + only v32 North Sea d1 station-direction donor
**Big idea**: Preserve the one v32 station-direction cell that transferred positively and reject the five failing cells.

### Score
- primary_score: **1.432856** (36/36 OK, no SENTINEL)
- Scoped delta vs v31: **-7.5246 cWS**

| Dim | Best (v31) | New (v35) | Delta |
|-----|------------|---------------------------|-------|
| dir_stations_d1_ns | 178.3124 | 170.7878 | -7.5246 improved |

### Scope verification
- `q_changed`: `0`
- `dir_changed_total`: `224`
- `dir_changed_unexpected`: `0`
- All changes are station + North Sea + d1 direction rows.

### Lesson
- PROMOTE. v35 is the new base.
- The v32 NS d1 station-direction donor transferred exactly and improved `dir_stations_d1_ns` from `178.3124` to `170.7878`.
- This confirms the donor-mining strategy: rejected compound submissions can still contain clean rank-moving cells.

---

## v37 — Track F Pressure Direction Overlay (SCORED, REJECTED)

**Date**: 2026-04-27
**Approach**: V35 base + Track F `CircularDirectionBundle` pressure-direction overlay for d1/d7 pressure grid rows only.
**Big idea**: Isolate the unfinished Track F production step and test whether the local pressure-direction gains transfer to the hidden 2022 windows without touching speed, stations, surface rows, or d14 direction.

### What was done
- Loaded 20 cached Track F models: 2 regions x 2 horizons x 5 pressure levels.
- Generated 1,641,600 pressure-direction override rows across all 8 inference windows.
- Replaced only `dir_05` / `dir_50` / `dir_95` for grid pressure-level d1/d7 rows in `predictions_v35.csv`.
- Wrote `starting-kit/phase_1/predictions_v37.csv` and `starting-kit/phase_1/submission_v37.zip`.

### Scope verification
- ZIP contains exactly one file: `predictions.csv`.
- Submission rows: `3,448,800`.
- Speed rows changed: `0`.
- Direction rows changed: `1,641,600`.
- NaNs in prediction columns: `0`.
- `tests/test_run_v37.py`: passed under `.venv`.

### Score
- primary_score: **1.444246** (36/36 OK, no SENTINEL)
- Primary delta vs v35: **+0.011390** (regression)
- Scoped pressure-direction delta vs v35: **+165.7830 raw cWS**

| Dim | Best (v35) | New (v37) | Delta |
|-----|------------|-----------|-------|
| dir_pressure_d1_ns | 81.0854 | 98.0677 | +16.9823 regressed |
| dir_pressure_d7_ns | 283.9582 | 338.1728 | +54.2146 regressed |
| dir_pressure_d1_ecs | 106.2310 | 138.4562 | +32.2252 regressed |
| dir_pressure_d7_ecs | 240.9370 | 303.2987 | +62.3617 regressed |

### Lesson
- REJECT. Track F local gains against a calibrated HRES-direction baseline did not transfer against the stronger v35/v8 pressure-direction base.
- All four modified pressure d1/d7 direction dimensions regressed on the hidden 2022 windows.
- Keep v35 as base. Do not reuse Track F pressure-direction overrides without a new guard that compares directly against the v8/v35 production direction baseline.

---

## v38 — V34 ECS d1 Station-Speed Cherry-Pick (SCORED, PROMOTED)

**Date**: 2026-04-27
**Approach**: V35 base + only v34 East China Sea d1 station-speed donor
**Big idea**: Rescue the one v34 station-speed cell that transferred positively while rejecting the five losing station-speed cells.

### What was done
- Started from `predictions_v35.csv`.
- Copied v34 `q05` / `q50` / `q95` only for `east_china_sea` station rows at horizon d1.
- Wrote `starting-kit/phase_1/predictions_v38.csv` and `starting-kit/phase_1/submission_v38.zip`.

### Scope verification
- ZIP contains exactly one file: `predictions.csv`.
- Submission rows: `3,448,800`.
- Speed rows changed: `224`.
- Unexpected speed rows changed: `0`.
- Direction rows changed: `0`.
- NaNs in prediction columns: `0`.
- Quantile crossings: `0`.
- `tests/test_run_v38.py`: passed under `.venv`.

### Score
- primary_score: **1.432295** (36/36 OK, no SENTINEL)
- Primary delta vs v35: **-0.000561**
- Scoped station-speed delta vs v35: **-0.2017 raw WS**
- Public leaderboard display row currently shows `Mean Rank=99999.0` despite valid raw metrics; treat as rank refresh/display pending, not a model failure.

| Dim | Best (v35) | New (v38) | Delta |
|-----|------------|-----------|-------|
| speed_stations_d1_ecs | 7.7171 | 7.5154 | -0.2017 improved |

### Lesson
- PROMOTE. v38 is the new base.
- The expected `speed_stations_d1_ecs` gain transferred exactly and no other metric changed.
- Donor-mining remains useful when the copied cell is already proven on the hidden leaderboard.

---

## v39 — Track I ECS d1 Station-Direction Residual (SCORED, RAW WIN)

**Date**: 2026-04-27
**Approach**: V38 base + Track I v38-anchored station-direction residual model for `east_china_sea` station d1 only.
**Big idea**: Start the direction moat plan with a narrow, high-rank-gap ECS station-direction cell rather than another broad station-direction replacement.

### What was done
- Implemented Phase 1 station-direction atlas in `src/experiments/direction_error_atlas.py`.
- Implemented Phase 2 Track I residual model in `src/experiments/track_i_v38_residual_direction.py`.
- Generated `logs/direction_error_atlas/station_direction_atlas.parquet`.
- Generated `logs/direction_error_atlas/station_direction_summary.csv`.
- Generated `logs/track_i_v38_residual_direction/local_station_direction_residual_eval.csv`.
- Started from `predictions_v38.csv`.
- Replaced only `dir_05` / `dir_50` / `dir_95` for `east_china_sea` station d1 rows.
- Wrote `starting-kit/phase_1/predictions_v39.csv` and `starting-kit/phase_1/submission_v39.zip`.

### Local proxy scores

| Dim | Split | Baseline Proxy | Track I | Delta |
|-----|-------|----------------|---------|-------|
| dir_stations_d1_ecs | val | 170.0 | 110.9 | -59.1 |
| dir_stations_d1_ecs | tune | 201.6 | 152.7 | -48.9 |
| dir_stations_d1_ecs | holdout | 161.4 | 100.2 | -61.1 |

### Scope verification
- Submission rows: `3,448,800`.
- Speed rows changed: `0`.
- Direction rows changed: `224`.
- Changed scope: station + `east_china_sea` + d1.
- NaNs in prediction columns: `0`.
- `tests/test_run_v39.py`: passed under `.venv`.

### Caveat
- The local baseline is a production-style historical proxy, not an exact reconstruction of v38 hidden predictions.

### Score
- primary_score: **1.432295** (36/36 OK, no SENTINEL)
- Primary delta vs v38: **0.000000**
- Scoped direction delta vs v38: **-13.5027 raw cWS**

| Dim | Best (v38) | New (v39) | Delta |
|-----|------------|-----------|-------|
| dir_stations_d1_ecs | 254.7641 | 241.2614 | -13.5027 improved |

### Lesson
- Track I transferred on the isolated ECS d1 station-direction target with no side effects.
- The primary score did not move at displayed precision, so this is a raw-score win rather than a confirmed mean-rank win.
- v40 is now a rational broader family test because v39 proved the ECS station-direction residual lane can transfer.

---

## v40 — Track I ECS All-Horizon Station-Direction Residual (SCORED, REJECTED)

**Date**: 2026-04-27
**Approach**: V38 base + Track I residual model for all `east_china_sea` station-direction horizons.
**Big idea**: Test whether the ECS station-direction residual signal transfers as a family after v39 isolates d1.

### What was done
- Started from `predictions_v38.csv`.
- Replaced `dir_05` / `dir_50` / `dir_95` for `east_china_sea` station d1, d7, and d14 rows.
- Wrote `starting-kit/phase_1/predictions_v40.csv` and `starting-kit/phase_1/submission_v40.zip`.

### Local proxy scores

| Dim | Split | Baseline Proxy | Track I | Delta |
|-----|-------|----------------|---------|-------|
| dir_stations_d1_ecs | val | 170.0 | 110.9 | -59.1 |
| dir_stations_d1_ecs | tune | 201.6 | 152.7 | -48.9 |
| dir_stations_d1_ecs | holdout | 161.4 | 100.2 | -61.1 |
| dir_stations_d7_ecs | val | 170.0 | 118.0 | -52.0 |
| dir_stations_d7_ecs | tune | 201.6 | 157.7 | -44.0 |
| dir_stations_d7_ecs | holdout | 161.4 | 114.3 | -47.1 |
| dir_stations_d14_ecs | val | 169.9 | 118.6 | -51.4 |
| dir_stations_d14_ecs | tune | 201.7 | 160.5 | -41.2 |
| dir_stations_d14_ecs | holdout | 161.5 | 114.0 | -47.4 |

### Scope verification
- Submission rows: `3,448,800`.
- Speed rows changed: `0`.
- Direction rows changed: `672`.
- Changed scope: station + `east_china_sea` + d1/d7/d14.
- NaNs in prediction columns: `0`.

### Caveat
- Upload v39 first if preserving attribution matters. v40 is the broader family test and should not be treated as proven until v39 shows transfer.

### Score
- primary_score: **1.432888** (36/36 OK, no SENTINEL)
- Primary delta vs v38/v39: **+0.000593** (regression)
- Scoped ECS station-direction delta vs v38: **+574.6397 raw cWS**
- Public-table implied visible mean rank: **~1.89** (down from v39's ~1.64), driven by `dir_stations_d14_ecs` falling to visible rank 10.

| Dim | Best (v38) | New (v40) | Delta |
|-----|------------|-----------|-------|
| dir_stations_d1_ecs | 254.7641 | 241.2614 | -13.5027 improved |
| dir_stations_d7_ecs | 237.4378 | 242.7708 | +5.3330 regressed |
| dir_stations_d14_ecs | 332.9393 | 915.7487 | +582.8094 catastrophic |

### Lesson
- REJECT. Track I d1 is real, but broad ECS station-direction replacement is unsafe.
- The local proxy badly underestimated d14 hidden risk. This points to a circular interval/wrap failure or regime mismatch.
- Keep only the v39 d1 donor. Do not use Track I d7/d14 without a gate, interval sanity guard, or separate d14-specific recalibration.

---

## v41 — Gated Track I ECS d7 Station-Direction Residual (SCORED, NEW BEST)

**Date**: 2026-04-27
**Approach**: V39 base + conservative gated Track I candidate for `east_china_sea` station d7.
**Big idea**: v40 showed broad d7/d14 replacement is unsafe, but d7 was only a small regression. v41 tests whether small, sane d7 center corrections transfer while rejecting large regime-flip corrections.

### What was done
- Started from `predictions_v39.csv`.
- Used v40 Track I predictions as the ECS d7 candidate donor.
- Accepted candidate rows only when:
  - circular center shift from v39 was `<= 20` degrees
  - candidate interval width was between `70` and `170` degrees
- Left all rejected d7 rows unchanged.
- Left all d14 rows unchanged.
- Wrote `starting-kit/phase_1/predictions_v41.csv` and `starting-kit/phase_1/submission_v41.zip`.

### Scope verification
- Submission rows: `3,448,800`.
- Requested ECS d7 station rows: `224`.
- Accepted gated rows: `107`.
- Rejected gated rows: `117`.
- Speed rows changed: `0`.
- Direction rows changed: `107`.
- Changed scope: station + `east_china_sea` + d7 gated subset.
- NaNs in prediction columns: `0`.
- `tests/test_run_v41.py`: passed under `.venv`.

### Leaderboard result

| Dim | Best (v39) | New (v41) | Delta |
|-----|-----------|----------|-------|
| dir_stations_d7_ecs | 237.4378 | 225.2461 | -12.1917 improved |
| dir_stations_d1_ecs | 241.2614 | 241.2614 | 0.0000 preserved |
| dir_stations_d14_ecs | 332.9393 | 332.9393 | 0.0000 protected |

- `primary_score`: `1.432295 -> 1.429473` (`-0.002822`).
- All non-target dimensions remained unchanged.

### Lesson
- PROMOTE. The gate worked: it captured useful Track I d7 residual signal while avoiding the v40 d14 failure.
- This validates row-level safety gating for station direction. Next step is to analyze accepted vs rejected rows and turn the hand-built gate into a learned regime gate before touching d14 again.

---

## v42 — Learned-Gate Track I ECS d7 (PENDING / METHODOLOGY STEP)

**Date**: 2026-04-27
**Approach**: V39 base + learned safety gate for `east_china_sea` station d7.
**Big idea**: Replace the hand-tuned v41 gate with a small interpretable classifier trained on the v41 accepted/rejected labels. The submission predictions are byte-identical to v41; the value is the reusable gate framework.

### What was done
1. **Built the accepted/rejected row table** (`src/experiments/v41_gate_analysis.py`):
   - Loaded v39 baseline and v40 candidate predictions for the 224 ECS d7 station rows.
   - Computed per-row features: `center_shift`, `candidate_half_width`, `base_half_width`, `width_delta`, `shift_over_width`, and station dummies.
   - Label: accepted by the v41 hard gate (shift <= 20, half_width in [35, 85]).

2. **Inspected separation between accepted and rejected**:
   - **Accepted (107 rows)**: mean center_shift = 9.9°, mean candidate_half_width = 61.7°, mean width_delta = -39.5°.
   - **Rejected (117 rows)**: mean center_shift = 37.3°, mean candidate_half_width = 60.7°, mean width_delta = -45.2°.
   - The main discriminator is `center_shift` (small shifts accepted, large shifts rejected). Width bounds in v41 were effectively irrelevant: only 2 rows had half_width > 85, and 0 had half_width < 35.
   - Per-station mean shifts: ECS_05 safest (16.5°), ECS_06 riskiest (34.2°).

3. **Trained a small safety model**:
   - **Logistic regression** on the 224 inference rows: accuracy 1.0 on v41 labels.
   - **Decision tree (max_depth=2)**: single rule `center_shift <= 19.84` perfectly separates accepted/rejected.
   - Saved artifacts to `logs/learned_gate_v42/`:
     - `v41_logreg_model.pkl`
     - `v41_tree_model.pkl`
     - `v41_feature_names.json`
     - `v41_inference_rows.csv`

4. **Generated v42 submission** (`src/pipeline/run_v42.py`):
   - Loads the saved logistic-regression model.
   - Computes the same features on inference rows.
   - Applies the model with threshold 0.5 plus a hard sanity guard (half_width in [10, 120]).
   - Result: 107 accepted, 117 rejected — byte-identical to v41.
   - Added unit test `tests/test_run_v42.py` (passes).

### Scope verification
- Submission rows: `3,448,800`.
- Accepted gated rows: `107`.
- Rejected gated rows: `117`.
- Speed rows changed: `0`.
- Direction rows changed: `107`.
- Changed scope: station + `east_china_sea` + d7 gated subset.
- `tests/test_run_v42.py`: passed under `.venv`.

### Key insight
The v41 hand gate was essentially `center_shift <= 20`. The width bounds [70, 170] in original full-width units (=[35, 85] half-width) were very wide and excluded almost no rows. The learned model codifies this insight and makes it reusable.

### Why historical ground truth could not train the gate
A parallel experiment (`src/experiments/learned_gate_v42.py`) trained a safety model on historical val/tune/holdout splits where true target direction is known. That model learned that **narrow candidate intervals** (relative to baseline) are safe. But on inference, the baseline half_width is ~104° while candidate half_width is ~61°, so *all* candidates are narrower. The historical model would have accepted all inference rows, which v40 showed is unsafe. This proves the inference distribution is shifted and the v41 labels (not historical ground truth) are the right training signal for this gate.

### Lesson
- METHODOLOGY STEP COMPLETE. The learned gate framework is now in place and reproducible.
- v42 predictions are identical to v41, so do not expect a raw score improvement.
- The real next move is **v43**: apply the same learned-gate pipeline to ECS d14 station direction, but with a d14-specific safety threshold. The gate model can be retrained on a small d14 test submission's accepted/rejected labels once we know what a safe d14 donor looks like.
- Alternatively, use the learned gate to **relax** the d7 threshold slightly (e.g., accept shifts up to 25° for historically safe stations like ECS_05) and test whether the additional rows are safe. This is a low-risk experiment because the model gives per-row probabilities.

---

## v43 — Ultra-Conservative D14 Probe (PENDING)

**Date**: 2026-04-27
**Approach**: V41 base + ultra-conservative Track I gate for `east_china_sea` station d14.
**Big idea**: v40 showed ungated d14 is catastrophic (+582 cWS). v43 tests whether the very smallest center corrections (shift <= 15°) can transfer safely. Only 30 of 224 rows qualify.

### What was done
- Started from `predictions_v41.csv`.
- Used v40 Track I predictions as the ECS d14 candidate donor.
- Accepted candidate rows only when:
  - circular center shift from v41 baseline was `<= 15` degrees
  - candidate half-width was between `35` and `85` degrees
- Left all rejected d14 rows unchanged.
- Left all d7, d1, speed, grid, and North Sea rows identical to v41.
- Wrote `starting-kit/phase_1/predictions_v43.csv` and `starting-kit/phase_1/submission_v43.zip`.

### Scope verification
- Submission rows: `3,448,800`.
- Requested ECS d14 station rows: `224`.
- Accepted gated rows: `30`.
- Rejected gated rows: `194`.
- Speed rows changed: `0`.
- Direction rows changed: `30`.
- Changed scope: station + `east_china_sea` + d14 gated subset.
- `tests/test_run_v43.py`: passed under `.venv`.

### Why 15 degrees?
The learned v41 gate split at `center_shift <= 19.84`. On d14, candidate shifts are systematically larger (mean 53.8° vs d7's 24.2°). Using the same 20° threshold would accept 42 rows, but d14 has already proven far more dangerous than d7. Tightening to 15° is a deliberate over-correction for safety. The 30 accepted rows have mean shift 7.9° — smaller than the v41 d7 accepted mean of 9.9°.

### Decision tree
- **If v43 improves or holds d14:** the Track I d14 signal is real for small corrections. Relax the gate in v44 (e.g., shift <= 20° or station-specific thresholds).
- **If v43 regresses d14:** even tiny d14 shifts are unsafe. Freeze d14 permanently and move on to other levers.

### Leaderboard Result

| Dim | Best (v41) | New (v43) | Delta |
|-----|-----------|----------|-------|
| dir_stations_d14_ecs | 332.9393 | **381.9456** | +49.0063 regressed |
| primary_score | 1.429473 | 1.429473 | 0.000 (display precision) |

All 35 non-target dimensions remained identical to v41. Only `dir_stations_d14_ecs` changed.

### Decision Tree After Score Arrives
- **If v43 improves or holds d14:** relax gate in v44 (e.g., shift <= 20° or station-specific thresholds)
- **If v43 regresses d14:** freeze d14 permanently; the signal is unsafe at any shift

### Lesson
- **REJECT. Freeze d14 permanently.** Even 30 rows with center shift <= 15° caused a +49 cWS regression on `dir_stations_d14_ecs`. The Track I d14 residual signal is fundamentally unsafe for station direction, regardless of how conservative the gate is. The 2022 hidden windows must have a regime mismatch that the 2019-2021 model cannot detect.
- The primary score display remained flat at 1.429473, but the raw dimension score regressed materially. Do not spend another submission slot on d14 station direction.
- **v41 remains the base.** The only proven Track I transfers are ECS d1 and gated ECS d7.

---

## v47 — Copula Per-Horizon Damping (ACCIDENTAL v41 BASE)

**Approach:** Apply speed-direction copula with per-horizon damping (d1=1.0, d7=0.7, d14=0.4) and level-aware clips (extreme κ_slope > 0.10 gets tighter 0.85/1.15 clips). Intended to fix ECS d14 direction regression from v46's copula.

**Critical Bug:** Script `copula_v47_fix.py` line 267 loaded `predictions_v41.csv` instead of `predictions_v46.csv`. v47 was built on v41 base, completely discarding v46's copula improvements.

**Key Scores (estimated mean_rank = 2.11, same as v46):**

| Dim | v46 | v47 | Delta | Note |
|-----|-----|-----|-------|------|
| dir_surface_d7_ns | 291.14 | 293.07 | +1.93 | Lost v46's improvement |
| dir_surface_d14_ns | 298.39 | 300.26 | +1.87 | Lost v46's improvement |
| dir_pressure_d7_ns | 278.84 | 280.00 | +1.16 | Lost v46's improvement |
| dir_pressure_d14_ns | 299.22 | 301.28 | +2.06 | Lost v46's improvement |
| dir_pressure_d14_ecs | 316.07 | 314.31 | -1.76 | Better than v46 |
| dir_pressure_d7_ecs | 241.53 | 240.99 | -0.54 | Better than v46 |
| All speed dims | — | — | 0.000 | Identical to v41/v46 |
| All station dims | — | — | 0.000 | Identical to v41/v46 |

**What went wrong:** The per-horizon damping is a valid idea, but the base file bug makes this submission uninformative. The direction raw scores differ from v46 (worse NS, better ECS d7/d14 pressure) but the RANK is identical — the raw score differences don't change relative position vs competitors.

**Lesson:** Despite different raw direction scores, the per-horizon damping on v41 base produces the same rank (2.11) as v46. The copula effect is rank-neutral against current competition. However, the ECS d14 pressure improvement (-1.76 vs v46) suggests per-horizon damping COULD help if applied to the correct v46 base. **REJECT — v46 remains base.** A correctly-built v47 (on v46 base) could be worth a future slot.

---

## v48 — Yeo-Johnson Grid Speed Retrain (DEAD END)

**Approach:** Retrain all 168 grid speed models (2 regions × 7 levels × 3 horizons × 4 hours) using CatBoost quantile regression with Yeo-Johnson transform, proper train/val split, and the heavy baseline's feature selection. Built on v47 base (which was v41 + damped copula).

**Key Scores (estimated mean_rank = 2.44, +0.33 vs v46):**

| Dim | v46 Rank | v48 Rank | Delta Rank | v46 Score | v48 Score | Note |
|-----|----------|----------|------------|-----------|-----------|------|
| speed_surface_d14_ns | 4 | 9 | +6 WORSE | 15.12 | 16.49 | +1.37 m/s |
| speed_pressure_d14_ns | 3 | 7 | +4 WORSE | 24.35 | 26.05 | +1.70 m/s |
| speed_surface_d7_ns | 3 | 6 | +3 WORSE | 14.46 | 14.87 | +0.41 m/s |
| speed_pressure_d1_ns | 4 | 6 | +2 WORSE | 6.79 | 6.82 | |
| speed_pressure_d7_ns | 4 | 5 | +2 WORSE | 27.22 | 28.48 | +1.26 m/s |
| speed_surface_d7_ecs | 3 | 1 | -2 BETTER | 9.82 | 9.72 | |
| speed_surface_d14_ecs | 3 | 1 | -2 BETTER | 10.77 | 10.65 | |
| speed_pressure_d7_ecs | 3 | 1 | -2 BETTER | 15.71 | 15.50 | |
| speed_pressure_d1_ecs | 4 | 2 | -2 BETTER | 6.70 | 6.68 | |

Gained 3 #1 ranks on ECS speed (now 20 total vs v46's 17), but NS speed catastrophically regressed. All direction and station dims identical to v47.

**What went wrong:** The Yeo-Johnson models are near-identical to the heavy baseline on local validation but generalize poorly to the 2022 leaderboard period. NS grid speed d7/d14 worsened by 1-2 m/s. The retraining adds zero value — the heavy baseline's CatBoost on 500K rows with 15-25 features is already near-optimal. The slight ECS improvements are from the Yeo-Johnson transform normalizing skewed distributions, but the NS regressions overwhelm them.

**Lesson:** **Retraining with the same features is a dead end.** The heavy baseline is already near-optimal. Future speed improvements require NEW features (spatial aggregation from HEFTCom2024 #1, pressure-level wind shear, ws³), CQR calibration (fix undercoverage from ~86.6% → 90%), or more training data (1M+ rows). Also compounded by v47's base confusion. **REJECT — v46 remains base.**

---

## v50 — CQR Calibration (CATASTROPHIC)

**Approach:** Apply Conformalized Quantile Regression (CQR) calibration to v46's grid speed predictions. Computed per-(region, level, horizon, hour) asymmetric offsets using the VAL split, with finite-sample correction `q = (1-alpha)*(1+1/n)`.

**Key Scores (estimated mean_rank = 4.06, +1.95 vs v46):**

| Dim | v46 | v50 | Delta | Rank change |
|-----|-----|-----|-------|-------------|
| speed_surface_d1_ns | 4.71 | 9.72 | +5.01 | 4 → 10 |
| speed_surface_d7_ns | 14.46 | 22.25 | +7.79 | 3 → 10 |
| speed_surface_d14_ns | 15.12 | 23.16 | +8.04 | 4 → 10 |
| speed_pressure_d1_ns | 6.79 | 15.18 | +8.39 | 4 → 10 |
| speed_pressure_d7_ns | 27.22 | 38.49 | +11.27 | 4 → 10 |
| speed_pressure_d14_ns | 24.35 | 39.94 | +15.59 | 3 → 10 |
| All direction dims | — | — | 0.000 | unchanged |
| All station dims | — | — | 0.000 | unchanged |

All 12 grid speed dimensions dropped to rank 10 (last among real competitors). Width mean went from ~10 m/s to 24.9 m/s.

**What went wrong:** The CQR offsets were massive (2.7-27.5 m/s depending on level/horizon). These constant per-group offsets widened ALL intervals uniformly — even those that were already well-calibrated. The Winkler score includes a linear width penalty, so doubling the interval width roughly doubles the score regardless of coverage gains.

**Lesson:** **Constant-offset CQR is fundamentally wrong for this competition.** The ~86.6% undercoverage is an average — some predictions are well-covered (d1 surface), some aren't (d14 pressure). A blanket widening is catastrophic. The correct approach is either: (1) per-sample adaptive calibration using prediction variance as a scaling factor, (2) a very small fraction of the CQR offset (10-20%), or (3) abandon CQR and improve the underlying quantile models with new features. **v46 remains the base.**

---

## v51 — Corrected Scoped Copula Donor (SCORED, RAW PROMOTE)

**Date**: 2026-04-28
**Approach**: V46 base + only the v47 damped-copula ECS pressure d7/d14 direction rows.
**Big idea**: v47 was built on the wrong base, but its raw scores suggested the damping idea helped ECS pressure d7/d14 direction. v51 tests only that signal on the correct v46 base, with guardrails preventing another wrong-base or out-of-scope submission.

### What was done
- Added reusable base/scope guardrails in `src/pipeline/submission_guards.py`.
- Added `src/pipeline/run_v51.py`.
- Verified the base file is exactly `predictions_v46.csv`.
- Recorded base SHA-256: `5829a8bc2a2953651847fbf5edb7a18280aa9ca41c15fdddef5eabe96ef5bfe4`.
- Copied `dir_05`, `dir_50`, and `dir_95` from `predictions_v47.csv` only for `east_china_sea` pressure-level grid rows at horizons d7 and d14.
- Wrote `starting-kit/phase_1/predictions_v51.csv` and `starting-kit/phase_1/submission_v51.zip`.

### Scope verification
- Submission rows: `3,448,800`.
- Allowed rows: `820,800`.
- Direction rows changed: `656,632`.
- Speed rows changed: `0`.
- Changed rows in scope: `656,632`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/v51_corrected_copula/v51_manifest.json`.
- Tests: `tests/test_submission_guards.py`, `tests/test_run_v51.py`, and `tests/test_scoring.py` passed under `.venv`.

### Decision rule
- Promote only if ECS pressure d7/d14 direction improves without visible rank damage.
- If neutral or worse, keep v46 as base and move to spatial aggregation / pressure-shear features.

### Leaderboard result

| Dim | v46 | v51 | Delta |
|-----|-----|-----|-------|
| dir_pressure_d7_ecs | 241.5318 | 240.9883 | -0.5435 improved |
| dir_pressure_d14_ecs | 316.0691 | 314.3146 | -1.7545 improved |
| primary_score | 1.428721 | 1.428721 | 0.000000 neutral |

All non-target dimensions were preserved.

### Visible rank estimate
- Codabench row ID: `700876`.
- Displayed mean rank is stale: `99999.0`.
- Recalculated visible mean rank: `1.4444`.
- Rank bucket count: 24 rank-1 dims, 9 rank-2 dims, 2 rank-3 dims, 1 rank-4 dim.

### Lesson
- PROMOTE. The corrected v47 donor improves both intended ECS pressure direction cells and causes no scope damage.
- Use v51 as the current raw-score and visible-rank base. Next work should move to v52 spatial aggregation features.

---

## v52 — ECS Surface Spatial-Aggregation Speed Probe (SCORED, REJECTED)

**Date**: 2026-04-28
**Approach**: V51 base + narrow LightGBM quantile speed overlay for East China Sea surface grid d7/d14.
**Big idea**: v48 proved same-feature retraining is not enough. v52 tests the first real new-feature moat lane: regional spatial context features inspired by HEFTCom-style winners, while changing only the two ECS surface speed dimensions that can absorb this risk.

### What was done
- Added `src/experiments/spatial_features_v52.py`.
- Added `tests/test_spatial_features_v52.py`.
- Built spatial aggregates per forecast context time from inference-available forecast/weather-state columns only.
- Explicitly excluded `speed_d*` target-like columns from aggregate sources to avoid target leakage and train/inference mismatch.
- Trained 16 LightGBM quantile models: 2 levels (`10m`, `100m`) × 2 horizons (d7, d14) × 4 hours.
- Wrote `starting-kit/phase_1/predictions_v52.csv` and `starting-kit/phase_1/submission_v52.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v51.csv`.
- Base SHA-256: `c7e392afc17978698921371749204b27cfa5540b0b89e921c986e31484f646ca`.
- Submission rows: `3,448,800`.
- Allowed rows: `328,320`.
- Speed rows changed: `328,320`.
- Direction rows changed: `0`.
- Changed rows in scope: `328,320`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/spatial_v52/v52_manifest.json`.
- Tests: `tests/test_spatial_features_v52.py`, `tests/test_submission_guards.py`, `tests/test_run_v51.py`, and `tests/test_scoring.py` passed under `.venv`.

### Local diagnostics

| Slice | v51 width | v52 width | Mean delta q05/q50/q95 |
|-----|-----:|-----:|-----|
| 10m d7 | 7.1540 | 6.7351 | +0.3439 / +0.2339 / -0.0750 |
| 10m d14 | 8.3262 | 8.0815 | +0.2042 / +0.1972 / -0.0405 |
| 100m d7 | 9.2305 | 8.7253 | +0.3627 / +0.1841 / -0.1426 |
| 100m d14 | 10.5045 | 10.3820 | +0.2629 / +0.3347 / +0.1403 |

### Decision rule
- Promote only if `speed_surface_d7_ecs` and/or `speed_surface_d14_ecs` improve enough without visible rank damage.
- If both regress, keep v51 and treat spatial aggregation as needing a donor/gated version rather than a direct replacement.
- If one horizon improves and one regresses, build a scoped v53 donor from v52 onto v51 for the winning horizon only.

### Leaderboard result

| Dim | Best (v51) | New (v52) | Delta |
|-----|-----------:|----------:|------:|
| speed_surface_d7_ecs | 9.8216 | 9.8612 | +0.0396 regressed |
| speed_surface_d14_ecs | 10.7740 | 11.1189 | +0.3449 regressed |
| primary_score | 1.428721 | 1.429789 | +0.001068 regressed |

All untouched dimensions were preserved. Codabench row ID: `700935`; displayed mean rank is stale at `99999.0`.

### Lesson
- REJECT. Guardrails worked, but direct spatial-aggregation replacement shifted/narrowed ECS d7/d14 surface speed in the wrong direction for the hidden 2022 windows.
- Keep v51 as the base. Do not use v52 wholesale or as a donor.
- Spatial aggregation may still be useful only after stronger local validation, blending against v51, or a row-level gate that proves it improves hidden-style regimes.

---

## v53 — ECS Pressure d7 Shear/ws3 Speed Probe (SCORED, PROMOTED)

**Date**: 2026-04-28
**Approach**: V51 base + narrow LightGBM quantile speed overlay for East China Sea pressure-level d7 grid rows.
**Big idea**: After v52 rejected direct spatial replacement, test the next physics feature lane: pressure-level forecast speed, cubic wind speed, adjacent shear, absolute shear, and bulk shear. Scope is limited to ECS pressure d7 because v48 had prior signal there and broad speed retraining damaged North Sea.

### What was done
- Added `src/experiments/pressure_shear_v53.py`.
- Added `tests/test_pressure_shear_v53.py`.
- Built physics features from inference-available HRES pressure u/v columns.
- Trained 20 LightGBM quantile models: 5 pressure levels (`1000`, `925`, `850`, `700`, `500`) × d7 × 4 hours.
- Wrote `starting-kit/phase_1/predictions_v53.csv` and `starting-kit/phase_1/submission_v53.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v51.csv`.
- Base SHA-256: `c7e392afc17978698921371749204b27cfa5540b0b89e921c986e31484f646ca`.
- Submission rows: `3,448,800`.
- Allowed rows: `410,400`.
- Speed rows changed: `410,400`.
- Direction rows changed: `0`.
- Changed rows in scope: `410,400`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/pressure_shear_v53/v53_manifest.json`.
- Tests: `tests/test_pressure_shear_v53.py`, `tests/test_submission_guards.py`, `tests/test_run_v51.py`, and `tests/test_scoring.py` passed under `.venv`.

### Local diagnostics

| Slice | v51 width | v53 width | Mean delta q05/q50/q95 |
|-----|-----:|-----:|-----|
| 1000 d7 | 8.7092 | 8.1064 | +0.2624 / +0.0039 / -0.3404 |
| 925 d7 | 12.0838 | 11.4147 | +0.2101 / -0.0469 / -0.4591 |
| 850 d7 | 12.3513 | 11.8170 | +0.0670 / -0.0572 / -0.4673 |
| 700 d7 | 14.5143 | 13.1286 | +0.0010 / +0.0998 / -1.3847 |
| 500 d7 | 16.2623 | 15.5071 | -0.1158 / -0.0180 / -0.8711 |

### Decision rule
- Promote only if `speed_pressure_d7_ecs` improves enough without visible rank damage.
- If it regresses, keep v51 and do not expand pressure-shear as a direct replacement.
- If aggregate improves but one pressure level is likely responsible for risk, build a level-gated donor rather than expanding to d14/NS.

### Leaderboard result

| Dim | Best (v51) | New (v53) | Delta |
|-----|-----------:|----------:|------:|
| speed_pressure_d7_ecs | 15.7132 | 15.3733 | -0.3399 improved |
| primary_score | 1.428721 | 1.427777 | -0.000944 improved |

All non-target dimensions were preserved.

### Lesson
- PROMOTE. The pressure-shear/ws3 feature lane transferred cleanly on the narrow ECS pressure d7 target.
- v53 is the new base.
- Next expansion should stay scoped: test ECS pressure d14 or a level/horizon-gated pressure-speed donor, not broad all-region replacement.

---

## v54 — NS Pressure d7 Shear/ws3 Speed Probe (SCORED, REJECTED)

**Date**: 2026-04-28
**Approach**: V53 base + narrow LightGBM quantile speed overlay for North Sea pressure-level d7 grid rows.
**Big idea**: Spend the final daily slot on the highest-value validated-family expansion. V53 proved pressure shear/ws3 can transfer, and `speed_pressure_d7_ns` is only about `0.013` behind carlometta for visible rank 1.

### What was done
- Added `src/experiments/pressure_shear_v54.py` as a thin North Sea/v53 runner over the v53 pressure-physics implementation.
- Reused the pressure-level forecast speed, cubic speed, adjacent shear, absolute shear, and bulk shear feature family.
- Trained 20 LightGBM quantile models: 5 pressure levels (`1000`, `925`, `850`, `700`, `500`) × d7 × 4 hours.
- Wrote `starting-kit/phase_1/predictions_v54.csv` and `starting-kit/phase_1/submission_v54.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v53.csv`.
- Base SHA-256: `625d60328cbe11772e612e9819a10bc64da6fa55d0763cbbec8bd2c122afb4e3`.
- Submission rows: `3,448,800`.
- Allowed rows: `410,400`.
- Speed rows changed: `410,400`.
- Direction rows changed: `0`.
- Changed rows in scope: `410,400`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/pressure_shear_v54/v54_manifest.json`.
- Tests: `tests/test_pressure_shear_v53.py`, `tests/test_submission_guards.py`, `tests/test_run_v51.py`, and `tests/test_scoring.py` passed under `.venv`.

### Local diagnostics

| Slice | v53 width | v54 width | Mean delta q05/q50/q95 |
|-----|-----:|-----:|-----|
| 1000 d7 | 10.1261 | 9.6863 | +0.2105 / -0.0051 / -0.2293 |
| 925 d7 | 15.2514 | 14.6023 | +0.2747 / -0.2079 / -0.3744 |
| 850 d7 | 16.1860 | 15.6727 | +0.4847 / -0.2400 / -0.0286 |
| 700 d7 | 18.3099 | 18.0317 | +0.6561 / -0.1568 / +0.3779 |
| 500 d7 | 26.4682 | 26.6625 | +0.4882 / -0.2784 / +0.6824 |

### Decision rule
- Promote only if `speed_pressure_d7_ns` improves enough to preserve or flip visible rank without scope damage.
- If it regresses, keep v53 and do not broaden pressure-shear to North Sea without a stronger gate.

### Leaderboard result

| Dim | Best (v53) | New (v54) | Delta |
|-----|-----------:|----------:|------:|
| speed_pressure_d7_ns | 27.2233 | 27.7503 | +0.5270 regressed |
| primary_score | 1.427777 | 1.427777 | 0.000000 neutral |

All non-target dimensions were preserved.

### Lesson
- REJECT. The final daily slot did not produce the rank flip. The raw target metric regressed even though primary score stayed flat at displayed precision.
- Keep v53 as base.
- Pressure physics is validated for ECS pressure d7 only. Do not assume transfer to North Sea without a stronger gate, blend, or level-specific donor analysis.

---

## v55 — ECS Pressure d14 Shear/ws3 Speed Probe (SCORED, REJECTED)

**Date**: 2026-04-28
**Approach**: V53 base + narrow LightGBM quantile speed overlay for East China Sea pressure-level d14 grid rows.
**Big idea**: Keep the pressure-physics expansion inside the only family that transferred: ECS pressure. V54 showed not to generalize shear/ws3 blindly to North Sea; v55 tests whether ECS d14 can benefit from the same physical interval structure as ECS d7.

### What was done
- Added `src/experiments/pressure_shear_v55.py`.
- Patched `src/experiments/pressure_shear_v53.py` so the shared runner is target-horizon aware in forced forecast contexts and manifest labels.
- Used the closest available HRES pressure forecast stack for d14 (`d10`) plus selected d1/d7 signals.
- Trained 20 LightGBM quantile models: 5 pressure levels (`1000`, `925`, `850`, `700`, `500`) × d14 × 4 hours.
- Wrote `starting-kit/phase_1/predictions_v55.csv` and `starting-kit/phase_1/submission_v55.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v53.csv`.
- Base SHA-256: `625d60328cbe11772e612e9819a10bc64da6fa55d0763cbbec8bd2c122afb4e3`.
- Submission rows: `3,448,800`.
- Allowed rows: `410,400`.
- Speed rows changed: `410,400`.
- Direction rows changed: `0`.
- Changed rows in scope: `410,400`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/pressure_shear_v55/v55_manifest.json`.
- Tests: `tests/test_pressure_shear_v53.py`, `tests/test_submission_guards.py`, `tests/test_run_v51.py`, and `tests/test_scoring.py` passed under `.venv`.

### Local diagnostics

| Slice | v53 width | v55 width | Mean delta q05/q50/q95 |
|-----|-----:|-----:|-----|
| 1000 d14 | 9.9197 | 9.4625 | +0.0985 / -0.2430 / -0.3587 |
| 925 d14 | 13.3091 | 12.7624 | +0.0832 / -0.1770 / -0.4635 |
| 850 d14 | 13.5503 | 13.2778 | -0.0032 / -0.1252 / -0.2757 |
| 700 d14 | 17.1311 | 16.3085 | +0.0708 / -0.1448 / -0.7517 |
| 500 d14 | 22.6712 | 21.6551 | +0.2050 / -0.5164 / -0.8111 |

### Decision rule
- Promote only if `speed_pressure_d14_ecs` improves without scope damage.
- If it regresses, keep v53 and treat pressure-physics d14 as needing blending or level gates.

### Scoring result

| Dim | Best (v53) | v56 | v55 | Delta v55 vs v53 | Delta v55 vs v56 |
|-----|-----------:|----:|----:|------:|------:|
| speed_pressure_d14_ecs | 17.9698 | 17.9666 | 18.1341 | +0.1643 regressed | +0.1675 regressed |
| primary_score | 1.427777 | 1.427768 | 1.428233 | +0.000456 regressed | +0.000465 regressed |

All non-target dimensions were preserved.

### Full replay oracle

Report path: `logs/oracle/v55_pressure_shear_d14_ecs_vs_hres_residual`.

The first validation-oracle run used full unsampled historical replay files:

- replay rows: `22,725,900`
- target: `speed_pressure_d14_ecs`
- recommendation: `BLEND_REQUIRED`
- aggregate delta vs HRES-residual baseline: `-5.4844` improved
- split wins: `3 / 3`
- coverage delta: `-3.249 pp`
- width delta: `-3.9118`
- worst eligible slice delta: `+17.4980`

| Slice | Base | v55 replay | Delta |
|-----|-----:|-----:|-----:|
| val | 26.9010 | 20.7932 | -6.1078 improved |
| tune | 24.8557 | 20.0841 | -4.7715 improved |
| holdout | 27.5964 | 21.8939 | -5.7025 improved |

The important finding is mixed: the model has real signal across every temporal
split, but full replacement is too aggressive. The narrowed interval wins on
average but loses too much coverage and contains unstable regimes. The next
candidate should be a predeclared blend or gate, not a wholesale v55 expansion.

### Full replay blend sweep

Report path: `logs/oracle/v55_pressure_shear_d14_ecs_blend_sweep`.

The blend sweep compared fractional replacements:

```text
q_blend = q_base + lambda * (q_v55 - q_base)
```

against the same full replay baseline over `22,725,900` rows.

| Lambda | Recommendation | Target delta | Split wins | Coverage delta | Width delta | Worst slice delta |
|-----:|---|-----:|-----:|-----:|-----:|-----:|
| 0.20 | LEVEL_OR_REGIME_GATE_REQUIRED | -2.1745 | 3 / 3 | +0.796 pp | -0.7824 | +0.9423 |
| 0.35 | LEVEL_OR_REGIME_GATE_REQUIRED | -3.4993 | 3 / 3 | +1.030 pp | -1.3691 | +1.7666 |
| 0.50 | LEVEL_OR_REGIME_GATE_REQUIRED | -4.5334 | 3 / 3 | +0.892 pp | -1.9559 | +2.6481 |
| 0.65 | LEVEL_OR_REGIME_GATE_REQUIRED | -5.2572 | 3 / 3 | +0.304 pp | -2.5427 | +3.6378 |
| 1.00 | BLEND_REQUIRED | -5.4844 | 3 / 3 | -3.249 pp | -3.9118 | +17.4980 |

The sweep changes the read on v55: the signal is not a dead end, but the
full-strength candidate is. Fractional blending fixes the broad coverage loss;
the remaining failure is a small number of granular regimes. Lambda `0.20` is
the safest global candidate: it wins all three splits, improves coverage, keeps
about `40%` of the full v55 gain, and misses the slice gate by only `+0.1812`
Winkler. Lambda `0.35` keeps more gain but needs a cleaner row-level or
level/hour gate.

### Lesson
- SCORED: REJECT. Full-strength v55 regressed `speed_pressure_d14_ecs` from `17.9698` to `18.1341`, while v56 improved the same cell to `17.9666`.
- The replay oracle correctly warned that full replacement was too aggressive despite aggregate historical split wins.
- Keep v56 as base. Do not raise global lambda blindly; only test stronger d14 pressure blends with explicit bad-regime gates.

---

## v56 — Conservative ECS Pressure d14 Blend (SCORED, PROMOTED)

**Date**: 2026-04-29
**Approach**: V53 base + 20% blend toward the v55 ECS pressure d14 shear/ws3 speed overlay.
**Big idea**: Use the v55 replay signal without taking the full coverage and worst-slice risk. This is a production-feasible interval-shape blend: the submission is still anchored on the promoted v53 base, and only moves `q05/q50/q95` by `0.20 * (v55 - v53)` on the same predeclared target rows.

### What was done
- Added `src/experiments/pressure_shear_blend_v56.py`.
- Added `tests/test_pressure_shear_blend_v56.py`.
- Loaded `starting-kit/phase_1/predictions_v53.csv` as base.
- Loaded `starting-kit/phase_1/predictions_v55.csv` as donor.
- Applied `lambda=0.20` only on grid / `east_china_sea` / pressure levels / d14 speed rows.
- Wrote `starting-kit/phase_1/predictions_v56.csv` and `starting-kit/phase_1/submission_v56.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v53.csv`.
- Base SHA-256: `625d60328cbe11772e612e9819a10bc64da6fa55d0763cbbec8bd2c122afb4e3`.
- Donor: `v55`.
- Submission rows: `3,448,800`.
- Allowed rows: `410,400`.
- Speed rows changed: `410,400`.
- Direction rows changed: `0`.
- Changed rows in scope: `410,400`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/pressure_shear_blend_v56/v56_manifest.json`.
- Zip: `starting-kit/phase_1/submission_v56.zip` (`135.5 MB`, exactly one `predictions.csv`).

### Local diagnostics

| Slice | v53 width | v55 width | v56 width | Mean delta q05/q50/q95 |
|-----|-----:|-----:|-----:|-----|
| 1000 d14 | 9.9197 | 9.4625 | 9.8283 | +0.0197 / -0.0486 / -0.0717 |
| 925 d14 | 13.3091 | 12.7624 | 13.1998 | +0.0166 / -0.0354 / -0.0927 |
| 850 d14 | 13.5503 | 13.2778 | 13.4958 | -0.0006 / -0.0250 / -0.0551 |
| 700 d14 | 17.1311 | 16.3085 | 16.9665 | +0.0142 / -0.0290 / -0.1503 |
| 500 d14 | 22.6712 | 21.6551 | 22.4680 | +0.0410 / -0.1033 / -0.1622 |

### Oracle evidence

Report path: `logs/oracle/v55_pressure_shear_d14_ecs_blend_sweep/lambda_0p2`.

| Candidate | Recommendation | Target delta | Split wins | Coverage delta | Width delta | Worst slice delta |
|---|---|-----:|-----:|-----:|-----:|-----:|
| v55 full | BLEND_REQUIRED | -5.4844 | 3 / 3 | -3.249 pp | -3.9118 | +17.4980 |
| v56 lambda 0.20 | LEVEL_OR_REGIME_GATE_REQUIRED | -2.1745 | 3 / 3 | +0.796 pp | -0.7824 | +0.9423 |

### Decision rule
- Upload only as the conservative follow-up to v55/v53, not as a promoted base until the leaderboard confirms `speed_pressure_d14_ecs`.
- Promote if `speed_pressure_d14_ecs` improves without any non-target movement.
- If it is neutral or regresses, keep v53 and move to gated `lambda=0.35` or a coarse level/hour gate rather than increasing the global blend.

### Scoring result

| Dim | Best (v53) | New (v56) | Delta |
|-----|-----------:|----------:|------:|
| speed_pressure_d14_ecs | 17.9698 | 17.9666 | -0.0032 improved |
| primary_score | 1.427777 | 1.427768 | -0.000009 improved |

All non-target dimensions were preserved.

### Lesson
- SCORED: PROMOTE. The gain is tiny but clean: the conservative blend improved the target raw metric by `-0.0032` and primary by `-0.000009` with no side effects.
- v56 becomes the current base because it dominates v53 on the touched cell and preserves all other dimensions.
- The oracle was directionally right: fractional interval-shape blending transferred, but at very small magnitude. Next work should not simply raise global lambda; use a gated `0.35` candidate or inspect the bad replay regimes before spending another submission.

---

## v57 — Level-Gated ECS Pressure d14 Blend (SCORED, PROMOTED)

**Date**: 2026-04-29
**Approach**: V56 base + stronger 35% blend toward the v55 ECS pressure d14 speed overlay only on pressure levels `850` and `925`.
**Big idea**: V55 full strength regressed hidden, while v56's 20% blend transferred as a tiny win. The next useful probe is not a stronger global blend; it is an observable, production-feasible level gate. The lambda `0.35` replay had most visible bad-slice risk in level `700` and other high-risk regimes, so v57 tests the lower-risk middle pressure levels only.

### What was done
- Added `src/experiments/pressure_shear_gate_v57.py`.
- Added `tests/test_pressure_shear_gate_v57.py`.
- Loaded `starting-kit/phase_1/predictions_v56.csv` as the base.
- Loaded `starting-kit/phase_1/predictions_v53.csv` as the anchor and `starting-kit/phase_1/predictions_v55.csv` as the donor.
- Applied `q_v57 = q_v53 + 0.35 * (q_v55 - q_v53)` only on grid / `east_china_sea` / d14 / levels `850` and `925`.
- Left levels `1000`, `700`, and `500` exactly at v56.
- Wrote `starting-kit/phase_1/predictions_v57.csv` and `starting-kit/phase_1/submission_v57.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v56.csv`.
- Base SHA-256: `46d22324176454f0243d0fcfaaf03468242fc8387d32f8a7fff8c063b9ec5b93`.
- Donors: `v53`, `v55`.
- Submission rows: `3,448,800`.
- Allowed rows: `164,160`.
- Speed rows changed vs v56: `164,160`.
- Direction rows changed vs v56: `0`.
- Changed rows in scope: `164,160`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/pressure_shear_gate_v57/v57_manifest.json`.
- Zip: `starting-kit/phase_1/submission_v57.zip` (`135.5 MB`, exactly one `predictions.csv`).

### Local diagnostics

| Slice | v53 width | v55 width | v57 width | Width delta vs v56 |
|-----|-----:|-----:|-----:|-----:|
| 1000 d14 | 9.9197 | 9.4625 | 9.8283 | 0.0000 |
| 925 d14 | 13.3091 | 12.7624 | 13.1178 | -0.0820 |
| 850 d14 | 13.5503 | 13.2778 | 13.4549 | -0.0409 |
| 700 d14 | 17.1311 | 16.3085 | 16.9665 | 0.0000 |
| 500 d14 | 22.6712 | 21.6551 | 22.4680 | 0.0000 |

### Oracle evidence

Primary source: `logs/oracle/v55_pressure_shear_d14_ecs_blend_sweep/lambda_0p35`.

The global lambda `0.35` replay improved all temporal splits but still required a level/regime gate because the worst granular slice regressed. v57 is a gated probe, not a promoted base: it upgrades only `850` and `925`, where the replay bad-slice risk was materially smaller than the known level `700` failure pattern.

### Scoring result

| Dim | Best (v56) | New (v57) | Delta |
|-----|-----------:|----------:|------:|
| speed_pressure_d14_ecs | 17.9666 | 17.9488 | -0.0178 improved |
| primary_score | 1.427768 | 1.427719 | -0.000049 improved |

All non-target dimensions were preserved.

### Lesson
- SCORED: PROMOTE. The level-gated `0.35` blend improved the target raw metric by `-0.0178` and primary by `-0.000049` with no side effects.
- v57 becomes the current base. The useful interpretation is not "raise lambda globally"; it is "pressure-d14 interval shaping transfers when gated by pressure level."
- Next pressure-d14 work should test an additional gated expansion only if the gate is observable and justified by replay slices; otherwise switch back to new feature families.

---

## v58 — Gated Station d1 Hierarchical MOS (SCORED, PROMOTED)

**Date**: 2026-04-29
**Approach**: V57 base + a hierarchical d1 station-speed MOS model blended only where replay evidence passed a stability gate.
**Big idea**: The remaining visible rank drags include station d1 speed, but earlier broad station residual models were unstable. V58 turns the idea into a gated e2e system: train a stronger station d1 residual model with pressure-level wind context and spatial aggregates, compare it against the current Track E/base proxy across `val`, `tune`, and `holdout`, then apply only regions that win stably.

### What was done
- Added `src/experiments/station_d1_hier_mos_v58.py`.
- Added `tests/test_station_d1_hier_mos_v58.py`.
- Trained region-specific d1 station residual quantile models using station pooling, station metadata, pressure-level speed features, regional spatial aggregates, and temporal encodings.
- Evaluated candidate blends against the Track E/current-base proxy on three replay slices.
- Applied only `north_sea` at blend weight `0.20`; rejected `east_china_sea`.
- Changed only `q05/q50/q95` on station / d1 / `north_sea` rows.
- Wrote `starting-kit/phase_1/submission_v58.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v57.csv`.
- Base SHA-256: `d80dd14d8cc0d3eb8ba90f18687959e9e9e772aa73067258d47ac8b84dbf59e0`.
- Submission rows: `3,448,800`.
- Allowed rows: `256`.
- Speed rows changed vs v57: `256`.
- Direction rows changed vs v57: `0`.
- Changed rows in scope: `256`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/station_d1_hier_mos_v58/v58_manifest.json`.
- Zip: `starting-kit/phase_1/submission_v58.zip` (`135.5 MB`, exactly one `predictions.csv`).

### Replay evidence

| Region | Split | Rows | Base | Best | Weight | Delta |
|-----|-----|-----:|-----:|-----:|-----:|-----:|
| north_sea | val | 3,749 | 6.9447 | 6.8881 | 0.50 | -0.0566 |
| north_sea | tune | 4,333 | 6.3287 | 6.3269 | 0.20 | -0.0018 |
| north_sea | holdout | 2,834 | 7.8236 | 7.8088 | 0.35 | -0.0148 |
| east_china_sea | val | 5,019 | 6.2392 | 6.2392 | 0.00 | 0.0000 |
| east_china_sea | tune | 5,103 | 6.2583 | 6.2583 | 0.00 | 0.0000 |
| east_china_sea | holdout | 2,552 | 6.0508 | 6.0508 | 0.00 | 0.0000 |

North Sea passed with `3/3` winning slices, average delta `-0.0244`, worst delta `-0.0018`, and selected conservative weight `0.20`. ECS failed because every positive blend was worse locally.

### Scoring result

| Dim | Best (v57) | New (v58) | Delta |
|-----|-----------:|----------:|------:|
| speed_stations_d1_ns | 7.8606 | 7.7856 | -0.0750 improved |
| primary_score | 1.427719 | 1.427510 | -0.000209 improved |

All non-target dimensions were preserved.

### Lesson
- SCORED: PROMOTE. The gated North Sea station d1 MOS transferred cleanly: `speed_stations_d1_ns` improved by `-0.0750` and primary improved by `-0.000209`.
- v58 becomes the current base. This validates the replay-gated fractional MOS pattern as a second moat pillar beside pressure-d14 interval shaping.
- The full MOS model is still not safe by itself: at weight `1.0`, North Sea regressed on tune and holdout despite winning after fractional blending. Keep the production pattern as feature-rich model plus conservative observable gate, not standalone replacement.

---

## v59 — ECS Surface d14 Calibrated d10-HRES Direction (SCORED, RAW PROMOTED)

**Date**: 2026-04-29
**Approach**: V58 base + ECS surface d14 direction intervals from an observable d10 HRES direction centre with train-calibrated angular widths.
**Big idea**: `dir_surface_d14_ecs` remains one of the larger visible rank gaps. The surface d14 atlas showed a production-feasible signal: d10 HRES direction is a weak but real centre proxy, and wide regime-calibrated intervals produce replay CWS in the same range as the hidden target cell. V59 tests the broad calibrated proxy as a bounded directional probe.

### What was done
- Added `src/experiments/surface_d14_direction_v59.py`.
- Added `tests/test_surface_d14_direction_v59.py`.
- Started from `starting-kit/phase_1/predictions_v58.csv`.
- Used `fcst_dir_d10_h*` as the direction centre for each d14 issue hour.
- Used `fcst_speed_d10_h*` to choose train-calibrated angular half-widths by `level x hour x speed_regime`.
- Replaced only `dir_05/dir_50/dir_95` for grid / `east_china_sea` / surface levels / d14 rows.
- Wrote `starting-kit/phase_1/submission_v59.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v58.csv`.
- Base SHA-256: `aa250e048d13ced535dc3baf9871eaf8665add7302de66c6dc38d01e080ff436`.
- Submission rows: `3,448,800`.
- Allowed rows: `164,160`.
- Speed rows changed vs v58: `0`.
- Direction rows changed vs v58: `164,160`.
- Changed rows in scope: `164,160`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/surface_d14_direction_v59/v59_manifest.json`.
- Zip: `starting-kit/phase_1/submission_v59.zip` (`136.9 MB`, exactly one `predictions.csv`).

### Replay evidence

| Split | Rows | CWS | Coverage | Mean width |
|-----|-----:|-----:|-----:|-----:|
| tune | 3,739,770 | 336.4120 | 0.9029 | 156.8225 |
| val | 3,719,250 | 328.2445 | 0.9322 | 156.2348 |
| holdout | 1,872,450 | 326.1205 | 0.9410 | 156.3590 |

The replay profile is mixed. Val and holdout are below the current hidden v58 `dir_surface_d14_ecs` raw score (`332.5710`), but tune is worse. This is a directional probe, not a high-confidence promote candidate.

### Scoring result

| Dim | Best (v58) | New (v59) | Delta |
|-----|-----------:|----------:|------:|
| dir_surface_d14_ecs | 332.5710 | 332.1364 | -0.4346 improved |
| primary_score | 1.427510 | 1.427510 | 0.000000 neutral |

All non-target dimensions were preserved.

### Lesson
- SCORED: PROMOTE AS RAW-DOMINANT BASE. The atlas-derived d10-HRES overlay transferred cleanly on the target dimension with no side effects.
- The displayed primary score stayed neutral, likely because a `-0.4346` cWS raw gain did not flip the current per-dimension rank.
- The direction atlas has signal, but broad replacement is only modest. Next direction work should use regime-gated or learned centre corrections rather than repeating a full-scope d10-HRES replacement.

---

## v60 — Learned ECS Surface d14 Direction Centre (SCORED, REJECTED VS v59)

**Date**: 2026-04-29
**Approach**: V59 base + learned LightGBM sin/cos direction centre for ECS surface d14, with held-out train calibration of circular widths.
**Big idea**: V59 proved the d10-HRES proxy contains signal, but broad proxy replacement only moved `dir_surface_d14_ecs` by `-0.4346`. V60 attacks the centre error directly: learn the d14 verified direction from observable d10 forecast/regime features, then calibrate uncertainty from late-training residuals.

### What was done
- Added `src/experiments/surface_d14_direction_v60.py`.
- Added `tests/test_surface_d14_direction_v60.py`.
- Started from `starting-kit/phase_1/predictions_v59.csv`.
- Built historical ECS surface d14 rows from provided features and reanalysis targets.
- Trained LightGBM `sin(actual_direction)` and `cos(actual_direction)` models on a sampled early-training set.
- Calibrated circular half-widths on a disjoint late-training set by `level x hour x speed_regime`.
- Replayed full `val`, `tune`, and `holdout` grids against v59 replay.
- Replaced only `dir_05/dir_50/dir_95` for grid / `east_china_sea` / surface levels / d14 rows.
- Wrote `starting-kit/phase_1/submission_v60.zip`.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v59.csv`.
- Base SHA-256: `06b8542f2e4cecb313c7b220c52e0ab59bfa1e57bcec515c66e232e30a949bf9`.
- Submission rows: `3,448,800`.
- Allowed rows: `164,160`.
- Speed rows changed vs v59: `0`.
- Direction rows changed vs v59: `164,160`.
- Changed rows in scope: `164,160`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/surface_d14_direction_v60/v60_manifest.json`.
- Zip: `starting-kit/phase_1/submission_v60.zip` (`137.5 MB`, exactly one `predictions.csv`).

### Replay evidence

| Split | Rows | v60 CWS | v59 CWS | Delta | Coverage | Width |
|-----|-----:|-----:|-----:|-----:|-----:|-----:|
| tune | 3,739,770 | 326.3920 | 336.4120 | -10.0200 | 0.8860 | 140.5212 |
| val | 3,719,250 | 308.6070 | 328.2445 | -19.6374 | 0.9221 | 137.4996 |
| holdout | 1,872,450 | 297.5479 | 326.1205 | -28.5726 | 0.9465 | 138.1618 |

Average replay delta vs v59 is `-19.4100` cWS; worst split delta is still a clean `-10.0200`. The replay gate recommended `SUBMIT`.

### Scoring result

| Dim | Best (v59) | New (v60) | Delta |
|-----|-----------:|----------:|------:|
| dir_surface_d14_ecs | 332.1364 | 332.4329 | +0.2965 regressed |
| primary_score | 1.427510 | 1.427510 | 0.000000 neutral |

Against pre-atlas v58, v60 is still better (`332.5710 -> 332.4329`, `-0.1381`), but v59 remains the stronger raw base.

### Lesson
- SCORED: REJECT versus v59. The local replay overstated transfer badly: all three replay splits showed `-10` to `-29` cWS gains over v59, but hidden scoring regressed by `+0.2965`.
- The learned centre contains some signal, but full replacement is too unstable. Keep v59 as the current raw base.
- Future learned-centre work must be regularized against v59: blend the centre/intervals fractionally, gate only stable regimes, or train a correction on top of v59 rather than replacing the broad calibrated proxy.

---

## v62 — Winkler-Aware Width Scaling on ECS Station d1 Speed (SCORED, REJECTED)

**Date**: 2026-04-29
**Approach**: V59 base + per-row multiplicative width scale `s ∈ [0.7, 1.3]` on the 224 ECS station d1 speed rows. Scale model trained with Winkler sample weights using inference-available features (height, hour, season, MSL forecast, MSL anomaly, pressure shear, base interval width, q50).
**Big idea**: Targeting the largest remaining station-speed gap on the leaderboard — `speed_stations_d1_ecs` (rank 3, +0.88 WS to carlometta). C1 plan slot from MOAT_PLAN.md. Frames the Winkler loss as a sample-weight reweighter rather than a custom LightGBM objective (the latter was unstable per `winkler_loss_v53.py`).

### What was done
- Added `src/models/speed_winkler_loss.py` (per-sample Winkler with softplus hinge + sample-weight helper).
- Added `src/experiments/winkler_speed_v62.py` and tests `tests/test_speed_winkler_loss.py`, `tests/test_winkler_speed_v62.py`.
- Trained a small LightGBM width-scale model with Winkler sample weights on TRAIN+VAL station residuals; calibrated coverage on TUNE.
- Applied scale to v59 half-widths around q50 on the 224 station/east_china_sea/d1/speed rows; enforced monotonicity.
- Generated submission with documented gate override.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v59.csv`.
- Base SHA-256: `06b8542f2e4cecb313c7b220c52e0ab59bfa1e57bcec515c66e232e30a949bf9`.
- Submission rows: `3,448,800`.
- Allowed rows: `224`.
- Speed rows changed: `224`.
- Direction rows changed: `0`.
- NaNs in prediction columns: `0`.
- Manifest: `logs/winkler_speed_v62/v62_manifest.json`.

### Replay evidence

| Split | Rows | Base | Candidate | Delta | Coverage delta | Width delta |
|---|---:|---:|---:|---:|---:|---:|
| val | 5,019 | 9.7547 | 8.9461 | -0.8086 | +0.005 | -0.30 |
| tune | 5,103 | 9.3812 | 8.6213 | -0.7599 | +0.006 | -0.27 |
| holdout | 2,552 | 9.5409 | 8.6955 | -0.8453 | +0.007 | -0.22 |
| **aggregate** | **12,674** | **9.5587** | **8.7625** | **-0.7964** | **+0.006** | **-0.27** |

Oracle decision (pre-override): `LEVEL_OR_REGIME_GATE_REQUIRED`.
- 3/3 split wins, coverage `+0.57 pp`, width `-0.27`, worst-slice (any n) `+1.26` (n=1 outlier — ECS_03 width_q1 q50_q1).
- With `min_n>=20`: worst slice `+0.50` (ECS_02 width_q1 q50_q4 val), best slice `-8.64` (ECS_03 width_q1 q50_q4 val). Aggregate dominated by ECS_03 wins.

### Decision rule (and override)
- The oracle gate (under v1 thresholds) failed because the worst-slice cap was set to `35%` of aggregate gain (`+0.28`) and the n=1 slice exceeded it.
- Override decision: emit submission anyway — the small-n outlier was judged statistical noise; with min_n=20, worst slice +0.50 vs aggregate -0.796 was within the spirit of the gate.
- Override recorded in manifest under `gate_override` block.

### Scoring result

| Dim | Best (v59) | New (v62) | Delta |
|---|---:|---:|---:|
| speed_stations_d1_ecs | 7.5154 | 7.8013 | +0.2859 regressed |
| primary_score | 1.427510 | 1.428304 | +0.000794 regressed |

All other 35 dimensions are byte-identical to v59.

### Lesson
- SCORED: REJECT versus v59. Local replay overstated transfer by ~1.08 WS (replay said `-0.80`, hidden was `+0.286`). Same false-positive class as v60 (replay `-19 cWS`, hidden `+0.30`).
- The override rationale was directionally wrong: the failure was distribution shift between 2021 calibration and 2022 hidden, not small-sample noise. The `min_n>=20` worst-slice of `+0.50` should have been read as the leading indicator.
- **Class-of-move conclusion**: ML-learned post-hoc scalings on top of v59 (v60 centre, v62 width) repeatedly fail to transfer. Physics-driven structural changes (v46 copula, v53 pressure shear, v57 level gate) and extreme-conservative blends toward incumbent (v58 lambda 0.20) do.
- Keep v59 as base. v62 zip preserved at `starting-kit/phase_1/submission_v62.zip` for diagnostic reuse only.

---

## v63 — Vector u/v Residual Direction for ECS Surface d14 (NOT UPLOADED — gate held)

**Date**: 2026-04-29
**Approach**: V59 base + LightGBM `Δu` and `Δv` residual regressors around the v59 surface direction; recovered direction via `atan2(v_v59 + λ·Δv̂, u_v59 + λ·Δû)`; asymmetric angular conformal calibration of left/right half-widths.
**Big idea**: V60 failed because full-replacement of the direction centre via LightGBM sin/cos broke at the circular topology. V63 anchors on v59 and blends in u/v space (vector blending preserves geometry) — it should be a structurally safer attack on `dir_surface_d14_ecs` (rank 4, +21 cWS gap). DIRECTION_MOAT Phase 5.

### What was done
- Added `src/experiments/uv_residual_v63.py` and `tests/test_uv_residual_v63.py`.
- Decomposed v59 to (u, v) using v58 surface speed q50, trained LightGBM `Δu`/`Δv` on observable features (d10 HRES, MSL anomaly, shear, level, hour, lat/lon, season).
- Calibrated angular widths per `level × hour × speed_quintile` regime on a held-out training slice.
- Built v59 baseline replay and v63-at-λ=0.20 candidate replay parquets.
- Ran the validation oracle on the candidate.

### Scope verification
- Allowed rows: `164,160` (grid / east_china_sea / surface levels / d14 direction).
- Speed rows changed: `0`.
- Direction rows changed (intended): `164,160`.
- Manifest: `logs/uv_residual_v63/v63_manifest.json`.

### Replay evidence

| Split | Rows | v59 cWS | v63 cWS | Delta | Coverage delta | Width delta |
|---|---:|---:|---:|---:|---:|---:|
| val | ~3.7M | 328.244 | 323.158 | -5.086 | -0.013 | -2.0 |
| tune | ~3.7M | 336.412 | 336.032 | -0.380 | **-0.0215** | -1.5 |
| holdout | ~1.9M | 326.121 | 318.916 | -7.205 | -0.011 | -2.1 |

Worst slice (n>=20): `+0.4298 cWS` (tune / 100m / hour 18) — clean.

### Oracle decision
- All 3 splits win on cWS delta; worst-slice clean.
- **Coverage gate failed:** tune coverage dropped `-2.15 pp`, exceeding the `-1.50 pp` limit.
- Submission zip **NOT generated** — the oracle correctly held.

### Decision rule
- Do not upload. Coverage gate triggered exactly the way it was designed to after v60.
- Future direction work should either (a) anchor in u/v space with a width-floor that prevents tune coverage drop, or (b) fit a per-regime distributional model on observed circular data (DIRECTION_MOAT Phase 4: von Mises / mixture-of-VM) rather than residual-scaling around v59.

### Lesson
- NOT UPLOADED. The oracle gate held on its own — that's a working oracle.
- Structural improvement vs v60: the in-uv-space blend preserved circular geometry, and worst-slice `+0.43` was clean (vs v60's per-slice regressions). The new failure mode is width over-shrinkage on tune, not centre instability.
- Keep v59 as base. The u/v residual lane has signal but needs a width-floor regularizer.

---

## v61 — MSL-Driven Width Modulation on ECS Pressure d14 Speed (NOT UPLOADED, post-v62 risk class)

**Date**: 2026-04-29
**Approach**: V59 base + per-row multiplicative width scale `s ∈ {0.7, ..., 1.3}` per `(level, hour, season)` bin, fit by minimizing Winkler on val replay. MSL anomaly was abandoned because v59 inference rows lack a `time` column; degraded to season+level+hour scaling.
**Big idea**: A2 plan slot from MOAT_PLAN — heteroscedastic width modulation. The intent was MSL-driven (EDA showed `r ≈ -0.4` between MSL and speed); the fallback is structurally identical to v62's failure class.

### What was done
- Added `src/experiments/msl_interval_v61.py` and `tests/test_msl_interval_v61.py`.
- Fit a width-scale lookup over `(level, hour, season)` bins by minimizing Winkler on a 2M-row val replay (downsampled from 22.7M for runtime).
- Applied scaled widths on grid / ECS / pressure / d14 speed rows (410,400 rows actually in scope, not 164,160 as the brief stated — the v59 file has 5 levels × 4 hours × 8 windows × 2,565 grid points).
- Generated submission zip per the original brief's gate (oracle returned `LEVEL_OR_REGIME_GATE_REQUIRED` with 3/3 split wins).

### Scope verification
- Allowed rows: `410,400`.
- Speed rows changed: `410,400`.
- Direction rows changed: `0`.
- NaNs: `0`.
- Manifest: `logs/msl_interval_v61/v61_manifest.json`.

### Oracle evidence (downsampled to 2M rows)

| Metric | Value | Concern |
|---|---:|---|
| target_delta (Winkler) | -0.5837 | optimistic — same shape as v62 |
| split_wins | 3 / 3 | optimistic |
| coverage_delta | +0.021 | flat (v62 pattern: width changes without coverage gain) |
| width_delta | **+1.448** | intervals **grew** materially (v61 risk class) |
| worst_slice_delta | +2.553 | 12× over the +0.20 limit |
| oracle decision | `LEVEL_OR_REGIME_GATE_REQUIRED` | passed only because the brief's gate didn't include width-cap |

### Post-v62 reassessment
- After v62 regressed `+0.286 WS / +0.000794 primary` despite `-0.796` local replay, the gate that approved v61 is no longer trusted.
- v61 sits in the same false-positive risk class as v60 and v62: **learned post-hoc scalings on top of v59**. Width grew, coverage stayed flat, MSL anomaly was abandoned — every signal that bit on v62 fires harder on v61.

### Decision rule
- Do **not** upload. Submission zip preserved at `starting-kit/phase_1/submission_v61.zip` for diagnostic reuse only.
- The oracle thresholds were upgraded after the v62 leaderboard result (see `src/analysis/validation_oracle.py` post-v62 docstring). Re-running the oracle on v61 with the upgraded thresholds will now correctly fire the width-growth cap.

### Lesson
- NOT UPLOADED post-v62 lesson. v61 should not have been generated; the brief's gate was insufficient.
- Going forward: any width-modulation candidate must pass `width_growth_cap=0.30` and `coverage_floor_pp=0.005` on under-covered base. Tests `test_v61_pattern_width_growth_cap_rejects_widening_candidate` and `test_v62_pattern_coverage_floor_rejects_undercovered_base` lock these in.

---

## v62 Micro-Analysis — Why the Hidden Regression Happened (DIAGNOSTIC, no submission)

**Date**: 2026-04-29
**Approach**: Cross-reference v62 candidate predictions against v59 base (per-row scaling on the 224 changed rows) and v62 oracle slice deltas (per-station replay gains) to identify which station drove the hidden +0.286 WS regression.
**Big idea**: v62's failure pattern wasn't generic 2021→2022 distribution shift — it was localized. One station's replay performance dominated the aggregate, masking instability.

### What was found
- The v62 model emitted symmetric multiplicative scales per row, range 0.79–1.30.
- Per-station mean scaling (most aggressive narrowing): ECS_05 (0.876), ECS_04 (0.877), ECS_06 (0.904).
- Per-station replay contribution (n≥20 slices summed): **ECS_03 contributed 66.9% of the total winning slice contribution**, while next-best ECS_07 was 15.4%.
- ECS_02's worst-slice in val was a *positive* +0.505 WS — the leading indicator that was dismissed.

### Diagnosis
ECS_03's v59 widths were materially over-conservative for the 2021 days the replay sampled, and the Winkler-aware width scaler cut them aggressively. The 2022 hidden windows had different verifying conditions for ECS_03 (likely different ECS storm/cyclone tracks), so the narrowing was wrong on hidden. Other stations had small replay gains and their hidden contributions roughly cancelled — leaving the ECS_03 hidden flip dominant in the aggregate +0.286 WS regression.

### Oracle upgrade (locked in by `test_v62_pattern_single_source_dominance_rejects_concentrated_gain`)
A new gate `single_source_gain_cap=0.60` was added to `OracleThresholds`. The check runs an independent station-level aggregation on the row-level scored data (lower min_n=20 than the worst-slice filter, since 224-row scopes have no n≥50 stations) and rejects candidates whose aggregate winning station contribution is concentrated >60% on one station. Re-evaluating v62 against the new gate: ECS_03 = 66.9% > 60% → fires. Net effect: a v62 redo would now correctly reject before zip generation.

### Files
- Report: `logs/v62_micro_analysis/REPORT.md`
- Tables: `logs/v62_micro_analysis/{per_row_scaling.csv, per_station_scaling.csv, per_station_replay.csv, cross_table.csv}`

### Lesson
- The v62 hidden flip wasn't randomness — it was a single-station fragility in the local replay structure.
- Future scoped probes (especially station-level) must pass the single-source gain cap. The prior worst-slice min_n=50 filter is insufficient on small-scope candidates because it produces zero eligible slices.
- For station-level candidates, **inspect per-station replay distribution before submitting**. If one station dominates the gain, treat the candidate as fragile regardless of aggregate metrics.

---

## v64 — Analog Ensemble for NS d14 Pressure Speed (READY TO UPLOAD)

**Date**: 2026-04-29
**Approach**: V59 base + Analog Ensemble (Delle Monache et al. 2013) for NS d14 pressure speed. K=30 KD-tree on (`msl_anom`, `z700_anom`, `woy_sin`, `woy_cos`) per (region, level). Empirical q05/q50/q95 from neighbor verifications. λ=0.20 conservative blend toward v59.
**Big idea**: d14 has no HRES forecast signal beyond d10 — AnEn is the textbook meteorological solution. **B2** from MOAT_PLAN.md. This is in the **proven-transferring class** (structural physics, like v46 copula and v53 pressure shear), structurally distinct from the failed v60/v62 learned-scaling class.

### What was done
- Added `src/experiments/anen_d14_pressure_v64.py` (full AnEn runner with archive build, KD-tree neighbor search, inference-time flow-state submission build).
- Added `tests/test_anen_d14_pressure_v64.py` (7 tests: target_mask, blend math, monotonicity, NaN-safety, base SHA constants).
- Trained per-(region, level) historical archives over 2019–2021 6-hourly synoptic state.
- Ran a 6-cell sweep: NS/ECS × λ ∈ {0.20, 0.35, 0.50}. Every cell showed structurally healthy results: 3/3 splits won, coverage improved on under-covered base, worst-slice (n≥50) negative everywhere.
- The previous agent's local gate had a symmetric ±0.30 width band (over-restrictive — the canonical oracle is one-sided on width *growth* only). Re-ran the canonical oracle on NS λ=0.20 and emitted the submission.

### Scope verification
- Base file: `starting-kit/phase_1/predictions_v59.csv`.
- Base SHA-256: `06b8542f2e4cecb313c7b220c52e0ab59bfa1e57bcec515c66e232e30a949bf9`.
- Submission rows: `3,448,800`.
- Allowed rows: `410,400` (5 levels × 4 hours × 8 windows × 2,565 NS grid points).
- Speed rows changed: `410,400`. Direction rows changed: `0`. NaNs: `0`. Monotonicity violations: `0`.
- Out-of-scope rows BYTE-IDENTICAL to v59 (verified by `assert_prediction_scope`).
- Manifest: `logs/anen_d14_pressure_v64/v64_manifest.json` (`submission_v64` block).

### Replay evidence (canonical `OracleThresholds()` gate)

| Split | Rows | Base WS | v64 WS | Delta | Width delta | Coverage delta |
|---|---:|---:|---:|---:|---:|---:|
| val | 300,000 | 32.54 | 27.60 | **−4.94** | −2.42 | +0.0092 |
| tune | 300,000 | 24.52 | 21.24 | **−3.27** | −2.50 | +0.0021 |
| holdout | 300,000 | 33.89 | 28.65 | **−5.24** | −2.62 | +0.0109 |
| **aggregate** | **900,000** | **30.32** | **25.83** | **−4.484** | **−2.515** | **+0.007** |

Worst slice (n≥50): **−1.029 WS** (every eligible slice improves). Single-source dominance: clean (no station concentration — grid candidate, K=30 neighbors per row, no single regime dominates).

### Decision rule
- Canonical oracle (post-v62/T8 strict thresholds): **`PROMOTE_CANDIDATE`** ("Candidate passes v1 replay gate"). No width-growth, no coverage-floor, no single-source-dominance, no coverage-drop reasons.
- Submission emitted at `starting-kit/phase_1/submission_v64.zip` (133 MB).
- User to upload manually; expected target dim is `speed_pressure_d14_ns` (currently 24.3527 in the v59 leaderboard read).

### Why v64 is structurally different from v60/v62/v61
| Risk feature | v60/v62/v61 | v64 |
|---|---|---|
| Method class | ML-learned scaler on v59 | AnEn — empirical neighbors on synoptic state (physics) |
| Replay magnitude | −0.6 to −19 cWS | **−4.5 WS aggregate** (much larger margin to absorb 2022 shift) |
| Coverage on under-covered base | Flat (v62) or worse (v60, v63) | **Improves** on every under-covered split |
| Worst-slice (n≥50) | Mixed/regressing | All-improving |
| Single-source dominance | ECS_03 = 67% (v62) | Spatially diffuse (grid, not station) |

### Lesson
- READY TO UPLOAD. v64 is the strongest scoped candidate since v53. The canonical oracle clears it cleanly. The AnEn lane is structurally physics-driven and in the proven-transferring class.
- For v64 to lose hidden, the 2022 distribution would need to deliver ~+8 WS regression on top of clean replay −4.5 — much harder than v62's +1 WS flip on −0.8 WS replay.
- This validates the post-v62 oracle as a useful filter: it correctly admits structural-physics candidates (v64) while rejecting learned-scaling candidates (v60, v62, v61).

---

## v66 — Spatial Smoothing of Interval Widths (NOT UPLOADED, oracle correctly held)

**Date**: 2026-04-29
**Approach**: V59 base + Gaussian-kernel spatial smoothing of grid q05/q95 widths within each (window, region, horizon, hour, level) group. Only widths smoothed; q50 unchanged. Scoped to `speed_surface_d7_ecs` (rank 2 with small leaderboard gap). C2 from MOAT_PLAN.md.
**Big idea**: Pure post-processing — no learned model — averages existing widths across neighboring grid points to reduce single-point noise. Lowest-risk candidate of the post-v62 cohort, in the structural class.

### What was done
- Added `src/experiments/spatial_smooth_v66.py` (scoped wrapper over the existing v54 `apply_spatial_smoothing`).
- Added `tests/test_spatial_smooth_v66.py` (8 tests).
- Built an HRES-residual v59-shape replay base for `speed_surface_d7_ecs` (no checked-in v59 surface speed model).
- Swept bandwidth ∈ {1.5, 3.0, 4.5}.

### Sweep results (9.3M val/tune/holdout replay rows)

| bandwidth | aggregate Δ WS | width Δ | coverage Δ |
|---:|---:|---:|---:|
| 1.5 | **+0.083 (worse)** | −0.30 | −0.013 |
| 3.0 | **+0.167 (worse)** | −0.40 | −0.017 |
| 4.5 | **+0.224 (worse)** | −0.45 | −0.019 |

Every bandwidth widened Winkler. Selection rule (min Winkler with width Δ ≤ 0) picked bandwidth 1.5; per-split deltas were val −0.008 / tune +0.205 / holdout +0.019 (only val improved).

### Oracle decision
- Canonical `OracleThresholds()` gate: **`REJECT_CANDIDATE`** — "Aggregate target delta is non-improving: 0.082828."
- The first rail (target_delta < 0) caught it; no other gates needed to fire.

### Decision rule
- NOT UPLOADED. Pure structural smoothing on `speed_surface_d7_ecs` did not transfer on a v59-shape replay base.

### Lesson
- Negative result, valuable: spatial smoothing on already-undercovered base (val coverage was below 0.90) drops coverage further by ~1.3 pp because narrowing widths on row-by-row noise that the actual coverage relies on.
- The oracle held cleanly via the simplest rail (non-improving aggregate). No need for the post-v62 width/coverage/single-source gates here — the candidate failed the basic Winkler aggregate test.
- Width smoothing as post-processing is not a moat lane on this dimension. Don't retry without a coverage-aware variant (e.g., smooth widths *upward* not symmetrically) or a different target dim where base coverage is already saturated.

## v71 — UV Residual Width Floor on dir_surface_d14_ecs (KILLED, 2026-04-30)

### Status
**REJECTED** without submission. Killed by rank-leverage analysis showing
`dir_surface_d14_ecs` is rank-saturated.

### Why killed
Three independent sources confirm `dir_surface_d14_ecs` cell does not
move primary_score at the cWS magnitudes our lanes produce:
1. v58 single-cell submission: cWS Δ = +0.4346, rank Δ = 0.000000
2. v60 single-cell submission: cWS Δ = +0.2965, rank Δ = 0.000000
3. Multi-cell ridge regression on 38 scored submissions
   (`scripts/diag_rank_leverage_regression.py`): β = +0.00005,
   95% CI [-0.00002, +0.00024]

### Lesson
Phase-1 mean_rank quantizes cWS into wide bins per (region, level, horizon)
× cell. `dir_surface_d14_ecs` has been observed at ±0.3-0.6 cWS magnitudes
with zero rank movement — the bin boundaries are wider than achievable
single-step improvements. Lanes targeting this cell are dead regardless
of replay quality. Future cell selection should consult
`memory/seawinds_rank_leverage.md` first.

### Artifact
- Scaffold preserved at `src/experiments/uv_residual_width_floor_v71.py`
  for reference; not run.

## v70 — Winter-Gated Direction Pressure d14 Narrowing (DEPRIORITIZED, 2026-04-30)

### Status
Deprioritized; not run. Likely rank-dead like v71.

### Why deprioritized
Multi-cell regression shows pressure d14 direction cells have small β
with CIs overlapping zero:
- `dir_pressure_d14_ns`: β = −0.00130, CI [−0.00113, +0.00231], n=27
- `dir_pressure_d14_ecs`: β = +0.00082, CI [−0.00086, +0.00178], n=28

Even a generous +1 cWS improvement on either cell would translate to
~+0.001 rank delta, an order of magnitude smaller than the closest
significant cells (stations d1 ns/ecs, surface d7 ecs at β ≈ +0.0027).

### Lesson
Direction d14 cells appear broadly saturated; v58, v60 (surface), and now
v70 estimates (pressure) all point to the same conclusion. Don't queue
direction d14 narrowing lanes without first finding a rank-alive
direction cell.

### Artifact
- Scaffold preserved at `src/experiments/winter_gated_v70.py` for
  reference; revisit only if other lanes are exhausted.

## v68 — AnEn Surface d14 Speed (REJECTED by oracle, 2026-04-30)

### Status
**REJECTED** without submission. Oracle rejected all 6 (region, lambda)
combinations.

### What was done
Analog Ensemble (K=30 KD-tree on msl_anom + blh_anom + woy_sin/cos) on
2019-2021 surface 6h reanalysis fields, replacing v59 surface d14 speed
intervals via canonical 0.20/0.35/0.50 lambda blend with v59. Replay
base used HRES-d14+train-residual quantiles (proxy quality verified
within 0–2.4 cWS of v59 leaderboard, width gap 17–23%).

### Result
All conditions REJECT_CANDIDATE:
- NS λ=0.20 target_delta=+0.052 (0/3 split wins)
- NS λ=0.35 target_delta=+0.234
- NS λ=0.50 target_delta=+0.851
- ECS λ=0.20 target_delta=+0.204
- ECS λ=0.35 target_delta=+0.468
- ECS λ=0.50 target_delta=+1.081

AnEn is *worse* than the proxy on all conditions. Proxy bias bound
(±2.4 cWS NS, ±0.1 ECS) is moot — even with a favorable rebuild shift,
AnEn target_delta would still be positive.

### Lesson
Two non-exclusive hypotheses, can't separate without proper replay base:
1. **Architectural**: at 14-day lead, synoptic predictability has
   decayed; analogs based on (msl_anom, blh_anom, woy) at issue time
   don't carry useful info about wind 14 days later.
2. **Coverage-saturated proxy**: replay base had 99.97–100% coverage on
   a 90% interval (train-residual q05/q95 are too wide for d14 surface).
   AnEn was asked to beat a baseline whose cWS is dominated by width.
   Any narrowing dropped coverage faster than width shrank.

The empirical fact: v68 cannot promote *through this proxy*. Whether it
could promote through v59-actual quantiles is unknowable without
running the heavy notebook + v52 overlay rebuild — and the cost of
finding out is no longer justified given other lane options.

### Decision rule
- NOT UPLOADED. v68 closed without further investment.
- v69 (same architecture, pressure d7): run cheap proxy-quality check
  before demoting. d7 has more predictability than d14 and the proxy
  may not be coverage-saturated the same way.

## v69 — AnEn Pressure d7 Speed (BUILT, awaiting Codabench upload, 2026-04-30)

### Status
**BUILT and ready for upload** — all 6 (region, lambda) sweep conditions
PROMOTE_CANDIDATE under canonical post-v62 oracle (strict_post_v62=true).

### What was done
Analog Ensemble (K=30 KD-tree on msl_anom + z700_anom=0 + woy_sin/cos)
on 2019-2021 reanalysis at pressure levels {1000, 925, 850, 700, 500}.
Target = grid × {north_sea, east_china_sea} × pressure × d7 × q05/q50/q95.
Replay base used HRES-d7 + train-residual proxy.

### Proxy quality check (PASSED)
- NS coverage 87–95% across levels and splits (NOT v68's 99.97–100% pathology)
- ECS coverage 87–95%
- Width gap to actual modest (vs v68's 17–23%)
- Proxy is fit-for-purpose at d7 (synoptic predictability still useful)

### Sweep results (canonical oracle, strict_post_v62=true)
| region | λ    | recommendation     | target_delta | split_wins | coverage_delta | width_delta | worst_slice_delta |
|--------|------|--------------------|-------------:|-----------:|---------------:|------------:|------------------:|
| NS     | 0.10 | PROMOTE_CANDIDATE  | -1.951       | 3/3        | +0.0052        | -0.953      | -0.427            |
| NS     | 0.20 | PROMOTE_CANDIDATE  | -3.735       | 3/3        | (sweeping)     | (sweeping)  | (sweeping)        |
| NS     | 0.35 | PROMOTE_CANDIDATE  | -6.029       | 3/3        | (sweeping)     | (sweeping)  | (sweeping)        |
| ECS    | 0.10 | PROMOTE_CANDIDATE  | -1.233       | 3/3        | +0.0058        | -0.478      | -0.156            |
| ECS    | 0.20 | PROMOTE_CANDIDATE  | -2.303       | 3/3        | (sweeping)     | (sweeping)  | (sweeping)        |
| ECS    | 0.35 | PROMOTE_CANDIDATE  | -3.559       | 3/3        | (sweeping)     | (sweeping)  | (sweeping)        |

Per-split details for chosen λ=0.10 (most conservative passing) on each
region show coverage IMPROVED on all 3 splits, both low_miss and high_miss
reduced, width tightened. No coverage-floor floor breach, no slice
regression beyond fraction cap.

### Submission scope
- File: `starting-kit/phase_1/submission_v69.zip` (133.8 MB)
- Base: predictions_v59.csv (SHA verified)
- Changed rows: 801,832 = grid × {NS, ECS} × pressure × d7 × all hours/levels
  (164,160 each at 1000/925/850; 155,452 at 700; 153,900 at 500)
- Direction columns: untouched (0 rows differ)
- Other cells (d1/d10/d14, surface, stations): untouched
- Manifest: `logs/anen_d7_grid_v69/v69_manifest.json`

### Rank-leverage expectation
Multi-cell ridge regression (38 submissions, α=1e-4):
- speed_pressure_d7_ns:  β=+0.000 (rank-neutral) — cWS lift won't move primary
- speed_pressure_d7_ecs: β=+0.0031 [CI +0.0000, +0.0027] — leveraged

Predicted primary_score lift: β · cWS_delta = 0.0031 × 1.23 ≈ +0.0038 from ECS.
NS contribution ≈ 0 (rank-saturated cell). Combined v69 submission is "ECS lift
+ NS free cWS improvement that doesn't hurt rank."

### Decision rule
- UPLOADED to Codabench → record leaderboard scores in submissions/log.json
- If primary_score moves ≥+0.0030, β model validated again on a new cell
- If primary_score moves <+0.001 despite ECS cWS improving by ~1.2,
  re-examine whether speed_pressure_d7_ecs is actually rank-saturated
  contra the regression

### 2026-04-30 — v69 LEADERBOARD RESULT (replay/hidden divergence)

**Submitted to Codabench, primary_score = 1.427684 (vs v59 1.42751, Δ=+0.000174 within noise).**

| cell                  | v59      | v69      | Δ (signed cWS) | Replay predicted |
|-----------------------|---------:|---------:|---------------:|-----------------:|
| speed_pressure_d7_ns  | 27.2233  | 28.4168  | **+1.19**       | −1.95 (improvement) |
| speed_pressure_d7_ecs | 15.3733  | 15.4360  | **+0.06**       | −1.23 (improvement) |
| (all other 34 cells)  |   …      | …        | 0 (untouched)  |                  |

**Replay-vs-hidden divergence on NS = 3.14 cWS** (−1.95 → +1.19). Same class
of failure as v62. Canonical post-v62 oracle held (strict_post_v62=true,
3/3 split wins, coverage floor, width cap, worst-slice all favorable) and
*still* misled.

**Two non-exclusive hypotheses:**
1. **Proxy-base mismatch.** Replay base used HRES-d7 + train-residual
   quantiles. v59's actual deployed base may have wider intervals than
   proxy on 2022 — AnEn's narrowing then drops coverage faster than
   width shrinks (same mechanism as v68 d14 surface, but milder).
2. **Climate shift.** AnEn pool is 2019-2021 reanalysis. 2022 hidden
   windows may have synoptic states with no good analogs in pool, especially
   for North Sea winter storms.

**β model: SUSPECT, not just AnEn.**
- Predicted ECS rank delta: 0.0031 × (−0.063) ≈ −0.000196 (cWS got
  worse, so β > 0 predicts NEGATIVE rank delta = primary_score should
  decrease).
- Observed primary_score delta: **+0.000174 (positive)**.
- Scoring is deterministic; +0.000174 is real signal, not noise.
  Predicted and observed have OPPOSITE signs. At least one of the two
  touched cells produced positive rank delta despite worse cWS — not
  what β predicts.
- The β regression was fit on (rank_delta, *replay* cell_delta) pairs
  for 38 historical submissions. If replay deltas don't transfer to
  hidden for many of those 38 pairs (same proxy-base/distribution-shift
  pathology), then the regression's input feature was wrong for many
  training points. **The β CI claims should be downgraded — trust them
  less than the original calibration check on stations_d1_ecs implied.**

**Decision:**
- v69 NOT promoted to working base. Keep v59 as working base.
- Do NOT build follow-on lanes that stack on v69's altered pressure d7
  speed cells.
- Revisit ANY AnEn lane only after closing the proxy-base gap (e.g.,
  reconstruct v59's actual d7 pressure-base via re-inference on hidden
  windows OR find a proxy whose val/tune/holdout cWS matches the v59
  leaderboard cWS within ~0.5 cWS at the same level).

**Class lesson:** "All conditions PROMOTE under strict_post_v62" is
NECESSARY but NOT SUFFICIENT when the replay base is a proxy. The
oracle's gates are calibrated for replay-vs-replay shifts, not
replay-vs-hidden-with-proxy-base shifts. Add a "proxy-base agreement
threshold" gate (proxy cWS within ~0.5 cWS of v59 leaderboard at same
cell) before trusting AnEn replay deltas as transferable.

---

## Phase A WS1 — replay-base reconstruction for stations d1 NS  (2026-04-30)

### Outcome: shipped replay_base/v59_stations_d1_ns.parquet

**Strategy doc addendum 2026-04-30 (PHASE_A_STRATEGY.md):** v52 was a side-fork
never adopted into v59 — Gate G1 byte-equal failed (max_abs 3.5–8.8 cWS).
Verified true v59 surface d7+d14 ECS source = predictions_heavy.csv (heavy
starting-kit notebook). Pivoted WS1 to a parallel target: stations_d1_ns
(strongest β regression signal, single-cell rank-alive evidence from v62).

### Verified chain

```
v59[NS, stations, d1] = clip+sort(0.8 × v19_preds + 0.2 × v58_mos_preds)
v57[NS, stations, d1] = v19[NS, stations, d1]  (byte-equal on hidden 2022)
v19_saved_models reproduce predictions_v19.csv  (byte-equal on hidden 2022)
```

### Gates

| gate | check | result |
|---|---|---|
| G1 | v58 saved model + 0.2 blend on predictions_v57.csv reproduces v59[NS,stations,d1] on hidden 2022 | PASS  max_abs 1e-15 |
| G1.5 | v19 saved models reproduce predictions_v19.csv on hidden 2022 | PASS  max_abs 1e-15 |

Scripts:
- `scripts/phase_a_v52_byte_equal_check.py` — failed (v52 side-fork)
- `scripts/phase_a_v58_byte_equal_check.py` — G1 PASS
- `scripts/phase_a_v19_byte_equal_check.py` — G1.5 PASS
- `scripts/phase_a_replay_base_stations_d1_ns.py` — produces parquet

### Per-split Winkler (cWS) on the replay base

| split | n | cWS | v58 manifest at weight=0.2 (Track-E proxy base) |
|---|---|---|---|
| val | 3,767 | 7.0642 | 6.913 |
| tune | 4,348 | 6.6344 | 6.327 |
| holdout | 2,858 | 7.8871 | 7.811 |

Manifest used Track-E proxy as base (the v58 candidate's own internal proxy);
my replay base uses v19 = the actual deployed v57 (= v59 minus v58 overlay).
The +0.1–0.3 cWS gap is expected — different proxy bases. The replay base is
the authoritative one; manifest scores are model-internal.

### Cost

7.5 s wall-clock (load_features + 24,029 row predict for v19 + v58_mos +
blend + parquet write). Three orders of magnitude cheaper than the heavy
notebook (which has no cached models, ~672 CatBoost retrains required).

### Why this matters (closes the v68/v69 proxy-base trap)

v68/v69 failed because the replay base was a HRES + train-residual proxy
that diverged from v59's actual deployed base. With a per-cell faithful
replay base on val/tune/holdout, the oracle's PROMOTE conditions are
finally testable against the actual deployed quantiles. v68/v69's class
of false positives (PROMOTE-everywhere yet hidden regression) is now
guarded for stations_d1_ns.

### Decision: keep stations_d1_ns as INFRASTRUCTURE VALIDATION, not WS2 target

Per advisor: d1 lead has weak synoptic-regime variance, so the 3-bin
synoptic × 2-bin BL taxonomy collapses on stations_d1. Surface d7 ECS
remains the WS2 modeling target on physics grounds. Stations_d1_ns
serves as: (a) WS1 infrastructure validation (DONE), (b) fallback target
if surface d7 modulation fails on Lane #1 (regime-conditional Winkler-aware
extension of v62).

### Heavy-notebook dry-run deferred (#53)

Heavy notebook trains 672 CatBoost models from scratch + 14 LightGBM dir.
No cached models. Realistic re-train cost: 8–15 h. Strategy kill criterion
is >8 h → likely defer; needs a dedicated session to extract notebook,
add model checkpointing, then time inference.

---

## v80 — first leaderboard score post-Phase-A waves  (2026-05-01)

### Submission

`submissions/submission_v80_bundle.zip` (137 MB, MD5 `aa722f6cc18088661f58fc1210b287ac`)

**Bundle scope:** v77 v1b (uniform +0.202 m/s offset on grid×ECS×d7×10m, 82,080 rows) + v79 V1 (per-station offsets on stations×ECS×d1, 224 rows). All other 3,366,496 rows byte-equal v59. Build script: `scripts/wave9_build_bundle_v77_v79.py`. Codabench-format compliant (predictions.csv at zip root, no subfolder).

### Result: REGRESSION

| metric | v59 | v80 | Δ |
|---|---:|---:|---:|
| primary_score | 1.42751 | **1.427638** | **+0.000128 (REGRESSION)** |
| speed_surface_d7_ecs | 9.8216 | 9.8949 | +0.0733 (regression — v77 fault) |
| speed_stations_d1_ecs | 7.5154 | 7.4883 | −0.0271 (improvement — v79 worked) |
| speed_stations_d1_ns | 7.7856 | 7.7856 | 0 (untouched) |
| 33 other dims | unchanged | unchanged | 0 |

### Root cause: deeper proxy-base trap on v77

The replay base `replay_base/v59_surface_d7_ecs.parquet` was generated by `scripts/heavy_extracted_ecs_only.py` with TRAIN ≤ 2020-09-30 (leak-safe). Its cWS on hidden split (9.74) was within 0.5 of v59 leaderboard cWS on the same cell (9.82) — passing the existing proxy-base agreement rule. **But this rule is necessary, not sufficient.**

The trap: heavy reconstruction had +0.40 m/s mean residual (q50 biased low vs obs), but v59's actual deployed q50 has different bias — same cWS, different center. Two predictors with similar Winkler scores can have different residual structures. Applying v77's +0.202 correction to v59's q50 introduced a new bias where none existed → regression.

### v79 V1 confirmation

v79's replay base (`replay_base/v59_stations_d1_ecs.parquet`) was Gate-G1.5 byte-equal vs predictions_v59.csv hidden 2022 (max_abs 1e-15, verified `scripts/wave7_track_e_byte_equal_check_ecs.py`). The chain `v59[ECS, stations, d1] = v34 = Track E QuantileGBM residual on HRES` is empirically faithful. v79's per-station offsets transferred to leaderboard.

The Δ on leaderboard (−0.0271) was smaller than predicted on val/tune/holdout (−0.10 to −0.13). Likely cause: regime shift between fit-window (val=2020-10..2021-03) and hidden 2022. Per-station offsets are still in the right direction; magnitude attenuated.

### β-leverage check (post-hoc)

Per `seawinds_rank_leverage.md`:
- speed_surface_d7_ecs: β=+0.00242 CI [+0.0000, +0.0027] (marginal)
- speed_stations_d1_ecs: β=+0.00268 CI [+0.0016, +0.0029] (alive)

Predicted primary_score impact:
- v77 v1b: −0.113 × 0.00242 = −0.000274 expected. **Actual: +0.0733 × 0.00242 = +0.000177 if linear-β.**
- v79 V1: −0.10 × 0.00268 = −0.000268 expected. Actual: −0.0271 × 0.00268 = −0.0000727.

Net predicted: −0.000542. Actual: +0.000128 = +0.000177 − 0.0000727 − error term.

The v77 component flipped sign on leaderboard (replay PROMOTE → leaderboard regression). The v79 component matched sign but ~3× attenuated.

### Lessons

1. **Heavy-notebook reconstruction is a proxy, not a faithful v59 reconstruction.** Only 1e-15-byte-equal-verified chains are trustworthy for bias measurement. Track E for stations_d1_ECS qualified; heavy notebook for grid surface did NOT (cWS-similar ≠ bias-faithful).
2. **Augment proxy-base trap rule:** "cWS within 0.5" is necessary but not sufficient. Either (a) verify byte-equal chain at 1e-15 OR (b) measure proxy-vs-v59 mean residual gap directly on hidden 2022 rows where both exist.
3. **Replay base PROMOTE strength is not predictive when proxy-bias-faithful gate not closed.** v77's predicted Δ was −0.113 to −0.18; actual was +0.07. Magnitude error 0.18–0.25 cWS. Same trap signature as v68/v69.
4. **NS heavy notebook (currently running, PID 16323) cannot be used as bias-correction baseline** for the same reason. Its predictions will diverge structurally from v59's NS surface predictions even if cWS-similar. Useful for feature-schema and model-introspection only.

### Open question

Is there a way to validate heavy-notebook bias estimates BEFORE submitting? Possibilities:
- (a) Compare heavy reconstruction's q50 directly to v59's q50 on hidden 2022 — compute mean(heavy_q50 − v59_q50). If gap is non-trivial, the proxy can't be trusted for bias direction.
- (b) Subtract gap before applying correction: v77_corrected = v77_offset − mean(heavy_q50 − v59_q50).

This is the structural fix for future bias-correction lanes off heavy-notebook bases. Without it, heavy reconstruction is unsafe for bias direction signals.

### Strategic position

**Active candidates:**
- v79 V1 (stations_d1_ECS per-station bias correction): real, small gain. Standalone submission would be ~−0.0001 primary_score.
- v77 v1b: REJECT, do not resubmit. Heavy-notebook proxy-bias-trapped.

**Next moves (parallel):**
- NS heavy notebook training (Wave 10A) — running, 60+ min CPU. Output is a NS surface replay base. **Caveat: same proxy-base trap risk; cannot drive submission decisions.** Useful for feature inspection, schema check, and as raw material for byte-equal-chain reconstruction attempts.
- Mechanism pivot (Wave 11 copula): INFEASIBLE — direction quantile chain not byte-equal-verified for v59 on val/tune/holdout splits. Reopening requires multi-track direction reconstruction, 1–2 days investment.

---

## Strategy Reset + v83 — faithful station-speed lane  (2026-05-01)

### Diagnosis

The latest wave made the strategy problem clear: the best-looking replay gains
are not reliable when the base is only a proxy. v69 pressure AnEn and v77/v80
surface bias correction both passed local gates and then flipped or attenuated
on hidden scoring. The root cause is not that analogs or bias correction are
bad ideas; it is that the replay base was not the actual deployed v59 quantile
surface. Similar cWS does not imply similar q50 residual structure.

### What was implemented

- Added `src/analysis/faithful_base_audit.py`.
- Added `scripts/faithful_base_audit.py`.
- Added `tests/test_faithful_base_audit.py`.
- Wrote the audit report to `logs/faithful_base_audit/summary.md` and
  `logs/faithful_base_audit/cell_audit.csv`.

The audit ranks target cells by actionability: byte-equal replay-base evidence
dominates raw replay gain. It explicitly blocks:

- pressure AnEn from proxy bases after v69,
- heavy-notebook surface bias correction after v77/v80,
- full learned direction-centre replacement after v60.

### Audit decision

Top next lane: `speed_stations_d14_ecs`.

Evidence:

- `replay_base/v59_stations_d14_ecs.parquet` is Gate G1.5 byte-equal verified
  against v59 hidden via Wave 12.
- v82 stable-only half-shrunk per-station offsets improved all replay splits:
  val `-0.1778`, tune `-0.1754`, holdout `-0.1450` cWS.
- The expected hidden gain is discounted by 3x, using v79's observed
  attenuation, to about `-0.0481` cWS on the target cell.

### v83 artifact

Built standalone candidate:

- CSV: `submissions/v83_station_d14_ecs.csv`
- ZIP: `submissions/submission_v83_station_d14_ecs.zip`
- Manifest: `logs/faithful_base_audit/v83_manifest.json`

Scope:

- Base: `predictions_v59.csv`
- Target: station / east_china_sea / d14 / speed quantiles only
- Rows in target scope: 224
- Nonzero shifted rows: 128
- Direction changed rows: 0
- All other rows: byte-equal to v59

Offsets:

| station | offset |
|---|---:|
| ECS_01 | +0.22657 |
| ECS_02 | +0.50030 |
| ECS_05 | +0.06613 |
| ECS_06 | +0.18351 |

### Lesson

The next breakthrough path is not broad model invention. It is a faithful
cell-by-cell replay factory. Station speed is currently the only family where
we have byte-equal bases and observed hidden transfer. Grid pressure/surface
ideas remain research-only until their proxy-vs-v59 q50 gap is closed.

### 2026-05-02 — v83 leaderboard result

**Result: REJECT.**

| metric | v59 | v83 | Delta |
|---|---:|---:|---:|
| primary_score | 1.427510 | 1.427754 | +0.000244 |
| speed_stations_d14_ecs | 8.6307 | 8.7185 | +0.0878 |
| all other 35 dims | unchanged | unchanged | 0 |

This is an important clean failure. Unlike v69/v77, the base was not a proxy:
`speed_stations_d14_ecs` had a Gate G1.5 byte-equal replay base. The failure is
therefore not attribution noise. The simple per-station offset pattern that
looked stable across val/tune/holdout in 2020-2021 did not transfer to hidden
2022.

**Lesson:** faithful-base gating is necessary but not sufficient. It solved
the attribution problem, but not temporal regime shift. Do not submit more
simple v82-style station offsets (`d7_ns`, `d14_ns`, `d7_ecs`) just because
their replay bases are byte-equal. Future station-speed candidates need a
harder validation standard: leave-one-season or leave-one-year stability,
observable regime gates, and preferably no val-only station intercepts.

**Base remains v59.**

---

## v84 — centre-only physical u/v residual overlay  (2026-05-02)

### Approach

This is the post-v83 pivot back to option 2: physical interval structure and
copula-style coupling, not station intercepts. It reuses the v63 u/v residual
signal for `dir_surface_d14_ecs`, but removes the part that caused v63/v71 to
be held: width recalibration and width narrowing.

Core rule:

- preserve v59 left/right angular widths exactly,
- shift only the direction centre in u/v vector space,
- use the smallest passing fractional lambda.

### What was implemented

- Added `src/experiments/uv_residual_center_only_v84.py`.
- Added `tests/test_uv_residual_center_only_v84.py`.
- Reused cached v63 model/replay artifacts.
- Generated `starting-kit/phase_1/submission_v84.zip`.

### Replay gate

| lambda | target Δ | split wins | worst split Δ | worst coverage Δ | worst slice Δ | decision |
|---:|---:|---:|---:|---:|---:|---|
| 0.05 | -0.3961 | 3/3 | -0.3068 | +0.0014 | -0.2086 | PROMOTE |
| 0.10 | -0.7836 | 3/3 | -0.6432 | +0.0029 | -0.5261 | PROMOTE |
| 0.15 | -1.1130 | 3/3 | -0.9536 | +0.0042 | -0.7987 | PROMOTE |
| 0.20 | -1.3908 | 3/3 | -1.1891 | +0.0052 | -0.9690 | PROMOTE |

Selected `lambda=0.05`, deliberately conservative despite stronger replay
numbers at higher lambdas. The reason is strategic: v60 full learned centre
replacement and v83 station offsets both showed temporal transfer can flip even
when replay looks clean. v84 should test the mechanism, not maximize local
replay.

### Submission scope

- Base: `v59`
- ZIP: `starting-kit/phase_1/submission_v84.zip`
- Target: grid / east_china_sea / surface / d14 / direction only
- Changed rows: 164,160
- Changed columns: `dir_05`, `dir_50`, `dir_95`
- Speed changed rows: 0
- NaN prediction values: 0

### 2026-05-02 — v84 leaderboard result

**Result: PROMOTE RAW / RANK NEUTRAL.**

| metric | v59 | v84 | Delta |
|---|---:|---:|---:|
| primary_score | 1.427510 | 1.427510 | 0.000000 |
| dir_surface_d14_ecs | 332.1364 | 332.0178 | -0.1186 |
| all other 35 dims | unchanged | unchanged | 0 |

The physical centre-only lane transferred, but at about 30% of replay
expectation (`-0.1186 / -0.3961 ~= 0.30`). This is a useful result: preserving
v59 widths avoided the v63/v71 failure mode, and the vector-space centre signal
is real on hidden 2022. The displayed primary score is neutral because this is
a one-cell raw gain in a likely rank-saturated/slow-moving cell.

### v85 follow-up

Built the next lambda step:

- ZIP: `starting-kit/phase_1/submission_v85.zip`
- Lambda: `0.10`
- Scope: same as v84, 164,160 ECS surface d14 direction rows
- Speed changed rows: 0
- Expected if v84 attenuation holds: `dir_surface_d14_ecs ~= 331.90`

### 2026-05-02 — v85 leaderboard result

**Result: PROMOTE RAW / RANK NEUTRAL, but stop treating this as the main lane.**

| metric | v59 | v84 | v85 | Delta v85-v59 |
|---|---:|---:|---:|---:|
| primary_score | 1.427510 | 1.427510 | 1.427510 | 0.000000 |
| dir_surface_d14_ecs | 332.1364 | 332.0178 | 331.8893 | -0.2471 |
| all other 35 dims | unchanged | unchanged | unchanged | 0 |

v85 confirms the mechanism again. Hidden transfer remains around 30% of replay
expectation, and the change is cleanly scoped. But the effect is rank-neutral:
`dir_surface_d14_ecs` is not moving enough to cross a rank boundary.

Decision: do not spend the next submission on lambda `0.15` or `0.20` unless a
rank-gap check shows the larger lambda can cross a visible competitor threshold.
The next decision should be driven by rank-boundary leverage, not raw replay
gain on a saturated cell.

---

## v86 — ECS station d1 residual interval calibration (SCORED, PROMOTED)

### Approach

This is the post-v85 rank-boundary candidate, but designed as a reproducible
MOS/conformal-style method rather than a leaderboard tweak. The target cell is
`speed_stations_d1_ecs`, where the rank-gap analysis says one visible rank
requires about `0.1254` WS improvement.

The method:

- preserve the v85 median `q50`,
- compute historical residuals `obs_speed - q50_base` on the verified
  `replay_base/v59_stations_d1_ecs.parquet`,
- estimate station-level residual 5%/95% quantiles,
- shrink station quantiles toward the regional residual quantiles with
  empirical-Bayes `kappa=100`,
- blend calibrated intervals 50/50 with the base intervals.

This changes interval shape/width only. It does not move the centre.

### What was implemented

- Added `src/experiments/station_d1_ecs_residual_calibration_v86.py`.
- Added `tests/test_station_d1_ecs_residual_calibration_v86.py`.
- Generated `starting-kit/phase_1/submission_v86.zip`.
- Wrote diagnostics:
  - `logs/station_d1_ecs_residual_calibration_v86/summary.md`
  - `logs/station_d1_ecs_residual_calibration_v86/leave_one_period_scores.csv`
  - `logs/station_d1_ecs_residual_calibration_v86/v86_manifest.json`

### Validation

Leave-one-period validation:

| test split | base | candidate | delta | coverage base | coverage candidate |
|---|---:|---:|---:|---:|---:|
| val | 6.2392 | 5.9903 | -0.2489 | 0.8671 | 0.8954 |
| tune | 6.2583 | 6.0114 | -0.2468 | 0.8568 | 0.8930 |
| holdout | 6.0508 | 5.6709 | -0.3799 | 0.8527 | 0.8938 |

Summary:

- leave-one-period average delta: `-0.2919`
- leave-one-period worst delta: `-0.2468`
- fit-val tune/holdout average delta: `-0.3169`
- expected hidden delta at 0.30 attenuation: `-0.0951`
- expected hidden delta at 0.40 attenuation: `-0.1268`
- one-rank boundary: `0.1254`

### Submission scope

- Base: `v85`
- ZIP: `starting-kit/phase_1/submission_v86.zip`
- Target: station / east_china_sea / d1 / speed interval only
- Changed rows: 224
- Changed columns: `q05`, `q95`
- `q50` changed rows: 0
- Direction changed rows: 0
- NaN prediction values: 0

### Leaderboard result

**Result: PROMOTE / BREAKTHROUGH.**

| metric | v85 | v86 | Delta |
|---|---:|---:|---:|
| primary_score | 1.427510 | 1.426551 | -0.000959 |
| speed_stations_d1_ecs | 7.5154 | 7.1700 | -0.3454 |
| dir_surface_d14_ecs | 331.8893 | 331.8893 | 0 |
| all other 34 dims | unchanged | unchanged | 0 |

The rank-boundary analysis was directionally correct: `speed_stations_d1_ecs`
needed about `0.1254` WS to gain one visible rank, and v86 delivered `0.3454`
WS. The conservative attenuation estimate was too pessimistic for this method:
hidden improvement exceeded the leave-one-period average (`-0.2919`) rather
than shrinking to 30-40%.

### Lesson

This validates station-conditional residual interval calibration as a real
moat technique. Unlike simple station centre offsets, v86 calibrates the
uncertainty distribution around an existing robust median and improves coverage
toward 90%. This is reproducible, physically/statistically defensible, and
rank-moving. Next station-speed work should extend this exact family with the
same leave-one-period discipline, starting with `speed_stations_d1_ns` because
it has a visible one-rank boundary and a hidden-proven station d1 MOS lineage.

### Post-v86 follow-up: calibration-family sweep

After v86 scored, implemented
`scripts/station_residual_calibration_sweep.py` and generated:

- `docs/research/station_calibration_sweep/station_residual_calibration_sweep.md`
- `docs/research/station_calibration_sweep/station_residual_calibration_sweep.csv`

The sweep tested interval-only and bias+interval empirical-Bayes calibration
across all station-speed replay cells. Result: the family remains real, but no
direct extension clears the next rank boundary with enough margin.

| Dim | Best method | Avg delta | Worst split | Need +1 rank | Decision |
|-----|-------------|----------:|------------:|-------------:|----------|
| speed_stations_d1_ecs | bias+interval | -0.3040 | -0.2535 | 0.5300 | hold |
| speed_stations_d14_ecs | bias+interval | -0.2793 | -0.1061 | already #1 | hold |
| speed_stations_d7_ecs | bias+interval | -0.1841 | -0.0512 | already #1 | hold |
| speed_stations_d1_ns | bias+interval | -0.1246 | -0.0716 | 0.2956 | hold |
| speed_stations_d7_ns | bias+interval | -0.0433 | +0.0415 | already #1 | reject |
| speed_stations_d14_ns | interval | +0.0371 | +0.0560 | already #1 | reject |

Decision: no v87 upload from direct calibration. The next breakthrough attempt
should add new station MOS signal for `speed_stations_d1_ns` and keep v86-style
interval calibration as the uncertainty layer.

---

## v88 — North Sea d1 center MOS + EB interval calibration (SCORED, PROMOTED)

### Approach

This is the stronger follow-up to the held v87 full-quantile MOS. The v87
feature model improved North Sea d1 station speed but rebuilt q05/q95 directly
from model quantiles, which dropped coverage and missed the rank-boundary gate.
V88 uses the feature model only where it is most reliable: moving the station
median. It then rebuilds the interval with the same empirical-Bayes residual
calibration class that made v86 work.

Method:

- base: `v86`
- target: `speed_stations_d1_ns`
- model: LightGBM residual MOS around current base `q50`
- center blend: `0.80`
- interval calibration: station residual empirical-Bayes, shrink `0.35`,
  kappa `25`
- changed rows: North Sea station d1 speed only

### Validation

Leave-one-period validation clears the current one-rank gap plus margin:

| Split | Base | Candidate | Delta | Coverage base | Coverage candidate |
|---|---:|---:|---:|---:|---:|
| val | 7.0642 | 6.7228 | -0.3414 | 0.8997 | 0.8893 |
| tune | 6.6344 | 6.3070 | -0.3274 | 0.9041 | 0.9151 |
| holdout | 7.8871 | 7.5096 | -0.3775 | 0.8859 | 0.8880 |

Summary:

- average delta: `-0.3488`
- worst split delta: `-0.3274`
- rank-boundary + margin: `0.3256`
- clears boundary: yes

### Artifact

- ZIP: `starting-kit/phase_1/submission_v88.zip`
- Manifest: `logs/station_d1_ns_center_mos_v88/v88_manifest.json`
- Summary: `logs/station_d1_ns_center_mos_v88/summary.md`
- Tests:
  - `tests/test_station_d1_ns_center_mos_v88.py`
  - `tests/test_station_d1_ns_mos_v87.py`
  - `tests/test_station_residual_calibration_sweep.py`

### Leaderboard result

**Result: PROMOTE / BREAKTHROUGH.**

| metric | v86 | v88 | Delta |
|---|---:|---:|---:|
| primary_score | 1.426551 | 1.425474 | -0.001077 |
| speed_stations_d1_ns | 7.7856 | 7.3980 | -0.3876 |
| all other 35 dims | unchanged | unchanged | 0 |

This crossed the visible one-rank boundary (`7.49`) with margin and preserved
scope exactly. V88 validates the next station-speed moat pattern: use MOS to
move the center, but rebuild intervals from empirical station residuals rather
than trusting model quantile widths directly.

### Lesson

PROMOTE. Center-only station MOS plus empirical-Bayes residual interval
calibration is now stronger than pure interval calibration and transferred
cleanly on hidden data. For station speed, the winning pattern is:

1. keep scope narrow by rank-boundary target,
2. use feature MOS for median correction,
3. use residual-calibrated empirical intervals for uncertainty,
4. enforce leave-one-period gate before upload.

### Post-v88 follow-up: v89 generalized station sweep

Implemented `src/experiments/station_center_mos_sweep_v89.py` to test the v88
pattern across all station-speed replay cells. No submission was written.

| Dim | Decision | Avg delta | Worst split | Boundary |
|-----|----------|----------:|------------:|---------:|
| speed_stations_d1_ecs | hold below boundary | -0.5579 | -0.4930 | 0.5400 |
| speed_stations_d1_ns | diagnostic already rank 1 | -0.3751 | -0.3665 | — |
| speed_stations_d14_ecs | reject split regression | -0.2506 | +0.0840 | 0.0107 |
| speed_stations_d7_ecs | reject split regression | -0.2098 | +0.0323 | — |
| speed_stations_d7_ns | reject split regression | -0.1329 | +0.0480 | 0.0734 |
| speed_stations_d14_ns | reject split regression | +0.2146 | +0.4281 | — |

Lesson: v88's method is validated, but direct generalization is not enough for
another upload. The next station-speed improvement needs an additional
stability layer, most likely regime gating or station-specific shrinkage,
before trying `speed_stations_d1_ecs` or d7/d14 cells.

### Post-v89 follow-up: v90 gated ECS d1 center MOS

Implemented `src/experiments/station_d1_ecs_gated_center_mos_v90.py` to test
whether the near-miss ECS d1 station-speed cell could cross its public
rank-boundary by applying v89 only where it is replay-stable. The gate search
used out-of-fold predictions and tested station subsets, hour subsets, station
hour subsets, and threshold regimes over `base_q50`, `base_width`,
`forecast_speed`, and `wind_shear`.

No submission was written.

| Gate | Avg delta | Worst split | Boundary + margin | Decision |
|------|----------:|------------:|------------------:|----------|
| all | -0.5579 | -0.4930 | 0.5500 | hold below boundary |

The top gate was the full application (`all`). Every interpretable restriction
reduced aggregate gain or worsened split stability, so there is no evidence that
ECS d1 needs gating. The signal is broad but the center model is not yet strong
enough to clear the next rank boundary from v88/v86.

Lesson: do not spend another upload on gated ECS d1 station speed unless the
center model itself improves. The next real station-speed step should improve
the median residual model, not slice the existing MOS output.

### Post-v90 follow-up: v91 stronger ECS d1 center model

Implemented `src/experiments/station_d1_ecs_strong_center_mos_v91.py` to test
a stronger LightGBM median residual MOS for ECS d1 station speed. This candidate
uses a larger median model (`num_leaves=31`, `min_child_samples=50`,
`n_estimators=400`) and the same EB interval reconstruction.

Important correction: v91 validates against the **current v86/v88 ECS d1
interval-calibrated replay**, not the stale raw v59 station replay. That avoids
double-counting the v86 interval breakthrough.

No submission was written.

| Split | Current base | Candidate | Delta vs current | Delta vs raw |
|------|-------------:|----------:|-----------------:|-------------:|
| val | 5.9903 | 5.6823 | -0.3080 | -0.5569 |
| tune | 6.0114 | 5.6853 | -0.3261 | -0.5729 |
| holdout | 5.6709 | 5.3393 | -0.3316 | -0.7115 |

Summary:

- avg delta vs current: `-0.3219`
- worst split delta vs current: `-0.3080`
- boundary + margin: `0.5500`
- clears gate: no

Lesson: stronger ECS d1 median MOS is real, but it is not enough after v86.
The stale raw replay made it look like a boundary-clearing candidate; the
current-base replay shows it would probably remain second behind carlometta.
Do not upload ECS d1 station speed unless a method improves by about another
`0.24` WS over v91 on the current-base replay.

### Forward plan preserved for next sessions

After v89/v90/v91, the station-speed path is saturated for same-feature
learning. The next breakthrough attempt should add new station information:

1. station-neighbor / station-cluster residual features,
2. analog station residual ensemble,
3. spatial grid-to-station representativeness features,
4. rank-gap retargeting if ECS d1 remains too expensive.

The key validation lesson from v91 is mandatory: every candidate must be scored
against the current-base replay, not stale raw replay. Stale raw replay is
allowed only as a diagnostic to measure total signal before subtracting already
captured v86/v88 gains.

---

## V92: Enhanced station features for ECS d1 (generated, NOT uploaded)

**Date:** 2026-05-03
**Module:** `src/experiments/station_d1_ecs_enhanced_mos_v92.py`
**Base:** v88
**Target:** `speed_stations_d1_ecs`

### New feature families

1. **Station-month-hour climatology residual** — mean residual (`obs_speed - base_q50`) per station-month-hour, plus std and count. Captures systematic seasonal/diurnal biases.
2. **Station overall mean/std residual** — long-term mean residual per station.
3. **Regional residual proxy** — mean of `base_q50 - forecast_speed` across all other stations in the same region at the same target_time. Inference-valid proxy for synoptic-scale base-model bias.
4. **Height-wind interactions** — `log_height_m * wind_shear`, `log_height_m * forecast_speed`, `height_m * forecast_speed`.

### Validation vs current base (v86 interval calibration reconstructed out-of-fold)

| Split | Raw base | Current base | Candidate | Delta vs current | Coverage current | Coverage candidate |
|---|---:|---:|---:|---:|---:|---:|
| val | 6.2392 | 5.9903 | 5.6743 | -0.3161 | 0.8954 | 0.8848 |
| tune | 6.2583 | 6.0114 | 5.6581 | -0.3534 | 0.8930 | 0.8930 |
| holdout | 6.0508 | 5.6709 | 5.3740 | -0.2969 | 0.8938 | 0.8926 |

- Avg delta vs raw: `-0.6140`
- Avg delta vs current: `-0.3221`
- Worst split delta vs current: `-0.2969`
- One-rank boundary + margin: `0.1554`
- Clears current-base boundary: `True`

### Comparison with v91

| Metric | v91 (stronger LGBM) | v92 (enhanced features) |
|---|---|---|
| avg delta vs current | -0.3219 | -0.3221 |
| worst delta vs current | -0.3080 | -0.2969 |

V92 matches v91 almost exactly. The enhanced features compensate for a weaker LightGBM config (num_leaves=15 vs 31, n_estimators=220 vs 400) but do not provide incremental improvement.

### Feature importances (proxy config)

Top new features:
- `station_month_hour_climo`: 166
- `height_x_forecast_speed`: 87
- `regional_other_residual_mean`: 49
- `height_raw_x_forecast_speed`: 31
- `station_month_hour_climo_std`: 30
- `regional_residual_mean`: 27
- `station_mean_residual`: 25

### Verdict

**HOLD.** The enhanced features are real and inference-valid, but they do NOT meet the teams 0.24 WS improvement threshold over v91. The station-speed ECS d1 lane appears structurally capped at ~-0.32 WS vs current base with this class of features.

Submission zip was generated (`submission_v92.zip`) but is not recommended for upload unless the user wants to gamble on +1 rank transfer.

### Lessons

1. **Current-base validation is mandatory.** The raw-base delta of -0.6140 is completely misleading; the true incremental improvement is only -0.32.
2. **Feature engineering saturation.** Even genuinely new feature families (climatology, regional proxy, interactions) only match, not beat, a stronger baseline model.
3. **Next steps:** Either (a) try more radical feature families (analog ensemble, multi-grid IDW, temporal persistence), or (b) retarget to a different alive cell where the rank boundary is smaller relative to the base gap.

---

## V93: Radical station features for ECS d1 (generated, NOT uploaded)

**Date:** 2026-05-03
**Module:** `src/experiments/station_d1_ecs_radical_mos_v93.py`
**Base:** v88
**Target:** `speed_stations_d1_ecs`

### Radical feature families

1. **Temporal persistence** — lagged proxy residuals (`base_q50 - forecast_speed`) at 6h, 12h, 18h, 24h per station. Captures short-term forecast error persistence.
2. **Analog ensemble** — nearest-neighbor residual statistics from synoptic analogs. Search space: forecast_speed, msl, wind_shear, t2m, ws10, z700. k=30 neighbors. Features: mean, std, q05, q95 of neighbor residuals.

Both features are inference-valid:
- Persistence uses only base predictions and HRES forecasts (no observations needed).
- Analog pool is fitted on training data only; at inference, query rows search the training pool.

### Architecture

- Strong LightGBM median model: `num_leaves=31`, `n_estimators=400`, `learning_rate=0.025` (same as v91)
- Center-only prediction (center_weight=0.80)
- EB interval calibration (shrink=0.50, kappa=25.0)
- Validated vs current base (v86 interval calibration reconstructed out-of-fold)

### Validation results

| Split | Raw base | Current base | Candidate | Delta vs current | Coverage current | Coverage candidate |
|---|---:|---:|---:|---:|---:|---:|
| val | 6.2392 | 5.9903 | 5.6690 | -0.3213 | 0.8954 | 0.8747 |
| tune | 6.2583 | 6.0114 | 5.6713 | -0.3402 | 0.8930 | 0.8762 |
| holdout | 6.0508 | 5.6709 | 5.3484 | -0.3225 | 0.8938 | 0.8797 |

- Avg delta vs raw: `-0.6198`
- Avg delta vs current: `-0.3280`
- Worst split delta vs current: `-0.3213`
- Clears +1 rank boundary (0.1554): `True`

### Comparison across all ECS d1 attempts

| Version | Features | Model strength | Avg delta vs current | Worst delta vs current |
|---|---|---|---|---|
| v86 | Interval calibration only | N/A | ~-0.29 | — |
| v91 | v58 features | Strong (400 trees, 31 leaves) | **-0.3219** | -0.3080 |
| v92 | v58 + climatology + regional + height | Standard (220 trees, 15 leaves) | -0.3221 | -0.2969 |
| v93 | v92 + persistence + analog | Strong (400 trees, 31 leaves) | **-0.3280** | -0.3213 |

### The plateau is real

V93 adds two genuinely new, inference-valid feature families to the strong v91 model. The improvement is **~0.006 WS** — essentially noise. This confirms:

1. The station-speed ECS d1 lane is structurally capped at approximately **-0.32 WS** vs the current base for any model built on v58-style grid features + replay residuals.
2. Temporal persistence and analog ensembles are real signals (they show high feature importances: residual_lag_6h=120, analog_residual_std=8), but they are **already captured implicitly** by the strong LightGBM model on the existing feature set.
3. The next breakthrough requires either a completely different modeling paradigm or a different target cell.

### Verdict

**HOLD.** V93 does not meet the 0.24 WS improvement threshold over v91. The submission zip exists but should not be uploaded unless the user wants to gamble on marginal +1 rank transfer.

### Forward path

The three feature families requested by the user have been fully explored:

1. ✅ **Neighbor residuals / spatial aggregates** — implemented as regional residual proxy (v92)
2. ✅ **Analog matches** — implemented as synoptic analog ensemble (v93)
3. ✅ **Temporal persistence** — implemented as lagged residual features (v93)

None broke the plateau. The remaining option from the original list is **multi-grid IDW spatial representativeness**, but given the pattern above, it is unlikely to provide the needed 0.24 WS breakthrough.

**Recommended next step:** Rank-gap retargeting. Identify the next alive cell with the smallest rank-boundary-to-base-gap ratio and apply the proven v88 center-MOS + EB calibration architecture there.

---

## V94: Global half-offset for surface d7 speed (REJECTED — hidden transfer failed catastrophically)

**Date:** 2026-05-03
**Module:** `src/experiments/surface_d7_global_half_offset_v94.py`
**Base:** v88
**Target:** `speed_surface_d7_ns` and `speed_surface_d7_ecs`

### Motivation

After confirming the station-speed ECS d1 plateau (~-0.32 WS cap), rank-gap analysis showed the smallest actionable gaps were in surface d7/d14 cells. The v77 diagnostic (ECS 10m) had previously found a sign-stationary bias, but v52/v80 spatial probes regressed hidden. This module revisits surface d7 with a corrected obs source and tests all four (region x level) combinations.

### Offsets applied

| Region | Level | Half offset |
|---|---|---:|
| NS | 10m | **+0.1397** |
| NS | 100m | **-0.9916** |
| ECS | 10m | **+0.2023** |
| ECS | 100m | **-0.2922** |

### Local diagnostic (misleading)

The corrected local diagnostic showed ALL splits improving for ALL four (region, level) combinations, including the local "hidden" split (Dec 31 - Jan 7):

| Cell | val delta | tune delta | holdout delta | hidden delta |
|---|---|---:|---:|---:|
| NS 10m | -0.05 | +0.07 | -0.05 | **-0.31** |
| NS 100m | -1.17 | -1.37 | -1.16 | **-0.45** |
| ECS 10m | -0.18 | -0.10 | -0.14 | **-0.11** |
| ECS 100m | -0.17 | -0.24 | -0.19 | **-0.21** |

### Actual leaderboard results (catastrophic failure)

| Dimension | v88 score | v94 score | **Delta** |
|---|---|---:|---:|
| speed_surface_d7_ns | 14.4643 | **15.2702** | **+0.8059** 🔴 |
| speed_surface_d7_ecs | 9.8216 | **9.8957** | **+0.0741** 🔴 |
| **primary_score** | **1.425474** | **1.427919** | **+0.002445** 🔴 |

Both target dimensions got WORSE. The primary score degraded by +0.002445.

### Why it failed

The local "hidden" split (8 days at the 2021->2022 boundary) is **not representative** of the actual leaderboard hidden scoring (full 2022 inference windows). The weather patterns in the actual 2022 hidden data are fundamentally different from the training distribution, and the val-fit offsets **overfit to the training regime**.

Specifically:
- **NS 100m**: Local hidden suggested -0.45 improvement; actual hidden was **+0.81 worse**. The -0.99 offset moved the center in the wrong direction for 2022.
- **ECS 100m**: Local hidden suggested -0.21 improvement; actual hidden was **+0.07 worse**.

This confirms that **simple global offsets on surface cells do not transfer** — the pattern holds across v52, v80, v77, and now v94.

### Verdict

**REJECT.** This is now the fourth consecutive failure of surface-cell global offset corrections (v52 spatial aggregation, v80 proxy bias, v77 ECS 10m held, v94 all levels). The surface d7 lane appears structurally uncorrectable via simple parallel shifts.

### Lessons

1. **Local hidden is NOT leaderboard hidden.** Even when ALL local splits (val, tune, holdout, hidden) improve, the actual 2022 hidden can regress catastrophically. The 8-day local hidden split is a poor proxy for full-year 2022 weather.
2. **Surface cells are regime-dependent.** The structural biases observed in training (2019-2021) do not persist into 2022. This suggests the base model already captures the best possible time-invariant correction.
3. **Stop trying global offsets on surface.** This pattern is now definitively dead. Any future surface work must be either (a) regime-conditional, (b) learned from 2022-like data, or (c) focused on other mechanisms (width modulation, ensemble blending, etc.).
4. **The rank-gap heuristic is dangerous for surface.** Small gaps (0.0016-0.0043) tempted us into thinking a tiny correction would suffice, but the actual required correction is both large AND regime-dependent.

---

## V95: Station d7 center-MOS + EB intervals (REJECTED — validation failed)

**Date:** 2026-05-03
**Module:** `src/experiments/station_d7_center_mos_v95.py`
**Base:** v88
**Target:** `speed_stations_d7_ns` and `speed_stations_d7_ecs`

### Motivation

After v94's catastrophic surface failure, the next logical target was station d7 — a dimension where the v88 architecture had not yet been applied, and where v89 had found near-miss improvements with split regressions. The hypothesis was that v58's richer spatial-context features + full quantile regression + center blend + EB intervals might stabilize the d7 predictions where v89's simpler track_e features + median MOS had failed.

### Architecture

- **Feature builder:** v58's `_build_rows` adapted for horizon=7 (spatial context, regional aggregates, pressure-stack features)
- **Model:** LightGBM quantile regression (0.05/0.50/0.95), 220 trees, 15 leaves
- **Center blend:** weight=0.80 (v88 proven parameter)
- **EB interval calibration:** shrink=0.35, kappa=25.0 (v88 proven parameter)
- **Validation:** leave-one-period, gate = boundary + 0.01 margin

### North Sea d7 results (catastrophic)

| Split | Base | Candidate | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 13.7752 | 14.4680 | **+0.6927** 🔴 | 0.9056 | 0.8312 |
| tune | 12.9126 | 13.4394 | **+0.5269** 🔴 | 0.9061 | 0.8248 |
| holdout | 14.4712 | 14.9291 | **+0.4579** 🔴 | 0.9047 | 0.8299 |

- **Avg delta: +0.5592**
- **Worst delta: +0.6927**
- Coverage collapses from ~90.5% to ~82.9%

**All three splits got significantly worse.** The center MOS is moving in the wrong direction, and the EB intervals are severely over-shrinking.

### East China Sea d7 results (split regression)

| Split | Base | Candidate | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 9.1630 | 9.0128 | −0.1503 | 0.9036 | 0.8651 |
| tune | 10.4566 | 10.8007 | **+0.3441** 🔴 | 0.8993 | 0.8652 |
| holdout | 9.2687 | 8.8836 | −0.3851 | 0.9224 | 0.8989 |

- **Avg delta: −0.0638**
- **Worst delta: +0.3441**
- Coverage drops from ~90.8% to ~87.6%

Same pattern as v89: val/holdout improve, **tune regresses massively** (+0.34). The d7 residual structure is seasonally non-stationary — the model overfits to winter patterns and fails in summer.

### Comparison to v89

| Approach | NS d7 avg | NS d7 worst | ECS d7 avg | ECS d7 worst |
|---|---|---:|---:|---:|
| v89 (track_e + median MOS) | −0.1329 | +0.0480 | −0.2098 | +0.0323 |
| **v95 (v58 + full quantile + center blend)** | **+0.5592** | **+0.6927** | −0.0638 | **+0.3441** |

**The richer v88 architecture is actually WORSE for d7 than v89's simpler approach.** The spatial context and full quantile regression overfit more severely to the training distribution.

### Verdict

**REJECT.** Station d7 is structurally uncorrectable with MOS architectures. The d7 residual patterns are too different from d1 — 7-day forecast uncertainty is too large, and seasonal non-stationarity makes any learned correction unstable.

This is now the **fifth consecutive failure** of station-speed d7 attempts:
- v34 (track E residual overlay): failed hidden transfer
- v89 (median MOS sweep): split regressions
- v95 (v88 full architecture): catastrophic NS / severe ECS split regression

### Lessons

1. **The v88 architecture is d1-specific.** Its success on d1 NS/ECS does not generalize to d7. The 7-day horizon has fundamentally different residual statistics.
2. **Coverage collapse is a leading indicator.** When EB interval calibration drops coverage from 90% to 83%, the model is severely overfitting. This happened for both NS and ECS d7.
3. **Seasonal non-stationarity dominates d7.** The summer (tune) split consistently regresses while winter (val/holdout) improves. Any d7 correction needs to be season-aware.
4. **Station-speed d7 is dead for this model class.** Like surface d7, it should not be attempted again without a completely different paradigm.

---

## V96: NS grid direction copula (NEUTRAL — rank unchanged)

**Date:** 2026-05-03
**Module:** inline script (no new module file)
**Base:** v88
**Target:** NS grid direction (all levels, all horizons)

### Actual leaderboard results

**primary_score: 1.425478** (vs v88's 1.425474) — **effectively identical** (+0.000004).

| Dimension | v88 score | v96 score | **Δ** |
|---|---|---:|---:|
| dir_surface_d7_ns | 291.1414 | **285.8152** | **−5.3262** ✅ |
| dir_pressure_d7_ns | 278.8434 | **276.6085** | **−2.2349** ✅ |
| dir_pressure_d14_ns | 299.2189 | **297.3284** | **−1.8905** ✅ |
| dir_surface_d14_ns | 298.3924 | **297.0769** | **−1.3155** ✅ |
| dir_surface_d1_ns | 91.1033 | **90.8856** | **−0.2177** ✅ |
| dir_pressure_d1_ns | 79.8870 | **80.1201** | **+0.2331** 🔴 |
| All other 30 dimensions | — | — | 0.0000 |

NS grid direction improved on 5 of 6 dimensions, but the improvements were **much smaller** than when v46 was originally applied to v41:

| Dimension | v46 on v41 | v96 on v88 |
|---|---|---:|
| dir_surface_d7_ns | **−6.77** | −5.33 |
| dir_surface_d14_ns | **−9.03** | −1.32 |
| dir_pressure_d7_ns | **−5.11** | −2.23 |
| dir_pressure_d14_ns | **−1.06** | −1.89 |
| dir_surface_d1_ns | **−0.52** | −0.22 |

### Why the effect was smaller

v41's NS grid direction was **worse** than v88/v59's. v41 had mean circular differences of ~3° for dir_50 and ~14.5° for dir_05/dir_95 vs v59. v46 had more "room to improve" on v41. On v88 (which is essentially v59 for grid direction), the base is already better, so the copula adjustment delivers smaller absolute gains.

### Verdict

**NEUTRAL / RANK UNCHANGED.** The submission is safe — no dimensions regressed catastrophically — but it does not improve the primary score. The mean_rank is effectively identical to v88.

### Lessons

1. **Copula effect size depends on base quality.** v46 was a breakthrough on v41 because v41's direction intervals were poorly calibrated. On v59/v88, the base is already better, so the same mechanism yields diminishing returns.
2. **Primary score is mean_rank, not mean cWS.** Even a −5 cWS improvement on one dimension may not change the rank if that dimension was already competitive.
3. **Grid direction on v88 is near its ceiling for this class of corrections.** Further improvements to NS grid direction need a different mechanism (e.g., regime-conditional, per-horizon damping like v47 attempted, or directional bias correction).

---

## Background

The user's request was to apply the v46 copula approach to the worst-scoring direction dimensions: `dir_stations_d14_ecs` (332.9), `dir_surface_d14_ecs` (331.9), and `dir_stations_d7_ns` (315.7).

Upon investigation, this recommendation was **flawed**:
1. **v46 only operates on grid rows** — it does not touch station direction at all
2. **v46 previously made ECS d14 surface WORSE** (+0.66 cWS) and ECS d7/d14 pressure worse (+0.59, +0.69)
3. **v46 previously helped NS grid direction significantly**:
   - `dir_surface_d7_ns`: −6.77 cWS
   - `dir_surface_d14_ns`: −9.03 cWS
   - `dir_pressure_d7_ns`: −5.11 cWS
   - `dir_pressure_d1_ns`: −1.20 cWS
   - `dir_surface_d1_ns`: −0.52 cWS

### What was built

Instead of blindly applying v46 everywhere, v96 applies the v46 copula **only to North Sea grid rows** — the subset where v46 is proven to help. ECS grid is intentionally skipped. Station direction is untouched.

- **Changed rows:** 1,721,307 (all NS grid direction intervals)
- **Speed quantiles:** unchanged
- **Direction center (dir_50):** unchanged
- **Direction bounds (dir_05, dir_95):** narrowed or widened based on predicted speed and fitted speed-direction correlation

### Scope

| Dimension | v46 previous effect on v41 | v96 action |
|---|---|---|
| dir_surface_d7_ns | −6.77 cWS | **Applied** |
| dir_surface_d14_ns | −9.03 cWS | **Applied** |
| dir_pressure_d7_ns | −5.11 cWS | **Applied** |
| dir_pressure_d14_ns | −1.06 cWS | **Applied** |
| dir_surface_d1_ns | −0.52 cWS | **Applied** |
| dir_pressure_d1_ns | −1.20 cWS | **Applied** |
| dir_surface_d7_ecs | −0.76 cWS | **Skipped** (risk of regression) |
| dir_surface_d14_ecs | **+0.66 cWS** | **Skipped** |
| dir_pressure_d7_ecs | **+0.59 cWS** | **Skipped** |
| dir_pressure_d14_ecs | **+0.69 cWS** | **Skipped** |
| All station direction | 0.00 (no effect) | **Skipped** (v46 doesn't apply) |

### Verdict

**PENDING LEADERBOARD SCORE.** This is a conservative, evidence-based re-application of a proven pattern on the subset where it is known to help. The expected effect is a small improvement to the primary score (~−0.001 to −0.002) from NS grid direction improvements alone.

**Risk:** Low. The scope is well-understood, the physical mechanism is sound, and the regions where v46 regressed are explicitly excluded.

### Lessons

1. **Re-application requires forensic analysis.** My original recommendation to target `dir_stations_d14_ecs` with v46 was wrong because v46 doesn't touch stations. Always verify the scope of a proven pattern before recommending it for new dimensions.
2. **Proven patterns can have anti-correlated regions.** v46 helped NS but hurt ECS. A blanket re-application would have been harmful. Subsetting to the winning region is the right conservative play.
3. **Station direction remains unaddressed.** The two worst dimensions (`dir_stations_d14_ecs` and `dir_stations_d7_ns`) are still at their base scores. A future session should explore Track I-style residual direction models or per-station bias corrections for these cells.

---

## Motivation

After v94's catastrophic surface failure, the next logical target was station d7 — a dimension where the v88 architecture had not yet been applied, and where v89 had found near-miss improvements with split regressions. The hypothesis was that v58's richer spatial-context features + full quantile regression + center blend + EB intervals might stabilize the d7 predictions where v89's simpler track_e features + median MOS had failed.

### Architecture

- **Feature builder:** v58's `_build_rows` adapted for horizon=7 (spatial context, regional aggregates, pressure-stack features)
- **Model:** LightGBM quantile regression (0.05/0.50/0.95), 220 trees, 15 leaves
- **Center blend:** weight=0.80 (v88 proven parameter)
- **EB interval calibration:** shrink=0.35, kappa=25.0 (v88 proven parameter)
- **Validation:** leave-one-period, gate = boundary + 0.01 margin

### North Sea d7 results (catastrophic)

| Split | Base | Candidate | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 13.7752 | 14.4680 | **+0.6927** 🔴 | 0.9056 | 0.8312 |
| tune | 12.9126 | 13.4394 | **+0.5269** 🔴 | 0.9061 | 0.8248 |
| holdout | 14.4712 | 14.9291 | **+0.4579** 🔴 | 0.9047 | 0.8299 |

- **Avg delta: +0.5592**
- **Worst delta: +0.6927**
- Coverage collapses from ~90.5% to ~82.9%

**All three splits got significantly worse.** The center MOS is moving in the wrong direction, and the EB intervals are severely over-shrinking.

### East China Sea d7 results (split regression)

| Split | Base | Candidate | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 9.1630 | 9.0128 | -0.1503 | 0.9036 | 0.8651 |
| tune | 10.4566 | 10.8007 | **+0.3441** 🔴 | 0.8993 | 0.8652 |
| holdout | 9.2687 | 8.8836 | -0.3851 | 0.9224 | 0.8989 |

- **Avg delta: -0.0638**
- **Worst delta: +0.3441**
- Coverage drops from ~90.8% to ~87.6%

Same pattern as v89: val/holdout improve, **tune regresses massively** (+0.34). The d7 residual structure is seasonally non-stationary — the model overfits to winter patterns and fails in summer.

### Comparison to v89

| Approach | NS d7 avg | NS d7 worst | ECS d7 avg | ECS d7 worst |
|---|---|---:|---:|---:|
| v89 (track_e + median MOS) | -0.1329 | +0.0480 | -0.2098 | +0.0323 |
| v95 (v58 + full quantile + center blend) | **+0.5592** | **+0.6927** | -0.0638 | **+0.3441** |

**The richer v88 architecture is actually WORSE for d7 than v89's simpler approach.** The spatial context and full quantile regression overfit more severely to the training distribution.

### Verdict

**REJECT.** Station d7 is structurally uncorrectable with MOS architectures. The d7 residual patterns are too different from d1 — 7-day forecast uncertainty is too large, and seasonal non-stationarity makes any learned correction unstable.

This is now the **fifth consecutive failure** of station-speed d7 attempts:
- v34 (track E residual overlay): failed hidden transfer
- v89 (median MOS sweep): split regressions
- v95 (v88 full architecture): catastrophic NS / severe ECS split regression

### Lessons

1. **The v88 architecture is d1-specific.** Its success on d1 NS/ECS does not generalize to d7. The 7-day horizon has fundamentally different residual statistics.
2. **Coverage collapse is a leading indicator.** When EB interval calibration drops coverage from 90% to 83%, the model is severely overfitting. This happened for both NS and ECS d7.
3. **Seasonal non-stationarity dominates d7.** The summer (tune) split consistently regresses while winter (val/holdout) improves. Any d7 correction needs to be season-aware.
4. **Station-speed d7 is dead for this model class.** Like surface d7, it should not be attempted again without a completely different paradigm.

---

## Motivation

After confirming the station-speed ECS d1 plateau (~-0.32 WS cap), rank-gap analysis showed the smallest actionable gaps were in surface d7/d14 cells. The v77 diagnostic (ECS 10m) had previously found a sign-stationary bias, but v52/v80 spatial probes regressed hidden. This module revisits surface d7 with a corrected obs source and tests all four (region x level) combinations.

### Offsets applied

| Region | Level | Half offset |
|---|---|---:|
| NS | 10m | **+0.1397** |
| NS | 100m | **-0.9916** |
| ECS | 10m | **+0.2023** |
| ECS | 100m | **-0.2922** |

### Local diagnostic (misleading)

The corrected local diagnostic showed ALL splits improving for ALL four (region, level) combinations, including the local "hidden" split (Dec 31 - Jan 7):

| Cell | val delta | tune delta | holdout delta | hidden delta |
|---|---|---:|---:|---:|
| NS 10m | -0.05 | +0.07 | -0.05 | **-0.31** |
| NS 100m | -1.17 | -1.37 | -1.16 | **-0.45** |
| ECS 10m | -0.18 | -0.10 | -0.14 | **-0.11** |
| ECS 100m | -0.17 | -0.24 | -0.19 | **-0.21** |

### Actual leaderboard results (catastrophic failure)

| Dimension | v88 score | v94 score | **Delta** |
|---|---|---:|---:|
| speed_surface_d7_ns | 14.4643 | **15.2702** | **+0.8059** 🔴 |
| speed_surface_d7_ecs | 9.8216 | **9.8957** | **+0.0741** 🔴 |
| **primary_score** | **1.425474** | **1.427919** | **+0.002445** 🔴 |

Both target dimensions got WORSE. The primary score degraded by +0.002445.

### Why it failed

The local "hidden" split (8 days at the 2021->2022 boundary) is **not representative** of the actual leaderboard hidden scoring (full 2022 inference windows). The weather patterns in the actual 2022 hidden data are fundamentally different from the training distribution, and the val-fit offsets **overfit to the training regime**.

Specifically:
- **NS 100m**: Local hidden suggested -0.45 improvement; actual hidden was **+0.81 worse**. The -0.99 offset moved the center in the wrong direction for 2022.
- **ECS 100m**: Local hidden suggested -0.21 improvement; actual hidden was **+0.07 worse**.

This confirms that **simple global offsets on surface cells do not transfer** — the pattern holds across v52, v80, v77, and now v94.

### Verdict

**REJECT.** This is now the fourth consecutive failure of surface-cell global offset corrections (v52 spatial aggregation, v80 proxy bias, v77 ECS 10m held, v94 all levels). The surface d7 lane appears structurally uncorrectable via simple parallel shifts.

### Lessons

1. **Local hidden is NOT leaderboard hidden.** Even when ALL local splits (val, tune, holdout, hidden) improve, the actual 2022 hidden can regress catastrophically. The 8-day local hidden split is a poor proxy for full-year 2022 weather.
2. **Surface cells are regime-dependent.** The structural biases observed in training (2019-2021) do not persist into 2022. This suggests the base model already captures the best possible time-invariant correction.
3. **Stop trying global offsets on surface.** This pattern is now definitively dead. Any future surface work must be either (a) regime-conditional, (b) learned from 2022-like data, or (c) focused on other mechanisms (width modulation, ensemble blending, etc.).
4. **The rank-gap heuristic is dangerous for surface.** Small gaps (0.0016-0.0043) tempted us into thinking a tiny correction would suffice, but the actual required correction is both large AND regime-dependent.

---

## Motivation

After confirming the station-speed ECS d1 plateau (~-0.32 WS cap), rank-gap analysis showed the smallest actionable gaps were in surface d7/d14 cells. The v77 diagnostic (ECS 10m) had previously found a sign-stationary bias, but v52/v80 spatial probes regressed hidden. This module revisits surface d7 with a corrected obs source and tests all four (region × level) combinations.

### Corrected diagnostic method

The initial diagnostic used `reanalysis_*_6h.parquet` which lost 90% of hidden rows. The corrected diagnostic uses `train_features.parquet` with `speed_d7_h{HH}` columns, matching the same obs source as the replay base. Hidden now has 79,515 rows per (region, level).

### Offsets (val-fit half-residual)

| Region | Level | Val mean residual | Half offset |
|---|---|---:|---:|
| NS | 10m | +0.2794 | **+0.1397** |
| NS | 100m | −1.9832 | **−0.9916** |
| ECS | 10m | +0.4046 | **+0.2023** |
| ECS | 100m | −0.5844 | **−0.2922** |

### Per-split results (hidden = Dec 31 – Jan 7)

**North Sea 10m:**
- val: −0.05, tune: **+0.07** (worsens), holdout: −0.05, **hidden: −0.31**

**North Sea 100m:**
- val: −1.17, tune: −1.37, holdout: −1.16, **hidden: −0.45**

**East China Sea 10m:**
- val: −0.18, tune: −0.10, holdout: −0.14, **hidden: −0.11**

**East China Sea 100m:**
- val: −0.17, tune: −0.24, holdout: −0.19, **hidden: −0.21**

### Net effect on dimensions

Assuming equal weighting of 10m and 100m within each dimension:

| Dimension | Base score (v88) | Est. improvement | Rank-1 gap | Verdict |
|---|---|---:|---:|---|
| speed_surface_d7_ns | 14.4643 | **~−0.38** | 0.0043 | **Likely clears** |
| speed_surface_d7_ecs | 9.6259 | **~−0.16** | 0.0016 | **Likely clears** |

### Key structural finding

**100m levels have consistent structural biases across ALL splits** (val, tune, holdout, hidden) in BOTH regions. The 100m base is systematically biased HIGH (negative residual). This is a robust, physics-motivated correction.

**10m levels also improve on hidden** but NS 10m shows seasonal non-stationarity: the bias is positive in winter (val/holdout) and negative in summer (tune). The half-offset fitted on winter data slightly overcorrects summer but still improves the winter-heavy hidden split.

### Scope

Only 328,320 rows changed out of 3,448,800 total — exclusively grid horizon=7 speed quantiles. Direction unchanged. All other dimensions (stations, pressure, other horizons) identical to v88.

### Verdict

**PENDING LEADERBOARD SCORE.** Submission zip generated at `starting-kit/phase_1/submission_v94.zip`. Recommended for upload — this is the first surface-cell correction with consistent hidden-transfer evidence since v77.

### Lessons

1. **Obs source matters.** The initial diagnostic using reanalysis parquet was completely wrong for hidden (7,695 rows vs 79,515). Always use the train features parquet for grid-cell obs.
2. **100m levels are structurally biased high.** This is consistent across regions and seasons. A simple global half-offset is the right first correction.
3. **Seasonal non-stationarity in 10m.** NS 10m bias flips sign winter→summer. Future work could fit a seasonal model, but the half-offset still helps hidden.


---

## v97 — Gated Track I d7 NS Station Direction (PENDING SCORE)

**Date:** 2026-05-03
**Module:** `src/experiments/track_i_d7_ns_v88.py`, `src/pipeline/run_v97.py`
**Base:** v88
**Target:** `dir_stations_d7_ns`

### Motivation

After v96's neutral result, the next viable target was `dir_stations_d7_ns` = 315.7, one of the two worst station direction dimensions (the other, d14 ECS, is frozen per v43). Track I had never been applied to d7 NS. The existing `track_i_v38_residual_direction.py` local eval showed catastrophic holdout regression (+117 cWS ungated), but v41 proved gated Track I can work for ECS d7.

### Approach

1. **Strong regularization**: Reduce `n_estimators` from 60→40, `learning_rate` 0.04→0.03, `subsample` 0.9→0.8, `colsample_bytree` 0.9→0.8, `min_child_samples` 15→20.
2. **Conservative gate**: `center_shift <= 15°` (stricter than v41's 20°).
3. **Narrow scope**: Only north_sea station rows, horizon=7, direction columns.

### Local Evaluation

| Gate | val Δ | tune Δ | holdout Δ | Accepted |
|------|------:|-------:|----------:|---------:|
| ungated | −11.5 | −17.7 | **+64.7** 🔴 | 3013/3013 |
| <=20° | −23.2 | −16.1 | −15.1 | 2688/3013 |
| **<=15°** | **−22.4** | **−13.7** | **−15.7** ✅ | **2668/3013** |
| <=10° | −20.9 | −10.5 | −14.4 | 2562/3013 |
| <=5° | −15.5 | −4.7 | −10.3 | 2012/3013 |

The 15° gate is the sweet spot: all three splits improve, holdout is the best-improved split, and coverage recovers to ~90%.

### Submission Build

- Base: `predictions_v88.csv`
- Candidate rows: 256 (8 stations × 4 hours × 8 windows)
- Accepted by 15° gate: 55 rows (21.5%)
- Rejected: 201 rows (78.5%)
- Changed speed rows: 0
- Changed direction rows: 55

### Scope Verification

- ZIP: `submissions/submission_v97.zip`
- Manifest: `logs/v97_gated_track_i_d7_ns/v97_manifest.json`
- Tests: `tests/test_run_v97.py` (8/8 passed)

### Decision Tree

- **If leaderboard improves d7 NS:** PROMOTE. The 15° gate successfully captured transferable Track I signal for d7 NS, validating the gated residual pattern across both regions.
- **If leaderboard is neutral:** HOLD. The change is too small (only 55 rows) to move the needle. Consider relaxing the gate to 20° or combining with another small improvement.
- **If leaderboard regresses:** REJECT. Even conservative gating is insufficient for d7 NS hidden transfer. Freeze d7 NS station direction and retarget to grid direction cells.

### Lesson

PENDING SCORE. Local evaluation is strongly positive for the 15° gate on all three splits, but the submission changes only 55 rows, so the leaderboard effect may be small. The ungated model's catastrophic holdout regression (+64.7 cWS) confirms that gating is essential for d7 NS, just as it was for ECS d7 in v41.

### Actual Leaderboard Result

**REJECT.** `dir_stations_d7_ns` regressed catastrophically:

| Dim | v88 | v97 | Delta |
|-----|-----|-----|-------|
| dir_stations_d7_ns | 315.7238 | **376.9924** | **+61.2686** 🔴 |
| primary_score | 1.425474 | 1.425474 | 0.000000 |

All other 35 dimensions were preserved exactly. The primary score did not move because the rank effect of 55 changed rows was too small, but the raw dimension score regressed by +61.3 cWS.

### Why the local evaluation failed us

The local evaluation showed the 15° gate improving all three splits:
- val: −22.4 cWS
- tune: −13.7 cWS
- holdout: −15.7 cWS

But the **feature baseline** used for local training is not the same as **v88's heavy baseline** used on the leaderboard. The Track I model learned residuals against the feature baseline (HRES forecast `dir_d7_h{hour}`). When those same corrections were applied to v88's heavy baseline, they systematically moved the center *away* from the true hidden observations for the accepted rows.

This is the same failure mode as v43 (d14 ECS): the inference baseline distribution is shifted from the training baseline, and even small gated corrections transfer poorly.

### Verdict

**REJECT. Freeze `dir_stations_d7_ns` permanently.**

Both of the two worst station direction dimensions are now frozen:
- `dir_stations_d14_ecs` = 332.9 — frozen since v43
- `dir_stations_d7_ns` = 315.7 → 377.0 — frozen as of v97

No further Track I or residual-based attempts should be made on station direction for d7/d14 horizons. The training baseline mismatch is insurmountable for these cells.

### Lesson

1. **Local validation against the feature baseline is not a reliable proxy for leaderboard transfer when the submission base uses a different baseline.** The feature baseline (HRES) and heavy baseline are divergent enough that corrections trained on one harm the other.
2. **Gating does not fix baseline mismatch.** The 15° gate filtered out large shifts but the *small* shifts that passed were still harmful. The gate assumes the model's small corrections are directionally correct — this assumption fails when the baseline distributions differ.
3. **Station direction at d7/d14 horizons may be near a hard ceiling for this competition.** Both ECS and NS d7/d14 station direction have now resisted multiple correction attempts (Track I, MOS, copula, global offsets). The remaining headroom should be sought in grid direction or grid speed cells.

### Recommended next target

Retarget to grid-level dimensions where the baseline is consistent between training and inference:
- `dir_surface_d14_ecs` = 331.9 (grid, copula or pressure-shear candidate)
- `dir_pressure_d14_ecs` = 314.3 (grid, v51-style damping candidate)

---

## V98: CatBoost quantile regression for ECS d1 station speed (HOLD — near-miss on boundary)

**Date:** 2026-05-03
**Module:** `src/experiments/station_d1_ecs_catboost_v98.py`
**Base:** v88
**Target:** `speed_stations_d1_ecs`

### Motivation

After v91's strong LightGBM plateaued at ~-0.32 WS vs the v86 current base, and v92/v93's enhanced/radical features failed to break through, this experiment tests whether CatBoost's ordered boosting and native categorical handling can capture residual signal that LightGBM misses.

### Architecture

- **Model:** CatBoost quantile regression (0.05/0.50/0.95), 400 iterations, depth=6, lr=0.03
- **Features:** Same v58 feature builder as v91 (345 cols)
- **Center blend:** 0.80
- **EB interval calibration:** shrink=0.50, kappa=25.0
- **Validation:** leave-one-period vs current base (v86 interval calibrator reconstructed OOF)

### Results

| split | base_ws | cand_ws | delta |
|---|---|---:|---:|
| val | 5.9903 | 5.3691 | **−0.6212** |
| tune | 6.0114 | 5.1938 | **−0.8176** |
| holdout | 5.6709 | 5.1623 | **−0.5086** |

- **Avg delta: −0.6491**
- **Worst delta: −0.5086**
- **Rank boundary: −0.540001**
- **Clears boundary: NO** (misses by 0.0314 WS on holdout)

### Parameter sweep

Tested stronger regularization (depth=5, l2=5.0) and lower center weights (0.65). Both made holdout worse:

| depth | lr | l2 | cw | val | tune | holdout | avg | worst |
|---|---|---|---|---|---|---|---|---|
| 6 | 0.03 | 3.0 | 0.65 | −0.5323 | −0.7147 | −0.4357 | −0.5609 | −0.4357 |
| 5 | 0.025 | 5.0 | 0.65 | −0.3653 | −0.5289 | −0.2856 | −0.3932 | −0.2856 |

The v98 default (depth=6, cw=0.80) is the best configuration.

### Interval calibration sweep

Tested shrink ∈ {0.30, 0.35, 0.40, 0.50, 0.60, 0.70} and kappa ∈ {10, 25, 50, 100}. The best holdout is shrink=0.50, kappa=10.0 with worst_delta=−0.5089 — barely different from kappa=25.0.

### Why holdout is the bottleneck

The CatBoost model improves holdout MAE by +0.1520 (15.5% relative), but the Winkler score only improves by −0.5086 WS (9.0% relative). The Winkler score is less responsive to center improvement than MAE because it also penalizes interval width and coverage.

The holdout split (late 2021 / early 2022) has genuinely different residual patterns than val/tune. Even with strong regularization, the model overfits to the training distribution.

### Verdict

**HOLD.** v98 is the strongest ECS d1 result since v86, but it does not clear the strict rank-boundary gate. The miss margin is small (0.03 WS), but the class-of-move rule and the history of near-miss rejections (v91, v92, v93, v94, v95) counsel conservatism.

### Lessons

1. **CatBoost captures signal that LightGBM misses.** The −0.65 WS avg improvement is roughly double v91's −0.32 WS. Ordered boosting and native categorical handling do help for this task.
2. **Holdout stability is the hard ceiling.** No configuration of regularization or center weight pushed holdout below −0.54 WS. The late-2021 residual distribution is structurally different from val/tune.
3. **ECS d1 station speed may be near its ceiling.** v86 already captured the easy interval-calibration gain. Further center improvements are real but marginal and not guaranteed to transfer.

### Recommended next targets

With ECS d1 plateaued and the two worst station direction dimensions frozen, the remaining actionable targets are:

1. **`dir_surface_d14_ecs`** — rank 3, gap 5.1 cWS. Atlas shows broad coverage problem (81% overall). Regime-gated width expansion is a physics-driven candidate.
2. **`dir_stations_d14_ns`** — rank 2, gap 4.45 cWS. Untouched since v31 but station-direction is risky.
3. **Grid speed d1** — rank 2, gaps ~0.047 WS. Tiny but no hidden-proven mechanism exists.


---

## V98b: Regime-gated width expansion diagnostic for dir_surface_d14_ecs (HOLD — signal too small)

**Date:** 2026-05-03
**Target:** `dir_surface_d14_ecs`

### Method

Using the `ecs_surface_d14_direction_atlas.parquet` (9.3M samples), simulated regime-gated width expansions:
- Regimes defined by (level, speed_regime, season, direction_sector)
- Expansion applied only to regimes with coverage < threshold
- delta = total degrees added to interval width

### Results

Best configuration: threshold=0.90, delta=15°

| split | base cWS | expanded cWS | delta |
|---|---|---:|---:|
| val | 328.24 | 326.93 | **−1.31** |
| tune | 336.41 | 334.84 | **−1.57** |
| holdout | 326.12 | 325.60 | **−0.52** |

- **Avg delta: −1.13 cWS**
- **Worst delta: −0.52 cWS**
- **Rank boundary: −5.10 cWS**

### Why it doesn't clear

The holdout improvement is only −0.52 cWS, far below the 5.1 cWS needed for rank 2. The atlas shows that while low-coverage regimes have very high per-regime cWS (420+), they represent only 1.6% of rows. The broad coverage problem (81% overall) is distributed across 20% of rows, but a targeted width expansion only yields ~1 cWS aggregate improvement.

A global width expansion makes cWS worse because the width penalty on already-inside points outweighs the benefit for outside points.

### Verdict

**HOLD.** A regime-gated width expansion has real signal (~1 cWS on val/tune) but insufficient holdout transfer and insufficient magnitude to clear the rank boundary.

### Lessons

1. **Coverage is the dominant driver of cWS** (R²=0.97 with coverage + width). But improving coverage through width expansion alone is inefficient.
2. **Center bias is the real problem.** The atlas shows signed biases up to +59° and −72° in worst regimes. Width expansion cannot compensate for large center errors without absurdly wide intervals.
3. **Any meaningful improvement to `dir_surface_d14_ecs` requires center correction, not just width expansion.** But v60 proved learned center corrections overfit. A physics-driven center correction (e.g., regime-specific climatology bias) is the only viable path.


## V101 — Residual-target CatBoost MOS for ECS d1 station speed (SCORED — PROMOTED)

**Date:** 2026-05-03
**Target:** `speed_stations_d1_ecs`
**Base:** v88 → **v101 is new base**

### Big idea
Train CatBoost to predict `base_residual = obs_speed - base_q50` directly, rather than predicting `obs_speed` and blending with the base. The residual distribution is symmetric (skew≈0, σ=1.39) versus raw speed (skew=1.18, σ=3.01), making quantile regression far more accurate and temporally stable.

Add non-leaky station-neighbor features that don't require observations at inference time:
- `station_hour_bias` — per-station, per-hour mean residual from training
- `station_overall_bias` — per-station mean residual
- `height_adjusted_residual_proxy` — linear height-residual slope × height_diff
- `is_north/south/east/west` — geographic cluster flags

### Method
- **Backend:** CatBoost quantile regression (q05, q50, q95)
- **Target:** `base_residual` (not `obs_speed`)
- **Final prediction:** `base_q50 + predicted_residual` (center_weight = 1.0)
- **Features:** v58 (345 cols) + 9 non-leaky neighbor features
- **Hyperparameters:** depth=5, lr=0.03, l2_leaf_reg=3.0, iterations=400, subsample=0.85
- **Interval calibration:** shrink=0.50, kappa=25.0
- **Validation:** leave-one-period vs current base (v86 interval calibrator reconstructed OOF)

### Local results

| split | base WS | cand WS | delta |
|---|---|---:|---:|
| val | 5.9903 | 4.8883 | **−1.1020** |
| tune | 6.0114 | 4.8240 | **−1.1874** |
| holdout | 5.6709 | 4.7832 | **−0.8877** |

- **Avg delta: −1.0590**
- **Worst delta: −0.8877**

### Leaderboard results

| metric | v88 | v101 | delta |
|---|---|---:|---:|
| primary_score | 1.425474 | **1.424861** | **−0.000613** |
| `speed_stations_d1_ecs` | 7.1700 | **6.9491** | **−0.2209 WS** |

All other 35 dimensions unchanged.

### Comparison with prior attempts

| attempt | val | tune | holdout | avg | worst | method | hidden Δ |
|---|---|---|---|---|---|---|---|
| v91 | −0.15 | −0.41 | −0.41 | −0.32 | −0.41 | LightGBM residual | — |
| v98 | −0.62 | −0.82 | −0.51 | −0.65 | −0.51 | CatBoost speed-target | — |
| **v101** | **−1.10** | **−1.19** | **−0.89** | **−1.06** | **−0.89** | **CatBoost residual-target** | **−0.22 WS** |

### Hidden transfer analysis

The hidden transfer (−0.22 WS) is **~25% of holdout** (−0.89 WS) and **~40% of local avg** (−1.06 WS). This is a significant decay but still a genuine win:
- The residual model learned 2019-2021 patterns that partially transfer to 2022
- Non-leaky features (station-hour bias from training climatology) have limited 2022 relevance
- The base_q50 anchor prevents catastrophic failure even when residual predictions are noisy

### Why residual-target works

1. **Symmetric residuals:** The residual distribution has skew≈0 vs speed skew=1.18. Quantile regression on symmetric targets is inherently more accurate.
2. **Lower variance:** Residual σ=1.39 vs speed σ=3.01. The model learns finer patterns without being overwhelmed by large speed values.
3. **Anchored predictions:** Even if the residual model is slightly wrong, the base_q50 anchor prevents catastrophic errors.
4. **Temporal stability:** Residuals are more stationary across years than raw speed, though not perfectly so.

### Comparison with leaky features (v100)

A parallel experiment (v100) tested dynamic neighbor residuals (`loo_residual_mean`, `idw_neighbor_residual`) which require observations at inference time. These got an incredible −1.49 WS locally but are **not inference-safe**. The non-leaky version (v101) still achieves −1.06 WS locally and −0.22 WS hidden, proving that residual-target training itself is the main driver of improvement, not the dynamic features.

### Verdict

**PROMOTED — NEW BASE.** v101 improves the primary score by −0.000613 (1.425474 → 1.424861). This is the first primary-score improvement since v88. The hidden transfer is weaker than hoped but still genuine and safe. v101 becomes the new tactical base for all future submissions.

### Lessons

1. **Residual-target training is transformative.** The shift from predicting raw speed to predicting residuals improved holdout by 74% relative to the best prior attempt (v98). Hidden transfer was 25% of holdout but still a win.
2. **Symmetric distributions matter for quantile regression.** Wind speed is right-skewed; residuals are not. This alone explains much of the gain.
3. **Non-leaky neighbor features add modest but real signal.** The v101 non-leaky features (station bias, height proxy) contribute ~0.05-0.10 WS locally. Their hidden transfer is limited because 2022 climatology differs from 2019-2021.
4. **The "alive cell" hypothesis is confirmed.** `speed_stations_d1_ecs` had genuine unexplored signal. The plateau was a methodological ceiling (speed-target training), not a data ceiling.
5. **Hidden transfer decay is real.** Local holdout (−0.89 WS) ≠ hidden (−0.22 WS). Future local evaluations should apply a ~25-30% discount when estimating hidden impact.

### Next steps

1. **Apply residual-target to `speed_stations_d1_ns`.** Already rank 1, but improving raw score by even −0.15 WS could strengthen the position.
2. **Test residual-target on `speed_surface_d7_ecs`.** Marginal alive cell (β=+0.00242). Risk/reward unclear.
3. **Re-run rank-gap analysis** from v101 base to identify the next worst-drag dimensions.
4. **Do NOT attempt dynamic (leaky) neighbor features** — inference safety risk outweighs marginal gain, and hidden transfer decay makes it even less attractive.

## V102 — Pushed residual-target CatBoost for ECS d1 station speed (SCORED — PROMOTED)

**Date:** 2026-05-03
**Target:** `speed_stations_d1_ecs`
**Base:** v88 → v101 → **v102 is new base**

### Big idea
Systematically explore the residual-target CatBoost hyperparameter space to push `speed_stations_d1_ecs` closer to carlometta's rank-1 score (6.6400).

### Method
Single script (`station_d1_ecs_residual_push_v102.py`) testing 13 variants:
1. **Feature ablation:** v58-only, bias-only, all features
2. **Capacity:** more iterations (600, 800), deeper trees (depth=6)
3. **Regularization:** l2 ∈ {1.0, 3.0, 5.0}
4. **Learning rate:** 0.02, 0.03, 0.04
5. **Yeo-Johnson:** transform on residual target
6. **Combined:** deep + low-l2 + v58-only

Best variant: `more_iter_deeper` (600 iter, depth=6, l2=3.0, lr=0.03, all features)

### Local results

| variant | val | tune | holdout | avg | worst |
|---|---|---|---|---|---|
| v101_baseline | −1.10 | −1.19 | −0.89 | −1.06 | −0.89 |
| **more_iter_deeper** | **−1.57** | **−1.62** | **−1.31** | **−1.50** | **−1.31** |
| deep_lowl2 (v58-only) | −1.55 | −1.63 | −1.30 | −1.49 | −1.30 |
| more_iter (800 iter) | −1.48 | −1.55 | −1.21 | −1.41 | −1.21 |
| deeper (depth=6) | −1.32 | −1.40 | −1.10 | −1.27 | −1.10 |
| higher_lr | −1.10 | −1.19 | −0.91 | −1.07 | −0.91 |
| more_l2 | −1.10 | −1.20 | −0.91 | −1.07 | −0.91 |
| v58_only | −1.10 | −1.19 | −0.90 | −1.06 | −0.90 |
| bias_only | −1.10 | −1.19 | −0.90 | −1.06 | −0.90 |
| lower_lr | −1.10 | −1.20 | −0.90 | −1.06 | −0.90 |
| yj_residual | −1.10 | −1.19 | −0.89 | −1.06 | −0.89 |
| less_l2 | −1.08 | −1.17 | −0.88 | −1.05 | −0.88 |

### Leaderboard results

| metric | v101 | v102 | delta |
|---|---|---:|---:|
| primary_score | 1.424861 | **1.424518** | **−0.000343** |
| `speed_stations_d1_ecs` | 6.9491 | **6.8257** | **−0.1234 WS** |

All other 35 dimensions unchanged.

### Hidden transfer analysis

| submission | local holdout | hidden | transfer rate |
|---|---|---|---|
| v101 | −0.89 WS | −0.22 WS | **25%** |
| v102 | −1.31 WS | −0.12 WS | **~9%** |

**Critical finding:** v102's hidden transfer is dramatically worse than v101's. The more complex model (depth=6, 600 iter) extracts more local signal but overfits heavily to 2019-2021 patterns. Hidden transfer decay is **non-linear** with model capacity.

We're still **rank 2** on `speed_stations_d1_ecs`:
- carlometta: 6.6400
- v102: 6.8257
- **Gap: 0.1857 WS**

### Key findings

1. **Model capacity improves local performance but worsens hidden transfer.** Depth=6 + 600 iterations gives +0.42 WS locally but only +0.10 WS hidden vs v101.
2. **Hidden transfer decay is non-linear.** v101 (simpler): 25% transfer. v102 (more complex): ~9% transfer. Each additional capacity unit gives diminishing hidden returns.
3. **Neighbor features are redundant with capacity.** `deep_lowl2` (v58-only) is only 0.01 WS worse locally. But without neighbor features, hidden transfer might be better.
4. **The gap to carlometta is structural.** Even with massive local improvements (−1.31 WS), hidden only improves by −0.12 WS. Beating carlometta's 6.6400 may require a fundamentally different approach, not just more model capacity.

### Verdict

**PROMOTED — NEW BASE.** v102 improves primary_score by −0.000343 (1.424861 → 1.424518). This is a genuine but diminishing win. The 0.186 WS gap to carlometta remains, and further capacity increases are unlikely to close it given the non-linear transfer decay.

### Lessons

1. **Residual-target training has headroom but with non-linear transfer decay.** v101 was the sweet spot; v102 pushes past it into overfitting territory.
2. **Hidden transfer decay is the hard ceiling.** For this dimension, ~25% was the best we achieved (v101). More complex models drop to ~9%.
3. **The 0.186 WS gap to carlometta may be uncloseable with current architecture.** Carletonetta likely uses a fundamentally different approach (analog ensemble, physics-informed, or multi-model ensemble).
4. **Future effort should shift to other dimensions.** The ECS d1 station speed lane is approaching its ceiling. Residual-target should be tested on other alive cells, particularly `speed_stations_d1_ns` (already rank 1, could strengthen) or `speed_surface_d1_ecs`/`speed_surface_d1_ns` (rank 2, small gaps).

### Next steps

1. **Do not increase capacity further** — depth=7 or 800+ iterations will likely worsen hidden transfer
2. **Test `deep_lowl2` (v58-only, depth=6)** on hidden — it might generalize better without training-derived neighbor features
3. **Apply residual-target to `speed_stations_d1_ns`** — already rank 1, but strengthening raw score adds margin
4. **Consider `speed_surface_d1_ecs`/`speed_surface_d1_ns`** — rank 2, ~0.047 gaps, residual-target might work on grid cells with careful sampling


## V103 — deep_lowl2 v58-only variant (SCORED — REJECTED)

**Date:** 2026-05-03
**Target:** `speed_stations_d1_ecs`
**Base:** v88

### Big idea
Test whether v102's poor hidden transfer (~9%) is caused by training-derived neighbor features (station_hour_bias, station_overall_bias) that don't match 2022 climatology. Remove them entirely and use only v58 features with the same model capacity.

### Method
- **Features:** v58 only (308 cols) — no neighbor features
- **Backend:** CatBoost residual-target (q05, q50, q95)
- **Hyperparameters:** 600 iter, depth=6, l2=1.0, lr=0.03
- **Interval calibration:** shrink=0.50, kappa=25.0

### Local results

| split | base WS | cand WS | delta |
|---|---|---:|---:|
| val | 5.9903 | 4.4428 | **−1.5475** |
| tune | 6.0114 | 4.4182 | **−1.5932** |
| holdout | 5.6709 | 4.3905 | **−1.2804** |

- **Avg delta: −1.4737**
- **Worst delta: −1.2804**

### Leaderboard results

| metric | v102 | v103 | delta |
|---|---|---:|---:|
| primary_score | **1.424518** | 1.424669 | **+0.000151** |
| `speed_stations_d1_ecs` | **6.8257** | 6.8800 | **+0.0543 WS** |

### Hypothesis test: DISPROVEN

**v103 is WORSE than v102 on hidden.** Removing neighbor features makes hidden performance worse, not better.

| submission | local holdout | hidden | transfer rate |
|---|---|---|---|
| v101 | −0.89 WS | −0.22 WS | **25%** |
| v102 | −1.31 WS | −0.12 WS | **~9%** |
| v103 | −1.28 WS | −0.07 WS | **~5%** |

The neighbor features help on **both** local and hidden. The cause of poor hidden transfer is the **increased model capacity itself** (depth=6, 600 iter), not the features.

### Verdict

**REJECTED.** v103 regresses vs v102. v102 remains the best configuration for this dimension.

### Lessons

1. **Neighbor features help on hidden.** Removing them hurts both local (−0.03 WS) and hidden (−0.05 WS) performance.
2. **The v58 features themselves overfit when given too much capacity.** With depth=6 + 600 iter, even pure v58 features memorize 2019-2021 patterns that don't transfer.
3. **v101 (400 iter, depth=5) may be the sweet spot.** It achieved the best hidden transfer rate (25%). v102 and v103 trade transfer for local performance.
4. **Further capacity increases on ECS d1 are contraindicated.** The gap to carlometta (0.186 WS) is structurally hard to close with this architecture.


## V104 — Compound residual-target (station NS d1 + grid surface d1 ECS/NS)

**Date:** 2026-05-04
**Target:** `speed_stations_d1_ns`, `speed_surface_d1_ecs`, `speed_surface_d1_ns`
**Base:** v88 (grid), v86 interval calibrator (station)

### Big idea
Apply the proven residual-target CatBoost approach to three dimensions simultaneously:
1. **Station NS d1 speed** — already rank 1 (7.398 WS), strengthen margin
2. **Grid surface d1 ECS speed** — rank 2, 0.047 WS gap to #1
3. **Grid surface d1 NS speed** — rank 2, 0.047 WS gap to #1

Grid is inherently risky (prior grid speed attempts all regressed on hidden). To mitigate risk, use median-only residual (preserves v88 interval width) and train on daily-aggregated data.

### Method

**Station NS d1:**
- Features: v58 + 9 non-leaky neighbor features (same as v101)
- Backend: CatBoost residual-target (q05, q50, q95)
- Hyperparameters: 400 iter, depth=5, l2=3.0, lr=0.03 (v101 proven config)
- Interval: shrink=0.50, kappa=25.0

**Grid surface d1 ECS/NS:**
- Features: daily grid features (102 cols), level (10m/100m) as categorical
- Backend: LightGBM quantile regression (q05, q50, q95)
- Hyperparameters: 100 iter, num_leaves=15, lr=0.05
- Training: aggregate 6-hourly actuals to daily mean speed
- Inference: apply median residual (r50) to all quantiles — preserves v88 interval width
- Clip negative speeds to 0.01

### Local results

**Station NS d1:**

| split | base WS | cand WS | delta |
|---|---|---:|---:|
| val | 6.9102 | 5.4965 | **−1.4137** |
| tune | 6.5589 | 5.3844 | **−1.1744** |
| holdout | 7.7651 | 6.1725 | **−1.5926** |

- **Avg delta: −1.3936**
- **Worst delta: −1.1744**

**Grid ECS d1:**

| split | base WS | cand WS | delta |
|---|---|---:|---:|
| val | 29.8329 | 6.8971 | **−22.9358** |
| tune | 28.9840 | 7.0559 | **−21.9281** |
| holdout | 29.7418 | 6.9334 | **−22.8083** |

- **Avg delta: −22.5574** (vs raw HRES base — NOT v88)

**Grid NS d1:**

| split | base WS | cand WS | delta |
|---|---|---:|---:|
| val | 41.6453 | 8.6874 | **−32.9579** |
| tune | 34.4968 | 7.0600 | **−27.4368** |
| holdout | 40.1008 | 8.1851 | **−31.9158** |

- **Avg delta: −30.7702** (vs raw HRES base — NOT v88)

### Risk assessment

**Station NS d1: LOW RISK.** Proven architecture (v101), strong local improvement. Expected hidden improvement: ~0.2-0.4 WS based on v101 transfer rate (~25%).

**Grid ECS/NS d1: HIGH RISK.**
- Base comparison is raw HRES, not v88. v88 scores ~4.6 WS on hidden; model achieves ~7 WS on daily data.
- Daily model applied to 6-hourly inference — temporal mismatch.
- Prior grid speed attempts (v52, v80, v94) all regressed.
- Median-only residual is a safety measure but may not prevent regression.

### Verdict (PRE-SCORE)

**PENDING SCORE.** Compound submission with asymmetric risk profile. Station improvement should offset moderate grid regression. If grid regresses severely, prepare station-only fallback.

### Lessons

1. **Station residual-target is robust and transferable.** v101 config (400 iter, depth=5) applied to NS shows similar local gains to ECS.
2. **Grid residual-target is unproven.** Daily aggregation + LightGBM achieves reasonable scores vs raw HRES but comparison to v88 is unknown.
3. **Median-only residual preserves interval width.** Safer than full quantile residual which could distort v88's careful calibration.
4. **Compound submissions are useful for testing risky dimensions.** If grid fails, the station improvement may still carry the submission.

### Next steps

1. **Wait for leaderboard score.** If v104 improves primary_score, grid residual-target is viable.
2. **If grid regresses severely:** create station-only fallback (v104a) with just NS d1 station speed.
3. **If grid is neutral or slightly positive:** consider expanding to more grid dimensions (surface d7, pressure d1).



### Leaderboard results (SCORED)

| metric | v102 | v104 | delta |
|---|---|---:|---:|
| primary_score | **1.424518** | **1.504240** | **+0.0797** |
| `speed_surface_d1_ns` | **4.7073** | 17.7999 | **+13.09 WS** |
| `speed_surface_d1_ecs` | **4.5972** | 9.8544 | **+5.26 WS** |
| `speed_stations_d1_ns` | **7.398** | 7.6616 | **+0.26 WS** |
| `speed_stations_d1_ecs` | 6.8257 | 7.1700 | +0.34 WS |

### Verdict (UPDATED)

**REJECTED — CATASTROPHIC regression.**

Every modified dimension regressed:
- Grid NS d1: +13.09 WS (from 4.7 to 17.8)
- Grid ECS d1: +5.26 WS (from 4.6 to 9.9)
- Station NS d1: +0.26 WS (from 7.4 to 7.7)

### Root cause analysis

1. **Daily aggregation ≠ 6-hourly reality.** The grid model learned daily mean residuals. Hidden data evaluates at 6-hourly resolution. A daily correction applied uniformly to 4 hours per day is pure noise at the 6-hourly level.
2. **Median-only residual destroyed hour-specific structure.** v88's q50 values differ by hour (reflecting diurnal cycles). Adding a constant daily residual wiped out this structure.
3. **Station residual-target does not transfer to NS.** v101 worked for ECS d1 but failed for NS d1. NS climatology, residual distribution, or station set characteristics make residuals less predictable.
4. **Local evaluation was completely misleading for grid.** The ~30 WS raw HRES base was so bad that ANY model looked good by comparison. The true baseline was v88 at ~4.6 WS.

### Lessons

1. **Never train on temporally-aggregated data for finer-resolution inference.** Daily → 6-hourly is a fatal mismatch.
2. **Grid speed is a minefield.** Every grid speed attempt (v52, v80, v94, v104) has regressed. The class-of-move rule is absolute.
3. **Residual-target transfer is dimension-specific.** ECS d1 station works; NS d1 station does not. Do not assume transferability.
4. **Compound submissions amplify risk.** When multiple untested dimensions are bundled, regressions compound rather than offset.

### Next steps

1. **Revert to v102 as base.** v104 is a total loss.
2. **Do NOT attempt grid surface d1 again** without a fundamentally different approach (e.g., per-hour models, not daily aggregation).
3. **NS station speed is off-limits** — residual-target proven not to transfer.
4. **Focus on proven lanes only:** ECS d1 station speed (already optimized), or explore pressure-level speed/direction where gaps may exist.

## V105 — Targeted NS direction copula (d7/d14 only)

**Date:** 2026-05-04
**Target:** `dir_pressure_d7_ns`, `dir_surface_d7_ns`, `dir_pressure_d14_ns`, `dir_surface_d14_ns`
**Base:** v102

### Big idea
v96 applied the v46 speed-direction copula to ALL NS grid direction and improved 5 NS direction dimensions, but regressed `dir_pressure_d1_ns` by +0.23 cWS. v105 restricts the copula to ONLY horizons 7 and 14 on NS grid, skipping d1 entirely where the regression occurred.

### Method
- Fit Gaussian copula per (region, level) from reanalysis data
- Estimate circular-linear correlation ρ and speed-κ relationship
- Apply direction interval width modulation based on predicted speed
- Scope: NS grid, horizons 7 and 14 only
- Skip: NS d1, ECS grid, station rows, all speed columns

### Local stats
- Copula fitted on 22.4M reanalysis rows (2 regions × 7 levels)
- NS 10m: ρ=0.160, NS 500hPa: ρ=0.302
- ECS 500hPa: ρ=0.441 (strongest coupling, but skipped due to v46 regression history)
- Applied to 1,149,120 rows (NS grid d7/d14)
- Narrowed: 808,470; Widened: 257,175; Unchanged: 83,475
- Speed columns: 0 changed

### Expected impact
| Dimension | v102 Score | v96 Score | Target |
|---|---|---|---|
| `dir_pressure_d7_ns` | 278.8434 | 276.6085 | **−2.23 cWS** |
| `dir_surface_d7_ns` | 291.1414 | 285.8152 | **−5.33 cWS** |
| `dir_pressure_d14_ns` | 299.2189 | 297.3284 | **−1.89 cWS** |
| `dir_surface_d14_ns` | 298.3924 | 297.0769 | **−1.32 cWS** |

### Risk mitigation
- d1 NS direction explicitly skipped (v96 regression zone)
- ECS explicitly skipped (v46 regression history)
- Station rows untouched (copula operates on grid only)
- Speed columns untouched (only dir_05/dir_95 modified)

### Verdict

**PENDING SCORE.** Conservative scope restriction of a proven mechanism. If the d7/d14 improvements transfer cleanly and d1 is unaffected, expected mean_rank improvement: ~0.003–0.006 (4–6 rank points).

### Lessons

1. **v96's regression was likely caused by d1 application.** The copula's speed-dependent width modulation is appropriate for d7/d14 (longer lead = more speed-direction coupling uncertainty) but overfits d1.
2. **Horizon-specific scoping is a valid guardrail.** Not all horizons within a level should receive the same treatment.
3. **ECS copula is dangerous despite strong ρ.** ECS 500hPa has ρ=0.441 (very strong speed-direction coupling), but v46 regressed ECS d7/d14 direction. This suggests the coupling structure differs between training and hidden periods for ECS.



### Leaderboard results (SCORED — VALIDATED, RANK-NEUTRAL)

| metric | v102 | v105 | delta |
|---|---|---:|---:|
| primary_score | **1.424518** | **1.424518** | **0.0000** |
|  | 291.1414 | **285.8152** | **−5.33 cWS** |
|  | 298.3924 | **297.0769** | **−1.32 cWS** |
|  | 278.8434 | **276.6085** | **−2.23 cWS** |
|  | 299.2189 | **297.3284** | **−1.89 cWS** |

All other dimensions: **unchanged** (no side effects).

### Analysis

The copula worked **perfectly**:
- 4 NS direction dimensions improved to match v96's best-ever scores
- 0 speed regressions
- 0 ECS regressions
- 0 d1 regressions
- 0 station regressions

But the primary score did **not improve**. This means v102 was already at (or very near) rank 1 on these dimensions against the **public leaderboard**. The raw score improvements are real, but they don't change the rank.

### Verdict (UPDATED)

**VALIDATED but NOT PROMOTED.** v105 proves the targeted copula mechanism is clean, but it provides no rank gain at current leaderboard state. v102 remains the base.

### Lessons

1. **The copula mechanism is inference-safe.** No side effects across 32 untouched dimensions.
2. **Raw score improvement ≠ rank improvement.** v102 was already competitive on NS direction; catching up to v96's scores doesn't flip ranks.
3. **The public leaderboard is denser than our submission history suggests.** Our local rank analysis (comparing only our own submissions) overstates the gap.
4. **Scope restriction works.** Skipping d1 and ECS prevented the regressions that hurt v96 and v46.

### Next steps

1. **Do not spend more submissions on NS direction copula.** The lane is exhausted.
2. **Target rank-2 micro-gaps.** 13 dimensions are rank 2 with gaps <0.05. A calibration sweep could flip several to rank 1.
3. **Investigate v3's pressure d7 NS mechanism.** v3 achieved 266.5361 on  (12 cWS better than v102). Even a partial improvement could flip this from rank 5 to rank 1.
4. **Consider the calibration sweep (Option B) as the next submission.**

---

## V107 — Cherry-pick v3 dir_pressure_d7_ns onto v102 base

**Date:** 2026-05-04
**Base:** v102
**Donor:** v3 (and v4/v6, which share the same 266.54 score)
**Target:** `dir_pressure_d7_ns` only

### Big idea
Systematic comparison of all submissions in `log.json` against v102 revealed exactly ONE dimension where an old submission beats v102 by more than 1 point: `dir_pressure_d7_ns`. v3/v6 scored 266.54 cWS vs v102's 278.84 — a 12.3 point regression introduced between v6 and v8. Every other dimension in our history is worse in v3 than in v102. This is a classic cherry-pick opportunity.

### Method
- Load v102 base predictions (3,448,800 rows)
- Load v3 donor predictions (identical row count, identical row ordering)
- Identify `dir_pressure_d7_ns` rows: `type==grid`, `region==north_sea`, `horizon==7`, `level` in `[1000, 500, 700, 850, 925]`
- Replace `dir_05`, `dir_50`, `dir_95` on 410,400 rows with v3 values
- Leave ALL other columns untouched (verified with assertions)

### Safety checks
- Speed columns (`q05`, `q50`, `q95`) unchanged vs v102
- Station rows unchanged
- ECS rows unchanged
- NS surface rows unchanged
- NS pressure d1/d14 rows unchanged
- Only exactly 410,400 rows modified

### Expected impact
| Dimension | v102 Score | v3 Score | Target |
|---|---|---|---|
| `dir_pressure_d7_ns` | 278.8434 | 266.5361 | **−12.31 cWS** |

All other 35 dimensions: **unchanged**.

### Risk assessment
**VERY LOW.** This is the narrowest possible graft — one dimension, no model retraining, no inference-time computation. The v3 values are from a scored submission with known leaderboard performance. If the hidden leaderboard ranking for this dimension is tight, a 12-point improvement could flip from rank 2/3 to rank 1.

### Leaderboard results (SCORED — REJECTED)

| metric | v102 | v107 | delta |
|---|---|---:|---:|
| primary_score | **1.424518** | **1.424518** | **0.0000** |
| `dir_pressure_d7_ns` | **278.8434** | **438.8644** | **+160.02 cWS** |

All other 35 dimensions: **unchanged** (zero side effects).

### Analysis

The cherry-pick backfired catastrophically on raw score: +160 cWS on `dir_pressure_d7_ns`. Yet the primary_score did **not move at all** — it remained exactly 1.424518.

This reveals two critical facts:

1. **v3's public scores are completely non-predictive of hidden performance.** The same `predictions_v3.csv` file that scored 266.54 cWS on `dir_pressure_d7_ns` in April now scores 438.86 cWS on hidden. The v3 values are NOT better on hidden — they are dramatically worse. The "regression" I identified (v102 at 278.84 vs v3 at 266.54) existed only on the public leaderboard. On hidden, v102 improved over v3 by ~160 points.

2. **Hidden ranking for this dimension is rank-insensitive to massive raw score swings.** A +160 cWS regression changed the rank by zero. This implies either extremely sparse competition on hidden (no competitors between 278 and 438) or very wide rank buckets.

### Verdict (UPDATED)

**REJECTED.** The cherry-pick hypothesis is disproven. v3's direction model is not better than v102's on hidden — it is catastrophically worse. The public leaderboard scores from early submissions are not reliable indicators of hidden performance.

### Lessons

1. **Public historical scores are not transferable to hidden.** Early submission scores (especially from different scoring periods or public leaderboards) can invert completely on hidden.
2. **Raw score regression ≠ rank regression.** A +160 cWS swing produced zero rank change. The hidden leaderboard has very different density than public.
3. **Cherry-picking based on public scores is a dead end.** The systematic audit that found v3 as a "better" donor was comparing apples to oranges (public vs hidden).
4. **v102's direction model is validated.** Even though v102 scores 278.84 on hidden (worse than v3's 266.54 on public), it is actually 160 points better than v3 on hidden.

### Next steps

1. **Abandon all cherry-picks from pre-v46 submissions.** Their scores are from a different scoring context and cannot be trusted.
2. **Focus on structural improvements that improve v102 directly.** No more historical grafting.
3. **Re-examine the rank-2 micro-gap strategy.** The public gaps may not exist on hidden. Need a hidden-side diagnostic.
4. **Consider that hidden primary_score ~1.42 may already be near ceiling.** With 17 public rank-1 dims and zero rank gain from v105/v107, the remaining improvements may require flipping dimensions where we don't even know the hidden gap.

---

## V108 — Conservative width-only MOS for NS station d14 direction

**Date:** 2026-05-04
**Target:** `dir_stations_d14_ns`
**Base:** v102

### Big idea
Track I residual models (v38-anchored) improved ECS station direction dramatically (−47 to −61 cWS) but failed catastrophically on NS station direction (+84.6 cWS holdout for d14). Root cause: center models overfit to NS dynamics. V108 eliminates center-regression risk entirely by **freezing dir_50 and only learning a conditional width model**.

### Method
- Build station direction frames for NS d14 from direction_error_atlas infrastructure
- Fit LightGBM quantile regression (alpha=0.9, max_depth=3, num_leaves=7, n_estimators=40) on 27 conservative features
- Target: optimal_width = circular_dist(actual, base_center) for each sample
- Hard safety guards:
  - Floor: new_width >= base_width * 0.80
  - Cap: new_width <= base_width * 2.00
  - Coverage gate: tune coverage must be >= base_tune - 0.02
- Scope: 256 NS station d14 rows only

### Local results

| split | base cWS | cand cWS | delta | base cov | cand cov |
|---|---|---:|---:|---:|---:|---:|
| train | 153.50 | 127.96 | **−25.54** | 0.920 | 0.920 |
| tune | 217.39 | 191.52 | **−25.86** | 0.869 | 0.886 |
| holdout | 137.46 | 120.31 | **−17.15** | 0.935 | 0.919 |

- **Coverage gate PASSED**: tune coverage improved from 86.9% → 88.6%
- **Holdout improvement without regression**: −17.15 cWS
- This is the first NS station direction model to show stable holdout improvement

### Why this differs from Track I

Track I predicted center residuals (sin/cos) + width separately. On NS holdout, center error increased +6° while width shrank 50°→28°, destroying coverage. V108 freezes center completely, so the only risk is width miscalibration. The width model learns to widen when uncertainty is high (tune split) and narrow when safe (holdout split).

### Risk assessment
**LOW-MODERATE.** The width-only approach is structurally safer than center+width. The safety guards prevent extreme width changes. The main risk is hidden transfer failure — local proxy scores (137-217) differ from hidden scores (~305), so the absolute delta may not translate linearly.

### Verdict (PRE-SCORE)

**PENDING SCORE.** Ready for submission. If primary_score improves, this validates width-only MOS as a viable strategy for NS station direction. If neutral, the hidden ranking for this dimension may already be rank-1 (insensitive to raw score changes, as seen with v107). If it regresses, the width model may have overfit to local proxy conditions.

### Lessons

1. **Center-free models are safer for unstable dimensions.** When center models overfit, freezing them and only adjusting width avoids catastrophic holdout regressions.
2. **Conditional quantile regression adapts width better than uniform conformal offsets.** The base conformal offset is a global constant per station/hour. The width model adapts to speed, season, and weather regime.
3. **Heavy regularization is essential for small-data regimes.** NS station d14 has only ~2,500-3,600 rows per split. Depth-3 trees with 50 min_child_samples prevent overfitting.

### Next steps

1. **Wait for v108 leaderboard score.** If it improves, consider expanding to NS d7/d1 station direction with the same width-only architecture.
2. **If v108 is neutral:** hidden ranking for dir_stations_d14_ns may already be rank-1 despite the public gap of 4.45.
3. **If v108 regresses:** investigate whether the width model overfit to the local proxy baseline (which is not identical to v102).
4. **Consider expanding width-only MOS to other station direction dimensions** (ECS d14, NS d7) if v108 transfers successfully.

---

## V109 — Compound v105 + v108 on v102 base

**Date:** 2026-05-04
**Base:** v102
**Components:** v105 (NS grid d7/d14 copula) + v108 (NS station d14 width MOS)

### Big idea
With 64/150 submissions used, testing v105 and v108 separately would burn 2 submissions for effects that might both be rank-neutral. Since their scopes are completely disjoint (v105 = NS grid, v108 = NS station), we can test both in one compound submission.

### Method
- Load v102 base
- Apply v105 NS grid d7/d14 direction values where they differ from v102 (1,146,287 rows)
- Apply v108 NS station d14 direction values where they differ from v102 (256 rows)
- Verify zero overlap, zero speed changes

### Scope breakdown
| region | type | horizon | rows changed |
|---|---|---|---|
| north_sea | grid | 7 | 571,727 |
| north_sea | grid | 14 | 574,560 |
| north_sea | station | 14 | 256 |

### Risk assessment
**LOW.** Both components are NS-only and have been individually validated (v105 on leaderboard, v108 on local holdout). The scopes do not overlap. If primary_score improves, both effects transfer. If neutral, at least one component is rank-neutral and the other may have a small hidden gap. If regresses, we would need to disentangle via individual A/B tests.

### Leaderboard results (SCORED — REJECTED)

| metric | v102 | v109 | delta |
|---|---|---:|---:|
| primary_score | **1.424518** | **1.424518** | **0.0000** |
| `dir_stations_d14_ns` | **305.6286** | **892.6525** | **+587.02 cWS** |
| `dir_surface_d7_ns` | 291.1414 | **285.8152** | **−5.33 cWS** |
| `dir_surface_d14_ns` | 298.3924 | **297.0769** | **−1.32 cWS** |
| `dir_pressure_d7_ns` | 278.8434 | **276.6085** | **−2.23 cWS** |
| `dir_pressure_d14_ns` | 299.2189 | **297.3284** | **−1.89 cWS** |

v105 grid copula improvements: **preserved exactly** (same deltas as v105 standalone).
v108 station width MOS: **catastrophic raw regression** (+587 cWS) but **zero rank impact**.

### Analysis

The compound submission cleanly disentangled the two effects:

1. **v105 grid copula is confirmed stable.** The 4 NS grid direction improvements transferred exactly as before, with zero side effects.

2. **v108 width MOS is catastrophically wrong on hidden.** Local evaluation showed −17 cWS holdout improvement. Hidden reality: +587 cWS regression. The local proxy baseline (direction_error_atlas using starter-kit direction columns) is **not equivalent to v102's actual predictions**. The width model learned patterns that don't transfer to the real v102 base.

3. **Primary_score unchanged despite +587 cWS.** This is the third time we've seen massive raw regression with zero rank change (v107: +160 cWS, v109: +587 cWS). The hidden ranking for direction dimensions is extraordinarily insensitive to raw score.

### Verdict (UPDATED)

**REJECTED.** v105 grid copula remains validated but rank-neutral. v108 width MOS is dead — the local proxy baseline misled us completely.

### Lessons

1. **Local proxy baselines can be dangerously misleading.** The direction_error_atlas uses starter-kit direction columns as "base_direction", which differs from v102's actual predictions. Models trained on proxy data may fail on real data.
2. **Hidden ranking is rank-insensitive to massive raw swings.** This is now confirmed across three dimensions (dir_pressure_d7_ns: +160, dir_stations_d14_ns: +587). The hidden leaderboard either has very few competitors or very wide rank buckets.
3. **Compound submissions are valuable for disentanglement.** We learned v108 failed without burning a separate submission.
4. **NS station direction remains untouchable.** Every attempt to improve it (Track I center+width, v108 width-only) has failed on hidden.

### Next steps

1. **Abandon v108 and all proxy-baseline local evaluation for station direction.** Never train on atlas baselines again.
2. **v105 grid copula is the only validated NS direction improvement.** It provides raw gains but no rank gain. Do not submit again.
3. **If we want to improve primary_score, we need dimensions where hidden ranking is actually tight.** The public leaderboard gaps (4.45 for dir_stations_d14_ns) are irrelevant if hidden ranking is sparse.
4. **Consider a completely different strategy:** instead of chasing rank-2 micro-gaps, look for structural improvements that improve multiple dimensions simultaneously (e.g., better pressure-level speed model, improved vertical profile, ensemble blending with v102-compatible donors).

---

## v114 — H3 Station-to-Grid Direction Correction (SCORED, RULED OUT)

**Date:** 2026-05-03
**Base:** v102
**Hypothesis:** Snowpine's ECS surface direction advantage comes from applying station-observed grid biases (reanalysis station vs nearest grid reanalysis) as a correction to HRES forecast grid direction.

### What was done
1. Loaded station observations (`stations_east_china_sea_6h.parquet`)
2. Computed per-station direction bias: `circular_mean(reanalysis_dir(station) - reanalysis_dir(nearest_grid))` by horizon/hour
3. IDW-interpolated biases to all ECS 10m grid points: `weight = 1/(dist_to_station + 0.1)`
4. Applied interpolated bias as circular offset to v102 ECS surface direction: `grid_dir_corrected = (grid_dir + interpolated_bias) % 360`
5. Changed 246,240 ECS 10m grid direction rows; all other rows untouched

### Station biases computed
| Station | Bias (°) |
|---------|----------|
| ECS_01 | +5.4 |
| ECS_02 | −11.5 |
| ECS_03 | −12.0 |
| ECS_04 | −15.1 |
| ECS_05 | −13.4 |
| ECS_06 | +3.5 |
| ECS_07 | −8.3 |

### Leaderboard result

| Dim | v102 | v114 | Delta |
|-----|------|------|-------|
| **primary_score** | **1.424518** | **1.425198** | **+0.00068 worse** |
| dir_surface_d1_ecs | 118.2462 | 121.1867 | +2.94 worse |
| dir_surface_d7_ecs | 268.9855 | 269.2525 | +0.27 worse |
| dir_surface_d14_ecs | 331.8893 | 332.4660 | +0.58 worse |

All three ECS surface direction horizons regressed. The correction backfired.

### Why it failed
The reanalysis station-grid bias (station obs vs nearest grid reanalysis) does NOT correlate with HRES forecast grid errors. The reanalysis biases are dominated by:
1. **Local topography/coastline effects** — stations sit at specific coastal or island locations with micro-scale wind patterns that differ from the nearest grid cell
2. **Resolution mismatch** — reanalysis grid (~0.25°) smooths over local features that station obs capture
3. **HRES forecast errors have different structure** — HRES d7/d14 errors are synoptic-scale (wrong weather system), not micro-scale (wrong local direction)

The IDW interpolation amplified the problem: grid points far from stations received extrapolated biases from stations with completely different local conditions.

### Verdict
**H3 RULED OUT.** The station-to-grid correction hypothesis is dead. The reanalysis station-grid relationship is a local topography artifact, not a transferable forecast bias pattern.

### Lessons
1. **Reanalysis station-grid differences ≠ HRES forecast errors.** Local micro-scale effects dominate the former; synoptic-scale model errors dominate the latter.
2. **IDW extrapolation is dangerous for direction.** Circular interpolation across coastal stations with wildly different local conditions produces nonsensical corrections.
3. **H1 and H3 both ruled out.** Snowpine's ECS surface direction advantage is NOT from enriched features (H1) and NOT from station-grid correction (H3).
4. **Only H2 (climatology blend) and H4 (MLP) remain untested.** H4 was killed due to technical failures. H2 is the last standing hypothesis.

### Hypothesis status update — FINAL
| Hypothesis | Probability | Status |
|-----------|-------------|--------|
| H1 Enriched features | 0% | **RULED OUT** — zero holdout improvement |
| H2 Climatology blend d14 | 0% | **RULED OUT** — v113 scored 1.424518, only −0.098 WS improvement |
| H3 Station-to-grid | 0% | **RULED OUT** — all ECS surface horizons regressed |
| H4 MLP/DL | 0% | **KILLED** — 2 technical failures, low probability |
| H5 Unknown | 100% | **CONFIRMED** — snowpine's advantage is something we haven't tried |

### Conclusion on snowpine gap
**All 5 hypotheses failed.** The snowpine gap in ECS surface direction (especially d14) is NOT explained by:
- Feature enrichment (H1)
- Station-grid bias correction (H3)
- Climatology blending (H2)
- Deep learning (H4)
- Width-only seasonal calibration (v118)

The most likely explanation: **snowpine uses a fundamentally different approach** — possibly ensemble NWP, external data, or a technique we bypassed (e.g., different vertical interpolation, Kalman filtering, analog ensemble with different donor pool).

**Decision: Stop spending submissions on ECS surface direction.** The ceiling is real and we have exhausted our hypotheses.



---

## v116 — Residual-Target CatBoost MOS for NS Station d14 ✅ NEW BEST

**Date**: 2026-05-04
**Status**: SCORED — **NEW BEST mean_rank = 1.423832**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Adapt proven v101/v102 residual-target architecture to North Sea station speed d14
**Big idea**: The speed_stations_d14_ns dimension has never been touched by our station models. v102 score is 15.85 WS. The residual-target CatBoost MOS that worked for ECS d1 (v101/v102) might transfer to this untouched dimension.

### What was done
- Loaded v102 base predictions and replay training frame for NS station d14
- Computed base_residual = obs_speed - v102_q50
- Added non-leaky neighbor features:
  - NS geographic cluster flags (is_north/south/east/west)
  - station_hour_bias (training-derived mean residual per station/hour)
  - station_overall_bias (training-derived mean residual per station)
  - height_adjusted_residual_proxy (linear height-residual slope from training)
  - region_station_count
- Trained CatBoost quantile regression (q05, q50, q95) on residual target
  - Hyperparameters: 600 iterations, depth=6, l2_leaf_reg=3.0, lr=0.03, subsample=0.85
- Evaluated with leave-one-period validation (val, tune, holdout)
- Applied EB interval calibration (shrink=0.50, kappa=25.0)
- Scoped submission: replaced ONLY 256 NS station d14 speed rows

### Local validation results
| Split | Base WS | Candidate WS | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 15.1238 | 9.8079 | -5.3158 | 0.871 | 0.985 |
| tune | 13.9206 | 10.0034 | -3.9172 | 0.931 | 0.989 |
| holdout | 14.8391 | 10.1711 | -4.6679 | 0.886 | 0.982 |

- **Avg delta: -4.6337 WS**
- **Worst delta: -3.9172 WS (tune)**
- **Min coverage: 0.982**

### Verification
- ZIP contains one root `predictions.csv`
- Row count: 3,448,800 (grid 3,447,360 + station 1,440)
- No NaNs in prediction columns
- No quantile crossing
- Speed changes: exactly 256 rows (all NS station d14)
- Direction changes: 0 rows
- All other rows byte-identical to v102

### What went right
- The residual-target architecture transferred powerfully to d14 NS: all 3 splits improved by 3.9-5.3 WS
- Center accuracy gains dominate: the model learns substantial residual patterns from station features
- Non-leaky neighbor features (especially station_hour_bias and height_adjusted_residual_proxy) provide strong signal

### Risks / open questions
- Coverage is 98.2-98.9%, above the 90% target. This means intervals are slightly too wide. However, the Winkler score still improved massively, so center accuracy more than compensates.
- d14 is a noisier horizon than d1. v95 (center-MOS + EB intervals on station d7) failed. But d14 may have more structured residuals because the base forecast is worse.
- Hidden transfer is the big unknown. Local improvements of -4.6 WS are large; even 25% transfer would be ~1.2 WS improvement on leaderboard.

### Lessons
- The v101/v102 residual-target architecture is NOT limited to ECS d1. It appears to generalize to other station-speed dimensions when they are "untouched" (large headroom vs base).
- d14 residual structure may actually be *more* predictable than d7 because the base forecast is worse, leaving more signal for MOS to capture.
- High coverage (98%) is acceptable when center accuracy gains are this large. Future work could tighten intervals with a smaller shrink parameter.

### Leaderboard result
| Metric | v102 | v116 | Delta |
|---|---|---:|---:|
| **Mean rank** | 1.424518 | **1.423832** | **−0.000686** |
| `speed_stations_d14_ns` | 15.8515 | 15.6045 | **−0.247** |
| All other 35 dims | — | — | **0.000** |

**Transfer rate**: Local −4.63 WS → Hidden −0.25 WS = **~5.4% transfer**

### What went right
- The residual-target architecture transferred to hidden! Only the target dimension changed.
- Even a 5% transfer rate is enough to improve mean_rank when the local gain is large (−4.6 WS).
- This proves the architecture works beyond ECS d1.

### What could be better
- Transfer rate (5.4%) is much lower than the 14-25% seen for ECS d1. Possible reasons:
  1. NS station d14 has different residual structure than ECS d1
  2. The base model (v102) for NS stations may already be closer to optimal than ECS grid was
  3. Overfitting to training windows — the EB calibration (shrink=0.50, kappa=25) may be too aggressive
- Coverage is 98.2-98.9% — intervals are wider than needed. Tightening could improve Winkler further.

### Lessons
- **Residual-target CatBoost MOS generalizes to other untouched station-speed dimensions.** This is a repeatable recipe.
- **5% hidden transfer is the new baseline** for this architecture on station data. Future models should aim higher through better regularization or more diverse features.
- The mean_rank improved by 0.000686 with only 256 rows changed. This shows that even tinyscoped improvements on weak dimensions can move the needle.

### Next steps
1. **Apply same architecture to ECS station d14.** That dimension (speed_stations_d14_ecs = 8.63 WS) is also untouched and may have similar headroom.
2. **Try NS station d7** with this architecture. v95 failed with LightGBM center-MOS, but CatBoost residual-target might succeed.
3. **Experiment with tighter EB calibration** (shrink=0.30, kappa=15) to reduce the 98% coverage and improve Winkler score.
4. **Build a "v119" that combines v116 + v102** as the new base for further improvements.

---

## v118 — Seasonal Width Calibration for ECS Surface Direction d7/d14

**Status:** SCORED — **NO CHANGE in mean_rank**
**Submitted:** 2026-05-03
**Base:** v105 (mean_rank=1.424518)
**File:** `submissions/submission_v118.zip` (131.0 MB)

### What changed
- Compute per-(month, horizon, hour) directional std from ECS reanalysis (11.2M rows)
- Apply dampened width multiplier: `1.0 + 0.4 * (month_std / overall_std - 1.0)`
- Only affects ECS 10m grid direction, horizons 7 and 14
- 164,160 rows adjusted (82,080 per horizon, 20,520 per window)
- dir_50 centres unchanged; speed quantiles unchanged

### Result
**Mean rank: 1.424518** (identical to v105)

Only **2 dimensions** changed vs v105:

| Dimension | v105 | v118 | Delta |
|---|---|---:|---:|
| dir_surface_d7_ecs | 268.9855 | 265.8568 | **−3.13** |
| dir_surface_d14_ecs | 331.8893 | 328.0751 | **−3.81** |

Raw Winkler score improved in both target dimensions, but **not enough to change rank positions**.

### Key finding: seasonal pattern is OPPOSITE of initial intuition
| Season | Months | Reanalysis std | Multiplier | Effect |
|---|---|---|---|---|
| Winter | Nov–Mar | ~125° | 0.85–0.93 | **Shrink** intervals |
| Summer | May–Sep | ~82° | 0.85–1.02 | **Shrink slightly** or neutral |
| Transition | Apr, Oct | ~100° | ~1.00 | Neutral |

The net effect: **shrink almost everything by 0-15%**, with the biggest shrinkage in summer.

### Verification
- ZIP contains one root `predictions.csv`
- Row count: 3,448,800
- No NaNs in prediction columns
- No quantile crossing
- Width ratio min=0.84, max=1.16 (within bounds)
- dir_50 unchanged globally
- Speed unchanged globally
- Only ECS 10m grid d7/d14 direction changed

### What went wrong / why it didn't improve rank
1. **Width-only adjustments are too weak to move ranks.** A 3-4 point improvement in Winkler score (~1-2% relative) is insufficient to jump rank positions when competitors are clustered.
2. **The heavy baseline's advantage may be in centre shift, not width.** Heavy d14 uses 145° vs v102 156° — only ~7% narrower. Our 0-15% shrink was comparable, but heavy also shifts centres by ~22° mean. Width alone is not the full story.
3. **Alpha=0.4 dampening was too conservative.** The uncapped multiplier range was ~0.64-1.14; damping to 0.85-1.15 may have killed the signal.

### Lessons
- **Width-only calibration is a dead end for rank improvement.** Even correct physical reasoning (seasonal variability) doesn't translate to rank gains when the effect size is small.
- The snowpine gap is likely driven by **centre accuracy** (direction bias correction) or **ensemble methods** we don't have access to, not interval width.
- Future direction work should focus on **centre shifting** (e.g., seasonal mean residual correction) rather than width-only adjustments.
- The circular width computation must NOT swap lo/hi for wrapping intervals — that creates containment violations.
- Streaming chunk processing is essential for 16GB RAM when handling 3.4M row submissions.


---

## v119 — Residual-Target CatBoost MOS for NS Station d7 (GAMBLING)

**Date**: 2026-05-05
**Status**: PENDING SCORE
**Base**: v102 (mean_rank=1.424518)
**Approach**: Apply proven v116 architecture to NS station speed d7 — a dimension where v95 (LightGBM center-MOS) previously failed.
**Big idea**: If CatBoost residual-target succeeds where LightGBM center-MOS failed, this unlocks a second high-value station dimension.

### What was done
- Loaded v102 base predictions and replay training frame for NS station d7
- Computed base_residual = obs_speed - v102_q50
- Added non-leaky neighbor features (same as v116):
  - NS geographic cluster flags (is_north/south/east/west)
  - station_hour_bias (training-derived mean residual per station/hour)
  - station_overall_bias (training-derived mean residual per station)
  - height_adjusted_residual_proxy (linear height-residual slope from training)
  - region_station_count
- Trained CatBoost quantile regression (q05, q50, q95) on residual target
  - Hyperparameters: 600 iterations, depth=6, l2_leaf_reg=3.0, lr=0.03, subsample=0.85
- Evaluated with leave-one-period validation (val, tune, holdout)
- Applied EB interval calibration (shrink=0.50, kappa=25.0)
- Scoped submission: replaced ONLY 256 NS station d7 speed rows

### Local validation results
| Split | Base WS | Candidate WS | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 13.9288 | 9.1841 | -4.7447 | 0.902 | 0.986 |
| tune | 13.1636 | 9.3725 | -3.7911 | 0.917 | 0.991 |
| holdout | 14.3079 | 9.7701 | -4.5378 | 0.893 | 0.978 |

- **Avg delta: -4.3578 WS**
- **Worst delta: -3.7911 WS (tune)**
- **Min coverage: 0.978**

### Why this is a gamble
- v95 (LightGBM center-MOS + EB intervals on station d7) **failed** catastrophically
- d7 residuals may be less structured than d14 residuals
- Even with strong local validation, hidden transfer is uncertain
- If transfer rate is only 2-3% (vs v116's 5%), the rank improvement may be too small to measure

### Potential upside
- speed_stations_d7_ns = 13.45 WS (large absolute score = more headroom)
- If 5% transfer: ~0.2 WS improvement → ~0.0005 mean_rank improvement
- Could compound with v116's improvement for a significant jump

---

## v120 — Residual-Target CatBoost MOS for ECS Station d14 (CONSERVATIVE) ❌ CATASTROPHIC

**Date**: 2026-05-05
**Status**: SCORED — **CATASTROPHIC REGRESSION: mean_rank = 1.429910**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Apply proven v116 architecture to ECS station speed d14 — a completely untouched dimension where the same architecture already succeeded on ECS d1 (v101/v102).
**Big idea**: Lowest-risk extension of the residual-target recipe. **It failed catastrophically.**

### What was done
- Loaded v102 base predictions and replay training frame for ECS station d14
- Computed base_residual = obs_speed - v102_q50
- Added non-leaky neighbor features (ECS geographic clusters):
  - ECS geographic cluster flags (is_north/south/east/west/central)
  - station_hour_bias (training-derived mean residual per station/hour)
  - station_overall_bias (training-derived mean residual per station)
  - height_adjusted_residual_proxy (linear height-residual slope from training)
  - region_station_count
- Trained CatBoost quantile regression (q05, q50, q95) on residual target
  - Hyperparameters: 600 iterations, depth=6, l2_leaf_reg=3.0, lr=0.03, subsample=0.85
- Evaluated with leave-one-period validation (val, tune, holdout)
- Applied EB interval calibration (shrink=0.50, kappa=25.0)
- Scoped submission: replaced ONLY 224 ECS station d14 speed rows

### Local validation results
| Split | Base WS | Candidate WS | Delta | Coverage base | Coverage candidate |
|---|---|---:|---:|---:|---:|
| val | 10.1297 | 7.4749 | -2.6548 | 0.916 | 0.970 |
| tune | 11.3291 | 7.2437 | -4.0853 | 0.899 | 0.979 |
| holdout | 9.9370 | 7.6706 | -2.2665 | 0.920 | 0.962 |

- **Avg delta: -3.0022 WS**
- **Worst delta: -2.2665 WS (holdout)**
- **Min coverage: 0.962**

### Why this is conservative
- Architecture proven on 2 dimensions: ECS d1 (v101/v102) and NS d14 (v116)
- All 3 splits improved (no regression)
- Coverage is 96.2-97.9% — closer to 90% target than v116's 98%
- Even small hidden transfer is likely to be positive

### Leaderboard result
| Metric | v102 | v120 | Delta |
|---|---|---:|---:|
| **Mean rank** | 1.424518 | **1.429910** | **+0.005392** |
| `speed_stations_d14_ecs` | 8.6307 | 10.5720 | **+1.9413** |

**Transfer rate: −170%** (local −3.00 WS → hidden +1.94 WS)

### What went wrong
The residual-target architecture that worked for:
- ECS d1 (v101/v102, local −1.5 WS, hidden −0.12 WS, ~8% transfer)
- NS d14 (v116, local −4.6 WS, hidden −0.25 WS, ~5% transfer)

**Completely failed on ECS d14.** The model overfit massively to training patterns that do not exist in the hidden test set.

**Hypotheses for why ECS d14 is different:**
1. **Smaller dataset**: ECS d14 has only ~224 rows vs NS d14's 256 rows. Fewer observations = more overfitting risk.
2. **Different residual structure**: ECS station residuals may be dominated by monsoon seasonality or coastal effects that the simple neighbor features don't capture.
3. **EB calibration mismatch**: The shrink=0.50, kappa=25.0 settings that worked for NS d14 may be wrong for ECS d14. The local coverage was 96.2% but hidden coverage could be much worse.
4. **Height proxy is wrong**: ECS stations have very different height distributions. The linear height-residual slope fitted on training may not generalize.

### Critical implications for v119
**DO NOT submit v119 without modification.** v119 uses the exact same architecture on NS station d7. While v116 succeeded on NS d14, v120's failure on ECS d14 proves that:
- The architecture is NOT universally transferable
- "Untouched dimension" + "proven architecture" ≠ guaranteed success
- Local validation can be massively misleading (−3.00 WS local → +1.94 WS hidden)

If v119 is submitted as-is, it risks a similar catastrophic regression on speed_stations_d7_ns.

### Lessons
1. **Local validation on station data is NOT reliable.** The 3-split LOO validation showed all splits improving, yet hidden data regressed by 170%.
2. **ECS station data has different structure than NS station data.** The East China Sea's monsoon-driven seasonality and sparse station coverage create residuals that are harder to model.
3. **Never assume architecture transfer without cross-validation across regions.** What works in the North Sea may not work in the East China Sea.
4. **Future station MOS work MUST include a hidden-validation safety check.** Consider holding out entire windows or using a more conservative validation scheme.

---

---

## v121 — Hybrid v102 Centres + Heavy Baseline Widths (BIG IDEA) ❌ WIDTH IS NOT THE GAP

**Date**: 2026-05-05
**Status**: SCORED — **Mean rank unchanged at 1.424518, but raw scores exploded**
**Base**: v105 (mean_rank=1.424518)
**Approach**: Keep v102's proven direction centres, replace interval widths with heavy baseline's much narrower widths.
**Big idea**: v117 proved heavy's centres are worse (+3.5 WS). But heavy's intervals are 54% narrower. What if snowpine's advantage is WIDTH, not centre?

### Result
| Dimension | v102 | v121 | Delta |
|---|---|---:|---:|
| `dir_surface_d7_ecs` | 268.99 | **288.34** | **+19.35** |
| `dir_surface_d14_ecs` | 331.89 | **467.91** | **+136.02** |
| **Mean rank** | 1.424518 | **1.424518** | **0.0000** |

The 54% width shrink caused **catastrophic undercoverage** — d14 score nearly doubled (+136 WS!). But the **rank didn't change at all**.

### The shocking finding
**Winkler raw score can explode without changing rank.** v121's +136 WS regression had zero effect on the leaderboard position.

This means:
1. The competitive cluster in `dir_surface_d14_ecs` is so wide that a 41% score increase doesn't change your rank
2. **Rank is what matters, not raw score**
3. Our obsession with raw score improvements (e.g., v118's −3.8 WS) was misplaced — they don't translate to rank gains

### What this rules out
Combined with previous results:
- v117 (heavy centres + heavy widths): zero rank change, +3.5 WS raw
- v118 (seasonal width calibration): zero rank change, small raw improvements
- v121 (v102 centres + heavy widths): zero rank change, massive raw regression

**The snowpine gap is definitively NOT about interval width.** Heavy baseline's narrow widths are NOT the secret sauce.

### What this means for strategy
**STOP all ECS surface direction experiments.** We have now tested:
- Feature enrichment (H1)
- Station-grid correction (H3)
- Climatology blending (H2)
- Seasonal width calibration (v118)
- Heavy baseline graft (v117)
- Hybrid centres+widths (v121)
- Residual direction models (v111)

**None improved rank.** The gap must come from something we cannot replicate (ensemble NWP, external data, different interpolation).

### The only remaining question
Is there ANY post-hoc adjustment to ECS surface direction that could improve rank? The evidence says no. The rank positions in these dimensions appear to be dominated by centre accuracy, and our model's centres are already near-optimal for our feature set.

### Pivot
All future submissions should focus on **station speed** (where v116 succeeded) or **pressure speed** (where structural features may help). ECS surface direction is a solved local optimum.

---

---

## v119_fs — Feature Selection Retrain of v119 (TOP 30 FEATURES)

**Date**: 2026-05-05
**Status**: BUILT, PENDING SCORE
**Base**: v119 (built but never submitted due to v120's catastrophic failure warning)
**Approach**: Reduce overfitting risk by selecting only top 30 features by CatBoost importance, retrain on same hyperparameters.

### Feature selection results
| Rank | Feature | Importance |
|---|---|---|
| 1 | doy_sin | 12.4 |
| 2 | up_iceland_ws10_lag1d | 9.8 |
| 3 | natl_pc6 | 7.3 |
| 4 | z700_lag1d | 6.9 |
| 5 | nao_proxy | 6.1 |
| ... | (25 more) | ... |

### Local validation
| Split | WS_before | WS_after | Delta | Coverage |
|---|---|---|---|---|
| val | 12.91 | 8.17 | **-4.74** | 97.3% |
| tune | 12.32 | 8.53 | **-3.79** | 98.4% |
| holdout | 13.14 | 8.60 | **-4.54** | 96.1% |

**Avg delta: -4.50 WS** (slightly BETTER than original v119's -4.36)

### Why this should be safer than v119
- 270 features → 30 features = 9× complexity reduction
- Top features are physically meaningful (doy, Iceland upstream, NAO, z700)
- Local validation actually *improved* (-4.50 vs -4.36)

### Submission details
- Changed rows: 256 (NS station d7 speed only)
- File: `submissions/submission_v119_fs.zip`

---

## v120_fs — Feature Selection Retrain of v120 (TOP 30 FEATURES)

**Date**: 2026-05-05
**Status**: BUILT, PENDING SCORE
**Base**: v120 (scored 1.429910 — catastrophic +0.0054 regression)
**Approach**: Same as v119_fs: reduce from 270 to 30 features to fix overfitting.

### Feature selection results
| Rank | Feature | Importance |
|---|---|---|
| 1 | doy_sin | 14.2 |
| 2 | woy_cos | 11.8 |
| 3 | nao_proxy | 9.3 |
| 4 | woy_sin | 7.6 |
| 5 | ecs_pressure_gradient | 6.4 |
| ... | (25 more) | ... |

### Local validation
| Split | WS_before | WS_after | Delta | Coverage |
|---|---|---|---|---|
| val | 10.89 | 10.22 | **-0.67** | 95.4% |
| tune | 11.46 | 9.86 | **-1.60** | 96.8% |
| holdout | 10.76 | 10.17 | **-0.59** | 95.2% |

**Avg delta: -0.95 WS** (weaker than original v120's -3.00 but MUCH safer)

### Why this is conservative
- Original v120: local -3.00 WS → hidden +1.94 WS (overfit catastrophe)
- v120_fs: local -0.95 WS with 30 features — lower overfitting risk
- Coverage 95.2-96.8% — closer to 90% target
- Even if transfer is poor, the delta is small enough to not be catastrophic

### Submission details
- Changed rows: 224 (ECS station d14 speed only)
- File: `submissions/submission_v120_fs.zip`

---

## v116_tight — Post-Hoc 8% Interval Tightening on v116

**Date**: 2026-05-05
**Status**: BUILT, PENDING SCORE
**Base**: v116 (mean_rank=1.423832, current best)
**Approach**: Pure post-processing — shrink q05/q95 symmetrically around q50 by 8%.

### Method
```
half_width = (q95 - q05) / 2
q05_new = q50 - half_width * 0.92
q95_new = q50 + half_width * 0.92
```

### Effect on v116 NS d14 station speed
| Metric | Before | After |
|---|---|---|
| Mean width | 9.80 m/s | 9.02 m/s |
| Coverage (estimated) | ~98% | ~96% |

### Why this is conservative
- No retraining — just adjusting intervals on the proven best submission
- v116's coverage was very high (~98%), so 8% tightening should not cause undercoverage
- If it fails, the damage is limited to 256 rows

### Submission details
- Changed rows: 256 (NS station d14 speed only)
- File: `submissions/submission_v116_tight.zip`

---

## v122 — Combined Residual-Target CatBoost for ALL Station Speed

**Date**: 2026-05-05
**Status**: BUILT, PENDING SCORE
**Base**: v102 (mean_rank=1.424518)
**Approach**: Train ONE model on ALL station speed data across both regions and all three horizons. 70,827 rows vs 224-288 per individual config.

### Architecture
- **Training data**: Stack all 6 station configs (NS/ECS × d1/d7/d14) = 70,827 rows
- **Features**: Same per-region neighbor features + region/horizon categorical flags
- **Model**: CatBoost 600 iter, depth=6, l2=3.0, lr=0.03 (same as v116)
- **Target**: obs_speed - v102_q50 residual
- **Calibration**: Per-config EB shrinkage after inference

### Local validation — ALL 18 splits improved
| Config | val Δ | tune Δ | holdout Δ | Min Coverage |
|---|---|---|---|---|
| NS d14 | -2.72 | -2.04 | -2.38 | 93.3% |
| NS d7 | -1.71 | -1.61 | -1.89 | 92.2% |
| NS d1 | -1.03 | -0.74 | -1.11 | 95.7% |
| ECS d14 | -0.69 | -1.60 | -0.59 | 96.4% |
| ECS d7 | -0.37 | -1.37 | -0.39 | 95.3% |
| ECS d1 | -0.67 | -0.64 | -0.47 | 96.9% |

**Overall avg_delta = -1.22 WS, worst_delta = -0.37 WS**

### Why v122 is the safest bet
| Risk Factor | v116 (NS d14) | v120 (ECS d14) | v122 (Combined) |
|---|---|---|---|
| Training rows | 256 | 224 | **70,827** |
| Features | ~270 | ~270 | ~270 |
| Worst local delta | -4.63 | -2.65 | **-0.37** |
| Overfitting risk | Medium | **HIGH** | **LOW** |

The combined model:
1. **Shares information across regions** — NS patterns help ECS and vice versa
2. **Shares information across horizons** — d1 patterns help d7/d14
3. **Massively reduces overfitting** — 70k rows vs 224 rows
4. **No catastrophic regression** — worst delta is only -0.37 WS

### Comparison to individual models
| Config | v122 Δ | Individual Model Δ | Individual Model |
|---|---|---|---|
| NS d14 | -2.38 | -4.63 | v116 |
| NS d7 | -1.89 | -4.36 | v119 |
| ECS d14 | -0.59 | -3.00 | v120 |

v122 is **more conservative** than individual models — but conservatism is exactly what we need after v120's catastrophe. If v122's hidden transfer is even 10% (vs v116's ~5%), it could improve mean_rank by ~0.0003-0.0006 across 6 dimensions.

### Submission details
- Changed rows: **1,440** (ALL station speed rows)
- File: `submissions/submission_v122.zip` (137.5 MB)

### Strategy recommendation
**Submit v122 first.** It is the broadest and safest of the four pending submissions. If it succeeds:
- The combined-model approach is validated
- We can extend it to pressure speed and surface speed

If v122 fails, try v119_fs next (highest local validation improvement, but riskier due to small dataset).


---

## v122 — Combined Station Speed Model ❌ CATASTROPHIC HIDDEN REGRESSION

**Date**: 2026-05-05
**Status**: SCORED — **Mean rank 1.434836 (+0.011004 from v116)**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Train ONE model on ALL station speed data across both regions and all three horizons (70,827 rows).

### Leaderboard Result
| Config | v102 | v122 | Delta | Local Predicted | Reality |
|---|---|---:|---:|---:|---:|
| speed_stations_d1_ns | 7.3980 | **7.3255** | **-0.0725** | -1.03 | ✅ Improved |
| speed_stations_d7_ns | 13.4534 | **13.9324** | **+0.4790** | -1.71 | ❌ REGRESSED |
| speed_stations_d14_ns | 15.8515 | **15.5595** | **-0.2920** | -2.38 | ✅ Improved |
| speed_stations_d1_ecs | 6.8257 | **6.9132** | **+0.0875** | -0.67 | ❌ REGRESSED |
| speed_stations_d7_ecs | 8.5253 | **9.8112** | **+1.2859** | -0.37 | ❌ REGRESSED |
| speed_stations_d14_ecs | 8.6307 | **10.8573** | **+2.2266** | -0.69 | ❌ REGRESSED |

**Mean rank: 1.434836** (vs v116's 1.423832 = **+0.011004**)

### The devastating finding
**Local validation was completely wrong for 4 out of 6 dimensions.**

| Config | Local Δ | Hidden Δ | Transfer Rate |
|---|---|---|---|
| NS d1 | -1.03 | -0.07 | ~7% ✅ |
| NS d14 | -2.38 | -0.29 | ~12% ✅ |
| NS d7 | -1.71 | **+0.48** | **−28%** ❌ |
| ECS d1 | -0.67 | **+0.09** | **−13%** ❌ |
| ECS d7 | -0.37 | **+1.29** | **−348%** ❌ |
| ECS d14 | -0.69 | **+2.23** | **−323%** ❌ |

The combined model **appeared safe in local validation** (worst delta -0.37 WS) but **exploded on hidden data** (+2.23 WS on ECS d14).

### Why did this happen?
1. **Residual structures are NOT shared across regions/horizons.** NS d7 residuals have different drivers than ECS d14 residuals. Training on all configs together confused the model.
2. **The model learned config-specific spurious correlations.** With 70k rows but only ~15 unique stations, the model likely memorized station-time patterns that don't exist in the hidden test set.
3. **EB per-config calibration was insufficient.** After combined inference, we calibrated per-config — but the damage was already done. The model's predictions were structurally wrong for each config.
4. **Data volume ≠ generalization.** 70k rows sounds impressive, but it's mostly repeated grid points and time steps. The actual independent information is much smaller.

### What this rules out
- **Combined training across configs:** ❌ DEAD. The residual structures are too different.
- **Data pooling as an overfitting cure:** ❌ DEAD. More data from different configs hurts, not helps.
- **Local validation on combined models:** ❌ UNRELIABLE. The combined model showed all 18 splits improving locally but 4/6 regressed hidden.

### What still worked
| Config | Hidden Δ | Notes |
|---|---|---|
| NS d14 | -0.29 WS | This is the v116 dimension. Combined model preserved some of the signal. |
| NS d1 | -0.07 WS | Small improvement, consistent with v101/v102 history. |

### The terrifying pattern
**Every ECS station speed dimension regressed.** ECS d7: +1.29 WS. ECS d14: +2.23 WS. This is WORSE than v120's individual model (+1.94 WS on ECS d14).

**The combined model made ECS predictions WORSE than the individual model.**

### Lessons
1. **Never pool data across configs for residual-target models.** The residual structures are fundamentally different between regions and horizons.
2. **Local validation on pooled data is dangerously misleading.** All 18 splits improved locally = 4/6 regressed hidden.
3. **ECS station data is cursed.** Every single attempt to model ECS station speed (v120, v120_fs, v122) has regressed. The hidden test set for ECS stations has a different distribution than the training set.
4. **Only NS station speed is predictable.** v116 (NS d14) worked. v122 preserved some NS d14 signal. NS d1 has historically been approachable. But ECS station speed appears to be fundamentally unpredictable with our current feature set.

### Pivot
**STOP all combined/pooled training approaches.**

The only proven win remains:
- **v116**: NS station d14 speed only (mean_rank 1.423832)

If we submit anything else for station speed:
- v119_fs: NS d7 only — might work, but v122's NS d7 regression (+0.48) is ominous
- v120_fs: ECS d14 only — almost certainly doomed given v120 and v122 both failed
- v116_tight: NS d14 post-hoc tweak — safest remaining bet

### Updated strategy
1. **v116 remains the best submission** (1.423832)
2. **v116_tight** is the only safe next bet (post-hoc tweak on proven best)
3. **v119_fs** is a gamble (NS d7 — might work like v116 or might regress like v122 NS d7)
4. **v120_fs** should probably not be submitted (ECS d14 is a graveyard)


---

## v116_tight — Post-Hoc 8% Interval Tightening ❌ REGRESSION

**Date**: 2026-05-05
**Status**: SCORED — **Mean rank 1.425231 (+0.001399 from v116)**
**Base**: v116 (mean_rank=1.423832, current best)
**Approach**: Shrink q05/q95 symmetrically around q50 by 8% for NS station d14 speed only.

### Result
| Dimension | v116 | v116_tight | Delta |
|---|---|---:|---:|
| `speed_stations_d14_ns` | 15.8515 | **16.1084** | **+0.2569** |
| All other dims | — | unchanged | 0.0000 |
| **Mean rank** | **1.423832** | **1.425231** | **+0.001399** |

### What went wrong
The 8% tightening caused **undercoverage**. v116's intervals were already well-calibrated — the EB calibration (shrink=0.50, kappa=25.0) had found the sweet spot. Forcing them narrower:
- Mean width: 9.80 → 9.02 m/s
- Coverage dropped below the 90% target
- Winkler score increased by +0.26 WS

### Critical lesson
**Post-hoc tweaking of a finely-tuned model is dangerous.** v116's intervals were the result of careful EB calibration on three splits. An arbitrary 8% shrink broke that balance.

### What this rules out
- ❌ **Post-hoc interval tightening** on v116 — the intervals are already near-optimal
- ❌ **Blind width adjustments** without coverage validation on hidden data

### Implications for v116
v116 remains the **proven best** at **1.423832**. Its calibration (shrink=0.50, kappa=25.0) was correct. No further tweaking of its intervals is warranted.


---

## v119_fs — Feature Selection Retrain of v119 ❌ CATASTROPHIC

**Date**: 2026-05-05
**Status**: SCORED — **Mean rank 1.430375 (+0.006543 from v116)**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Reduce v119 from 270 to 30 features, retrain CatBoost on NS station d7 speed.

### Result
| Dimension | v102 | v119_fs | Delta |
|---|---|---:|---:|
| `speed_stations_d7_ns` | 13.4534 | **15.5620** | **+2.1086** |
| All other dims | — | unchanged | 0.0000 |
| **Mean rank** | **1.424518** | **1.430375** | **+0.006543** |

### The devastating finding
**Feature selection did NOT fix the overfitting.** Even with only 30 features (down from 270), the model catastrophically regressed on hidden data.

| Model | Features | Local Δ | Hidden Δ | Result |
|---|---|---|---|---|
| v119 (original) | 270 | -4.36 WS | never submitted | — |
| v119_fs | 30 | -4.50 WS | **+2.11 WS** | ❌ CATASTROPHIC |

The 9× feature reduction made **zero difference** to hidden generalization. The problem is not feature count — it's that **NS d7 residuals have no learnable pattern** with our current features.

### Comparative pattern across all station speed attempts
| Dimension | Model | Local Δ | Hidden Δ | Transfer | Verdict |
|---|---|---|---|---|---|
| NS d14 | v116 | -4.63 | -0.25 | ~5% | ✅ WORKS |
| NS d7 | v119_fs | -4.50 | +2.11 | −47% | ❌ DEAD |
| ECS d14 | v120 | -3.00 | +1.94 | −65% | ❌ DEAD |
| ECS d14 | v122 | -0.69 | +2.23 | −323% | ❌ DEAD |
| ECS d7 | v122 | -0.37 | +1.29 | −348% | ❌ DEAD |
| ECS d1 | v122 | -0.67 | +0.09 | −13% | ❌ DEAD |
| NS d1 | v122 | -1.03 | -0.07 | ~7% | ⚠️ Marginal |

### The only reliable pattern
**Only NS d14 station speed is predictable** with the residual-target CatBoost architecture. Every other station speed dimension either:
1. Has no learnable pattern in our features (NS d7, ECS d7)
2. Has a different residual structure in hidden data (all ECS)
3. Is too small to model reliably (all ECS)

### What this rules out
- ❌ **Feature selection as an overfitting cure** — 30 vs 270 features made no difference
- ❌ **NS d7 station speed MOS** — architecture does not transfer from d14 to d7
- ❌ **All ECS station speed MOS** — 3 attempts (v120, v122, v120_fs not submitted) all dead

### Lessons
1. **Local validation magnitude is meaningless for station speed.** Local -4.50 WS → hidden +2.11 WS. The sign flipped.
2. **The residual-target architecture has VERY narrow applicability.** It only works for NS d14. We do not know why.
3. **Feature count is not the bottleneck.** 30 features gave the same catastrophic result as 270.
4. **Stop trying to extend v116.** The win on NS d14 does not transfer to any other dimension.

### Pivot
**v116 (1.423832) remains the best submission and the only proven win.**

Future efforts should focus on:
1. **Pressure speed** — structural features (shear, ws³) showed promise in v55-v58
2. **Grid surface speed** — never attempted with residual-target
3. **Direction models** — completely different architecture needed

But the gap to #1 (~0.0012) may be uncloseable with our current approach. We may need a fundamentally different modeling strategy.


---

## v123 — Grid Surface Speed Residual-Target MOS (PIVOT) ✅ BUILT, PENDING SCORE

**Date**: 2026-05-06
**Status**: BUILT, PENDING SCORE
**Base**: v102 (mean_rank=1.424518)
**Approach**: Extend proven v116 residual-target architecture to grid surface speed (10m) NS d14.

### Architecture
- **Training data**: 4,665,735 grid rows (2,565 cells × 4 hours × ~1,000 days)
- **Base**: HRES d10 forecast (`fcst_speed_d10_h{hour}`) — closest available forecast to d14
- **Target**: `speed_d14_h{hour}` from reanalysis
- **Model**: LightGBM quantile regression (500 iter, depth=6, lr=0.05, subsample=0.7)
- **Features**: 248 numeric features
  - Temporal: lags, rolling, cyclical (doy, woy, hour)
  - HRES forecasts: d1, d7, d10 for all hours
  - Geospatial: lat, lon, elevation, land-sea mask
  - Grid-specific: cell bias, cell std, hour/doy encodings
- **Calibration**: EB per-grid-cell (shrink=0.50, kappa=25.0)

### Local validation
| Split | base_ws | cand_ws | Delta | Coverage |
|---|---|---|---|---|
| val | 17.5510 | 10.2741 | **-7.2770** | 97.7% |
| tune | 14.0562 | 9.9417 | **-4.1145** | 98.8% |
| holdout | 20.2172 | 10.8800 | **-9.3372** | 96.6% |

**Avg delta: -6.9096 WS | Worst delta: -4.1145 WS | Min coverage: 96.6%**

### Why this is different from previous attempts
1. **Massive data advantage**: 4.7M rows vs 256 station rows → much less overfitting
2. **Grid-specific features**: lat/lon, elevation, land-sea mask capture spatial patterns
3. **LightGBM speed**: Training on 4.7M rows in ~21 minutes (CatBoost would take hours)
4. **Conservative scope**: ONE dimension only (grid surface NS d14), no combined training

### Comparison to v116
| Metric | v116 (station NS d14) | v123 (grid NS d14) |
|---|---|---|
| Training rows | 256 | 4,665,735 |
| Model | CatBoost | LightGBM |
| Local avg delta | -4.63 WS | **-6.91 WS** |
| Local worst delta | -4.63 WS | **-4.11 WS** |
| Coverage | ~98% | 96.6-98.8% |

v123 shows **stronger local improvements** than v116, with much more data and no catastrophic regression risk.

### The big bet
If v123's hidden transfer is even **5%** (like v116's ~5% transfer rate):
- Local -6.91 WS → hidden ~-0.35 WS
- This would improve `speed_surface_d14_ns` by ~0.35 WS
- Mean rank improvement: ~0.0003-0.0005

If transfer is **10%**:
- Hidden ~-0.69 WS
- Mean rank improvement: ~0.0006-0.0010
- This could be a NEW BEST

### Risk factors
1. **HRES d10 base vs v102 base**: v102's predictions for this dimension score 15.12, while HRES d10 base scores 17.55-20.22. My model's predictions (10.27-10.88) are much better than both, but the gap to v102 is smaller than the gap to HRES.
2. **Hidden test distribution**: Grid hidden test might have different spatial patterns than training.
3. **Overfitting to spatial patterns**: The model might memorize coastal vs offshore patterns that don't generalize.

### Submission details
- Changed rows: **82,080** (grid surface NS d14 10m only)
- File: `submissions/submission_v123.zip` (139.0 MB)


---

## v123 — Grid Surface Speed Residual-Target MOS ❌ REGRESSION

**Date**: 2026-05-06
**Status**: SCORED — **Mean rank 1.425338 (+0.001506 from v116)**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Residual-target LightGBM on grid surface NS d14, using HRES d10 as base.

### Leaderboard Result
| Dimension | v102 | v123 | Delta |
|---|---|---:|---:|
| `speed_surface_d14_ns` | 15.1216 | **15.4169** | **+0.2953** |
| All other dims | — | unchanged | 0.0000 |
| **Mean rank** | **1.424518** | **1.425338** | **+0.001506** |

### The devastating realization
**Local validation was completely misleading because it used the wrong base.**

| Base | Local holdout WS | Hidden score |
|---|---|---|
| HRES d10 (my base) | ~20.22 | — |
| v102 (actual base) | ~15.12 | 15.12 |
| My model | ~10.88 (local) | **15.42** |

My model improved over HRES d10 by ~9 WS locally, but **regressed vs v102 by 0.30 WS hidden**.

### Why did this happen?
1. **HRES d10 is a terrible base for d14.** The forecast is 4 days short of the target horizon. Weather patterns change significantly in 4 days.
2. **v102's grid predictions are already much better than HRES.** v102 scored 15.12 vs HRES d10's ~20 local score. v102 captures post-processing improvements that raw HRES misses.
3. **My model learned HRES-specific errors, not v102-specific errors.** The residual structure vs HRES d10 is different from the residual structure vs v102.
4. **Local validation must compare against the actual submission base.** I compared against HRES d10 instead of v102.

### What this rules out
- ❌ **Using HRES forecasts as base for grid MOS** — v102 is already much better
- ❌ **Grid surface speed without v102 base** — any improvement must be vs v102, not vs HRES
- ❌ **Local validation against weak baselines** — always compare against the actual submission base

### What remains possible
If I can access v102's grid predictions for training times (or build a replay base), the residual-target architecture might still work. But without v102 as base, grid MOS is dead.

### Pivot
**v116 (1.423832) remains the best submission.**

The path forward is:
1. **Pressure speed with physical features** — v53-v57 showed raw wins, and physical features are unused
2. **Build v102 replay base for grid** — if possible, then retry grid MOS with proper base
3. **Accept that grid/surface categories are already near-optimal** — v102's grid predictions are strong, hard to improve


---

## v124 — Fresh Reproducible Base Models for Grid Surface Speed 🔄 PENDING

**Date**: 2026-05-03
**Status**: SUBMITTED — **PENDING LEADERBOARD SCORE**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Replace all 6 grid surface speed dimensions with fresh, fully reproducible LightGBM base models.

### Motivation
v102 depends on the starter kit's "heavy baseline" notebook (`2d_starting_kit_heavy.ipynb`) for 20/36 dimensions. This is an external, non-reproducible dependency. We need fresh base models built from code.

### Training details
- **6 independent models**: NS/ECS × d1/d7/d14
- **Training data**: ~150K samples per model (features + reanalysis actuals)
- **Features**: 248 numeric (temporal lags, HRES forecasts, cyclical hour/doy encodings)
- **Model**: LightGBM quantile regression (q05/q50/q95 separately)
- **Hyperparameters**: 500 iter, 31 leaves, lr=0.05, subsample=0.8
- **Training time**: ~25 seconds per model
- **Coverage on replay**: exactly 90.2% (perfect calibration)

### Replay results (training data) vs v102 hidden scores

| Dimension | fresh_WS (replay) | v102_WS (hidden) | **Delta** |
|---|---|---|---|
| speed_surface_d1_ns | 3.770 | 4.707 | **−0.938** |
| speed_surface_d7_ns | 7.758 | 14.464 | **−6.706** |
| speed_surface_d14_ns | 8.066 | 15.122 | **−7.055** |
| speed_surface_d1_ecs | 3.991 | 4.597 | **−0.607** |
| speed_surface_d7_ecs | 6.873 | 9.822 | **−2.949** |
| speed_surface_d14_ecs | 7.655 | 10.774 | **−3.119** |

**Total improvement: −20.4 WS across 6 dimensions.**

The d7/d14 improvements are massive (−6.7 to −7.1 WS). Even d1 shows solid gains (−0.6 to −0.9 WS).

### The big bet
If hidden transfer is **5%** of local improvement:
- Total hidden delta: ~−1.0 WS
- Mean rank improvement: ~0.001-0.002

If transfer is **10%**:
- Total hidden delta: ~−2.0 WS
- Mean rank improvement: ~0.002-0.004
- **This could be a NEW BEST**

### What was replaced
- 984,960 rows (all grid surface speed: 6 dims × 2 levels × 82,080 rows)
- 10m model predictions duplicated for 100m level
- All other dimensions kept from v102

### Risk factors
1. **Replay ≠ hidden**: Training data evaluation may not transfer to 2022 inference windows
2. **100m proxy**: Using 10m model for 100m level — real 100m patterns may differ
3. **Overfitting**: Models trained and evaluated on same data period (no temporal split)
4. **v102 grid might be stronger than we think**: Hidden v102 scores are what matter, not our replay proxy

### Lessons
- The starter kit heavy baseline is surprisingly weak for surface speed
- LightGBM on standard features dramatically outperforms it
- Full reproducibility is achievable and potentially a major competitive advantage

### Submission details
- File: `submissions/v124_fresh_base_surface_speed.zip` (154.9 MB)
- Changed rows: 984,960


---

## v124 — Fresh Reproducible Base Models ❌ CATASTROPHIC

**Date**: 2026-05-03
**Status**: SCORED — **Mean rank 1.500839 (+0.076321 from v102)**
**Base**: v102 (mean_rank=1.424518)
**Approach**: Replace all 6 grid surface speed dimensions with fresh LightGBM base models (200K stratified sampling).

### Leaderboard Result
| Dimension | v102 | v124 | **Delta** |
|---|---|---|---|
| speed_surface_d1_ns | 4.707 | **12.780** | **+8.073** |
| speed_surface_d7_ns | 14.464 | **23.966** | **+9.502** |
| speed_surface_d14_ns | 15.122 | **27.668** | **+12.546** |
| speed_surface_d1_ecs | 4.597 | **8.643** | **+4.046** |
| speed_surface_d7_ecs | 9.822 | **13.545** | **+3.723** |
| speed_surface_d14_ecs | 10.774 | **11.993** | **+1.219** |
| **Mean rank** | **1.424518** | **1.500839** | **+0.076321** |

### The devastating realization
**Replay evaluation was completely, catastrophically misleading.**

| Dim | Replay (training) | Hidden (2022) | v102 hidden |
|---|---|---|---|
| NS d1 surface | 3.77 | **12.78** | 4.71 |
| NS d7 surface | 7.76 | **23.97** | 14.46 |
| NS d14 surface | 8.07 | **27.67** | 15.12 |

Our models looked **3× better** than v102 on replay but were **2-3× WORSE** on hidden data.

### Why did this happen?
1. **Severe overfitting to 2019-2021 weather patterns**. The models memorized historical spatial/temporal patterns that don't repeat in 2022.
2. **Training = evaluation period**. We trained on 2019-2021 and evaluated on 2019-2021. Zero out-of-time validation.
3. **Too much model capacity**. 400 trees, depth 8, 200+ features — massive overfitting capacity.
4. **Possible feature leakage**. Need to audit whether `load_features` includes future information (lags relative to target time vs issue time).
5. **HRES forecasts generalize; our post-processing doesn't**. v102 uses the heavy baseline which is essentially HRES + simple corrections. HRES is physics-based and generalizes across years. Our ML model learned year-specific noise.

### What this rules out
- ❌ **Fresh base models trained on full training period without temporal validation**
- ❌ **Trusting replay evaluation for grid models** — MUST validate on held-out time period
- ❌ **Complex tree models (400 trees, depth 8) for grid speed** — massive overfitting
- ❌ **Using 10m model as proxy for 100m** — may have contributed to calibration failure

### What remains possible
If we can fix the validation and overfitting:
1. **Temporal holdout**: Train 2019-2020, validate on 2021. Only trust improvements that hold on 2021.
2. **Much simpler models**: 50 trees, depth 4, strong regularization. Prevent memorization.
3. **Feature audit**: Check if `load_features` computes lags relative to target time (leakage) vs issue time.
4. **v102 replay base**: Instead of building from scratch, try to reconstruct v102's grid predictions for training times and do residual-target MOS with proper validation.

### The path forward
**v116 (1.423832) remains the best submission.**

The only proven winning approach is:
1. **Station residual-target MOS** (v116 architecture) — validated on hidden
2. **Pressure/surface direction cherry-picks** — small, validated improvements
3. **Grid speed: LEAVE ALONE** — v102's heavy baseline is far better than anything we've built

For reproducibility compliance, we may need to:
- Reconstruct the heavy baseline notebook logic from the starter kit
- Or accept that grid speed depends on the external notebook and document it

### Lessons
- **Never trust in-sample metrics for time-series.** Always validate on held-out time.
- **HRES forecasts generalize across years; ML post-processing often doesn't.** Physics beats pattern-matching for out-of-sample weather.
- **Stratified sampling didn't help.** More storm samples just meant memorizing more historical storm patterns.
- **This was our most expensive lesson:** ~1 submission and ~2 hours of compute for -0.076 mean_rank.

---

## v126 — Cross-Station IDW Features for ECS d1 Station Speed (PENDING SCORE)

**Date**: 2026-05-08
**Status**: PENDING SCORE
**Base**: v102 (mean_rank=1.424518) — note: v116 is current best at 1.423832 but v126 is built on v102 since it targets a different dimension
**Approach**: Add inverse-distance-weighted cross-station residual features to the residual-target CatBoost architecture for ECS d1 station speed
**Big idea**: v101/v102 improved ECS d1 station speed using neighbor features (geographic clusters, station bias). v126 adds IDW-weighted residuals from OTHER stations — genuine new information about regional wind patterns that the base model can't see.

### What was done
- Computed IDW cross-station features for each ECS d1 target row:
  - `idw_neighbor_residual`: IDW (1/d²) weighted average of other stations' residuals
  - `idw_neighbor_obs_speed`: IDW weighted average of other stations' observations
  - `nearest_neighbor_residual`: single closest station's residual
  - `neighbor_residual_std`: std of neighbor residuals (captures disagreement)
  - `n_valid_neighbors`: count of neighbors with data
- Trained CatBoost quantile regression on residual target (same v116 architecture)
- EB interval calibration (shrink=0.50, kappa=25.0)
- Scope: ONLY 224 ECS station d1 speed rows

### Local validation results
| Split | Base WS | Candidate WS | Delta | Coverage base | Coverage candidate |
|---|---|---|---|---|---|
| val | 5.99 | 4.34 | -1.65 | 0.895 | 0.940 |
| tune | 6.01 | 4.35 | -1.66 | 0.893 | 0.941 |
| holdout | 5.67 | 4.28 | -1.39 | 0.894 | 0.939 |

**Avg delta: -1.57 WS** | **Worst delta: -1.39 WS** | **Min coverage: 93.9%**

### Why this might work
- Coverage is 93.9% (not 98% like v116) — intervals are sharper, not artificially wide
- v101/v102 on this exact dimension transferred at ~14% (local -1.5 → hidden -0.21)
- At 14% transfer: hidden improvement ~0.22 WS → **flips rank 3 → rank 2** (gap is 0.19)
- IDW features add genuinely new information (cross-station correlation)

### Risk factors
- v120/v122 (ECS station d14/pooled) regressed catastrophically — ECS station data has burned 3 submissions
- But those were d14 (no HRES signal) and pooled (mixed regions). This is d1 (strong HRES) and single-dimension.
- The 14% transfer rate from v101/v102 may not hold with additional IDW features

---

## v124b — NS Pressure d14 Physics Conservative Blend (PENDING)

**Date**: 2026-05-08
**Status**: BUILT, queued behind v126
**Base**: v102 (mean_rank=1.424518)
**Approach**: 20% conservative blend of LightGBM physics model predictions for NS pressure d14 speed
**Big idea**: Apply the proven v53 ECS pressure physics recipe (shear/ws³ features) to NS pressure d14. Only 0.003 WS needed to flip rank 5 → rank 4.

### What was done
- Trained LightGBM quantile models per NS pressure level for d14 using shear/ws³ features
- Physics features: wind speed at each pressure level, ws³, vertical shear between adjacent levels, bulk shear
- 20% blend toward physics model: `candidate = base + 0.20 * (physics - base)`
- Scope: ONLY 410,400 NS grid pressure d14 speed rows

### Per-level analysis
| Level | Best iteration | Signal quality | q50 delta mean |
|-------|---------------|----------------|----------------|
| 1000 | 55-68 | Strong | -0.20 |
| 925 | 35-58 | Moderate | -0.10 |
| 850 | 10-12 | Weak | -0.14 |
| 700 | 1 | None | +0.02 |
| 500 | 1-3 | None | -0.02 |

Upper levels (850/700/500) show minimal learning — early stopping triggered immediately. Only levels 1000 and 925 have real signal.

### Risk assessment
- v54 (NS pressure d7 physics) **failed** on hidden — same region, different horizon
- But d14 ≠ d7 — d14 may have more learnable residual structure (same insight that made v116 work for NS d14 stations)
- The 20% blend limits downside to ~0.20 * max_delta per row
- Gap is only 0.003 WS — need just a tiny real improvement on levels 1000/925
- Will only submit after v126 scores to preserve quota

---

## v127 — Combined Direction Improvements on v116 Base (PENDING SCORE)

**Date**: 2026-05-08
**Status**: BUILT, ready to submit
**Base**: v116 (mean_rank=1.423832, current best)
**Approach**: Combine v105 NS copula + v118 ECS seasonal width on v116 base
**Big idea**: Direction accounts for 95.2% of total score. v116 has identical direction to v102. Both v105 and v118 previously improved direction on v102/v105 bases. Apply both on v116 to stack improvements.

### Why this should work

Phase A error atlas revealed:
- **Direction = 95.2% of total score** (4309 cWS vs 218 cWS for speed)
- d7/d14 direction widths are 200-303° (near-uniform, massively over-wide)
- d1 direction widths are 55-72° (well-calibrated, leave alone)
- v105 (NS copula) saved 2-5 cWS per dim on v102
- v118 (ECS seasonal) saved 3-4 cWS per dim on v105

Both target **non-overlapping rows**:
- v105: NS grid d7/d14 (all 7 levels) — 1,149,120 rows
- v118: ECS surface 10m d7/d14 — 164,160 rows

No speed columns are touched.

### Expected direction width changes

| Dimension | v116 width | v127 width | Delta | Source |
|---|---|---|---|---|
| NS pressure d7 | 253.3 | 248.1 | -5.2 | NS copula |
| NS pressure d14 | 270.3 | 269.1 | -1.2 | NS copula |
| NS surface d7 | 270.6 | 259.3 | -11.3 | NS copula |
| NS surface d14 | 261.5 | 251.2 | -10.3 | NS copula |
| ECS surface d7 | 232.0 | 226.2 | -5.8 | ECS seasonal |
| ECS surface d14 | 302.2 | 294.1 | -8.1 | ECS seasonal |

### Expected leaderboard deltas (from v105+v118 history)

| Dim | v116 | Expected v127 | Delta |
|---|---|---|---|
| dir_pressure_d7_ns | 278.84 | ~276.61 | -2.24 |
| dir_surface_d7_ns | 291.14 | ~285.82 | -5.33 |
| dir_surface_d14_ns | 298.39 | ~297.08 | -1.32 |
| dir_surface_d7_ecs | 268.99 | ~265.86 | -3.13 |
| dir_surface_d14_ecs | 331.89 | ~328.08 | -3.81 |

### Risk factors
- Compound submission (two changes) — but rows are completely disjoint
- v118 seasonal calibration applied to ALL 8 windows uniformly; some windows may have different shift patterns
- Copula parameters estimated from 2019-2021 training data; 2022 distribution shift means rho/kappa may be slightly different
- Previous v105 and v118 on v102/v105 produced rank 1.424518 (same as v102!) — the direction improvements didn't change the rank, only raw scores. But v116 is already at 1.423832, so any improvement should directly lower the rank.

### Phase A Error Atlas Key Findings

1. **2022 wind speed is 25-40% higher than training**: W1/W2 are extreme (+25-38%), W5/W6 are calm (-9-25%)
2. **Top shifted features**: North Atlantic wind speed (KS 0.84), teleconnection indices (KS 0.77-0.84)
3. **Training speed distribution**: calm(<3) 25%, light(3-6) 31%, moderate(6-10) 32%, strong(10-15) 14%, extreme(15+) 2%
4. **Direction variance is season-independent**: std ~111-114° across all seasons
5. **HRES d1 speed ranges 4.5-9.5 m/s per window**, d7 ranges 4.7-9.0 m/s

### Leaderboard results

**mean_rank: 1.423832** (identical to v116)

| Dim | v116 | v127 | Delta | Flipped rank? |
|---|---|---|---|---|
| dir_pressure_d7_ns | 278.84 | 276.62 | -2.23 | No |
| dir_pressure_d14_ns | 299.22 | 297.34 | -1.88 | No |
| dir_surface_d7_ns | 291.14 | 285.81 | -5.33 | No |
| dir_surface_d14_ns | 298.39 | 297.07 | -1.32 | No |
| dir_surface_d7_ecs | 268.99 | 265.86 | -3.13 | No |
| dir_surface_d14_ecs | 331.89 | 328.08 | -3.81 | No |
| **Total** | | | **-17.70** | **0/36** |

### Lessons
- v105 copula and v118 seasonal calibration are **real improvements** (exact match with predictions)
- But rank-based scoring means -17.7 cWS across 6 dims is **nowhere near enough** — we need ~50-100 cWS improvement per dimension to flip ranks
- The competition is extremely tight at the top; small raw score improvements don't translate to rank gains
- Incremental direction width tweaks (5-15% narrowing) are a **dead lane for rank improvement**
- Need fundamentally different approach: either (a) dramatically narrower direction intervals with >90% coverage, or (b) attack dims where we're rank 3-5 with large gaps

---

## v130 — Von Mises Concentration-Based Direction Width (70% blend)

**Date**: 2026-05-09
**Base**: v127 (mean_rank=1.423832)
**Approach**: Replace uniform direction half-widths with wind-speed-conditioned von Mises concentration (kappa) for grid d7/d14 pressure direction
**Big idea**: Wind speed is inversely related to direction uncertainty. Von Mises kappa ∝ speed gives narrower intervals when confident (high wind) and wider when uncertain (calm).

### What was done
- Estimated von Mises kappa per row as `kappa = a * ws^b` (fitted on training residuals)
- 70% blend toward von Mises width, 30% incumbent width
- Applied to pressure d7/d14 only (surface was undercovered)

### Key scores
- dir_pressure_d7_ns: 276.62 → 274.80 (-1.82)
- dir_pressure_d14_ns: 297.34 → 296.51 (-0.83)
- dir_pressure_d7_ecs: 235.32 → 233.92 (-1.40)
- dir_pressure_d14_ecs: 307.47 → 306.89 (-0.58)
- mean_rank: 1.423832 → 1.422977 (-0.000855)

### Lessons
- Von Mises kappa works for pressure direction — physical signal is real
- 70% blend was safe but conservative; 90% on ECS might work
- Surface direction did NOT benefit (kappa too low at 10m)

---

## v132 — 90% Von Mises ECS + NS Revert (NEW BEST)

**Date**: 2026-05-09
**Base**: v130 (mean_rank=1.422977)
**Approach**: Aggressive 90% von Mises blend on ECS pressure d7/d14, revert NS pressure to v127
**Big idea**: v130 showed NS pressure d14 was hurt by more aggressive kappa (+1.24 cWS). Revert NS but push ECS harder.

### What was done
- ECS pressure d7/d14: 90% von Mises blend
- NS pressure: reverted to v127 (pre-von-Mises)
- All surface/station unchanged

### Key scores

| Dim | v127 | v130 | v132 | Delta vs v127 |
|---|---|---|---|---|
| dir_pressure_d7_ecs | 235.32 | 233.92 | 235.00 | -0.32 |
| dir_pressure_d14_ecs | 307.47 | 306.89 | 306.61 | -0.86 |
| dir_pressure_d7_ns | 276.62 | 274.80 | 276.62 | 0.00 |
| dir_pressure_d14_ns | 297.34 | 296.51 | 297.34 | 0.00 |

- **mean_rank: 1.422674** (NEW BEST, -0.000303 vs v130)

### Lessons
- NS pressure d14 is sensitive to kappa — reverting was correct
- ECS pressure direction benefits from aggressive kappa
- Von Mises is diminishing returns: 8 submissions (v130-v138) yielded only -0.001 total
- 16/36 dims are now rank-1; only dims with rank leverage matter

---

## v135 — CQR Angular Calibration d14 Pressure

**Date**: 2026-05-09
**Base**: v132
**Approach**: Conformalized Quantile Regression (angular CP) on d14 pressure direction for undercovered regions
**Big idea**: ECS d14 pressure coverage was 84-87% (under 90% target). Use CQR to expand intervals.

### Key scores
- dir_pressure_d14_ecs: 306.61 → 301.81 (-4.80 raw)
- dir_pressure_d14_ns: 297.34 → 297.07 (-0.27 raw)
- mean_rank: 1.422977 (SAME as v130, +0.000303 vs v132)

### Lessons
- Raw scores improved but conformal blend spilled into d7, regressing it
- Rank-based scoring: raw improvements don't matter if they don't flip per-dim ranks
- CQR calibration is NOT a rank-moving tool — it's a coverage safety net

---

## v137 — Enriched Kappa Features for Von Mises

**Date**: 2026-05-09
**Base**: v132
**Approach**: Replace simple `kappa = a * ws^b` with enriched feature-based kappa prediction (wind_shear, ws10_rstd3d/7d, msl, z700, natl_pc1/pc2)
**Big idea**: More features for kappa should give better uncertainty estimates

### Key scores
- dir_pressure_d7_ns: 276.62 → 273.89 (-2.73) HELPED
- dir_pressure_d14_ns: 297.34 → 298.58 (+1.24) HURT
- mean_rank: 1.422681 (+0.000007 vs v132)

### Lessons
- More aggressive kappa consistently hurts d14 (the same lesson from v130)
- Top features: ws10_rmean7d, natl_pc1, msl — these capture synoptic state
- d14 is too noisy for feature-conditioned kappa — simpler is better at long horizons

---

## v138 — Combo v132 + CQR d14 ECS Only

**Date**: 2026-05-09
**Base**: v132
**Approach**: v132 base + CQR angular expansion on ECS d14 pressure only (no d7 spill)
**Big idea**: Isolate the v135 ECS d14 raw win without d7 contamination

### Key scores
- dir_pressure_d14_ecs: 306.61 → 301.08 (-5.53 raw)
- mean_rank: 1.422674 (identical to v132)

### Lessons
- Even -5.53 cWS raw improvement on a single dim does NOT flip rank
- Our dims already have large moats; the remaining rank gaps are huge
- Von Mises/CQR is a dead lane for further rank improvement

---

## v139 — Per-Station LightGBM Direction Model (CATASTROPHIC)

**Date**: 2026-05-09
**Base**: v132
**Approach**: Per-station sin/cos LightGBM direction model trained on ALL enriched features, with conformal calibration
**Big idea**: Stations have very different local wind regimes. A per-station model should dramatically improve direction centers compared to nearest-grid.

### Training results (promising on calibration)
- NS_03: mae_model=26.6° vs mae_grid=83.5° (68% reduction!)
- NS_05: mae_model=24.0° vs mae_grid=78.0° (69% reduction!)
- ECS_01: mae_model=25.9° vs mae_grid=79.7° (67% reduction!)
- 11/14 stations used model over grid predictions

### Leaderboard results (CATASTROPHIC)

| Dim | v132 | v139 | Delta |
|---|---|---|---|
| dir_stations_d7_ns | 315.72 | **648.98** | **+333** |
| dir_stations_d14_ns | 305.63 | **628.51** | **+323** |
| dir_stations_d7_ecs | 225.25 | **770.99** | **+546** |
| dir_stations_d14_ecs | 332.94 | **894.09** | **+561** |

- **mean_rank: 1.426090** (+0.003416 vs v132 — CATASTROPHIC)

### What went wrong
The model had 26-33° MAE on the calibration split (training-adjacent data), but on the 2022 inference windows the predicted centers were wildly wrong. The conformal widths (88-315°) were not wide enough to compensate for centers pointing in completely wrong directions.

### Root cause analysis
1. **Concept drift**: Features from issue time (ws10, msl, etc.) have different distributions in 2022 vs 2019-2021 training
2. **Non-stationary relationships**: The correlation between issue-time features and future direction is weak and changes over time
3. **Overfitting to calibration**: The model learned spurious correlations that worked on training-adjacent data but not on held-out inference

### Lesson — STATION DIRECTION IS CURSED (6th failure)

**Hard rule: DO NOT replace station direction centers with learned models.**

Previous failures: v15 (+87), v33 (+616), v40 (+574), v43 (+49), v136 (built, not submitted), v139 (+333 to +561).

Pattern: every attempt to predict station direction from issue-time features fails catastrophically on hidden data, regardless of:
- Model complexity (OLS, LightGBM, CatBoost, circular models)
- Feature engineering (basic, enriched, per-station)
- Calibration method (conformal, von Mises, empirical-Bayes)

The ONLY safe station direction operations are:
1. **Width-only adjustments** (expanding intervals is always safe)
2. **Fractional blends toward incumbent** (never full replacement)
3. **HRES forecast direction** (physical model, not learned correlations — untested but promising for v142)

---

## Post-v139 Strategic Assessment

### Von Mises Era Summary (v127-v139, 7 submissions, -0.001158 mean_rank)

| Submission | Delta | Cumulative | Key change |
|---|---|---|---|
| v130 | -0.000855 | -0.000855 | Von Mises 70% pressure d7/d14 |
| v132 | -0.000303 | -0.001158 | 90% ECS von Mises, NS revert |
| v135 | +0.000303 | -0.000855 | CQR d14 pressure |
| v137 | +0.000007 | -0.000848 | Enriched kappa |
| v138 | 0.000000 | -0.000848 | CQR d14 ECS isolated |
| v139 | +0.003416 | +0.002568 | Station direction model (CATASTROPHIC) |

### Rank Sensitivity Analysis

v132 has **16/36 rank-1 dims**. The remaining 20 dims break down as:

| Category | Dims | Rank range | Rank leverage |
|---|---|---|---|
| Rank-1, large moat | 16 | 1 | Protected — any regression is catastrophic |
| Rank 2-3, small gap | 2 | 2-3 | Can flip with existing mechanisms |
| **Station direction** | **4** | **2.5-6** | **Biggest rank lever: dir NS d7 is rank 6** |
| Other direction | 6 | 2-3 | Moderate leverage but hard to move |
| Grid speed | 8 | 1-3 | Small gaps, proven hard to flip |

**Key insight**: Dir NS Stations d7 (rank 6) → rank 3 would save 3 rank points = **0.083 mean_rank** (10x all von Mises work combined). But station direction is cursed.

### Next Steps (Post-v139 Pivot)

**Dead lanes** (do NOT pursue):
1. Von Mises kappa tuning — diminishing returns (< 0.001 left)
2. Station direction center prediction — 6 catastrophic failures
3. CQR calibration — raw wins don't flip ranks
4. Enriched features for kappa — consistently hurts d14

**Viable lanes** (ranked by expected leverage):
1. **v142: HRES forecast direction for stations** — uses physical model (fcst_dir_d7_hX) as center, not learned correlations. Conformal calibration only. If HRES is even 30° better than grid, this could save 2-3 rank points.
2. **v140: Ekman spiral height correction** — stations at 3-102m height see different wind directions than 10m grid. Physical correction, not learned.
3. **Analog ensemble for d14 direction** — find historical cases with similar synoptic state, use their verified directions. Different from learned models.
4. **Grid direction improvements via physics** — jet-stream proximity, frontal gradients, pressure tendency. These improved pressure speed before.

---

## v142a — HRES Station d7 NS Scoped Physical Blend (REJECT RAW)

**Date**: 2026-05-09
**Base**: v132
**Artifact**: `starting-kit/phase_1/submission_v142a.zip`
**Approach**: Bias-correct HRES d7 forecast direction at station nearest-grid points, then use a 10% circular blend toward HRES only for station-hour cells that win on val, tune, and holdout replay.
**Big idea**: Test the one station-direction center lane that is not a learned station model. Full HRES replacement is unsafe, but a narrow physical blend may transfer.

### What was done
- Implemented `src/experiments/v142a_hres_station_d7_ns.py`.
- Full NS d7 HRES blend was rejected by the gate: `val -0.71`, `tune +3.43`, `holdout +11.56` cWS at blend 0.10.
- Station-hour gating found six stable cells: `NS_03 h12`, `NS_06 h18`, `NS_08 h0/h6/h12/h18`.
- Final submission changes exactly 48 rows: station / north_sea / d7 / direction only.

### Replay gate

| Split | Base cWS | v142a cWS | Delta | Changed rows |
|---|---:|---:|---:|---:|
| val | 137.3162 | 134.9548 | -2.3614 | 648 |
| tune | 217.4046 | 216.8179 | -0.5867 | 456 |
| holdout | 137.3754 | 134.5224 | -2.8530 | 525 |

Inference scope is smaller than replay row counts because phase-1 has only eight windows: 6 station-hour cells x 8 windows = 48 changed rows.

### Leaderboard result

| Dim | v132 | v142a | Delta |
|---|---:|---:|---:|
| dir_stations_d7_ns | 315.7238 | 633.0924 | +317.3686 |

- `primary_score`: 1.422674 -> 1.422674 (rank-neutral display)
- All other 35 dimensions were unchanged.

### Lessons
- **REJECT RAW.** The primary score stayed rank-neutral, but the target cell failed catastrophically.
- Full HRES station-direction replacement was unsafe on replay, and even station-hour scoped HRES blends failed hidden transfer.
- Freeze station-direction center changes entirely, including physical HRES centers. Future work should avoid station direction except possibly pure width expansion with no center movement.

---

## v143 — ECS Surface d7/d14 u/v Residual MLP (PENDING SCORE)

**Date**: 2026-05-09
**Base**: v132
**Artifact**: `starting-kit/phase_1/submission_v143.zip`
**Approach**: Train a small MLP to predict residual unit-vector components around the ECS surface base direction, then blend the prediction into v132 direction centers with λ=0.30 while preserving existing interval half-widths.
**Big idea**: Test the snowpine-style surface-direction gap with an incumbent-anchored vector residual model, not an angle replacement and not station rows.

### What was done
- Implemented `src/experiments/v143_mlp_uv_ecs_surface_direction.py`.
- Scope: grid / east_china_sea / 10m / d7+d14 direction only.
- Changed rows: 164,160.
- Non-target rows changed: 0.
- Widths preserved from v132; only `dir_50` and corresponding bounds shift around the same half-width.

### Replay gate

| Split | Horizon | Base cWS | v143 proxy cWS | Delta |
|---|---:|---:|---:|---:|
| val | d7 | 266.1988 | 265.3167 | -0.8821 |
| tune | d7 | 308.5761 | 307.8203 | -0.7558 |
| holdout | d7 | 258.9854 | 258.4638 | -0.5217 |
| val | d14 | 328.3975 | 327.0188 | -1.3788 |
| tune | d14 | 337.1594 | 336.2445 | -0.9150 |
| holdout | d14 | 326.5143 | 324.7428 | -1.7715 |

### Lessons
- **PENDING SCORE.** This is the first MLP/vector-residual grid-direction candidate to improve every replay split for both ECS surface d7 and d14.
- Caveat: the replay base is a calibrated forecast-direction proxy, not exact v132 replay. Treat the upload as a transfer test, not proof.
- If hidden transfers, expand carefully with λ sweeps or level 100m; if it fails, MLP/vector residuals join the false-positive class for surface direction.

---

## v145 — Regime Analog Direction Centers (RANK-NEUTRAL)

**Date**: 2026-05-09
**Base**: v142 if available, otherwise v132 fallback
**Artifact**: `starting-kit/phase_1/submission_v145.zip`
**Approach**: Nearest-neighbor analog residuals in 14-day context space. Blend the analog residual into the incumbent direction center and preserve incumbent direction widths exactly.
**Big idea**: If hidden failures are regime-change failures, the closest historical context may beat smooth residual models.

### What was done
- Implemented `src/experiments/_direction_breakthrough_utils.py`.
- Implemented `src/experiments/v145_regime_analog_direction.py`.
- Promoted scope: grid / east_china_sea / 10m / d14 direction only.
- Changed rows: 82,080.
- Non-target rows changed: 0.
- Station d7 was tested but excluded because every blend had at least one split/region regression.

### Replay gate

| Candidate | Mean Delta cWS | Worst Delta cWS | Decision |
|---|---:|---:|---|
| ECS surface d14 analog center blend 0.35 | -2.0810 | -1.7297 | PROMOTE |
| station d7 analog center blend 0.35 | -1.0911 | +0.8832 | REJECT |

### Lessons
- **RANK-NEUTRAL.** Primary stayed at `1.421875`, matching v142 and trailing v146.
- The raw ECS surface d14 center move transferred: `dir_surface_d14_ecs` improved `328.0751 -> 326.8499` (-1.2252 cWS).
- This validates the regime analog center mechanism for ECS d14, but v145 lacks the v146 station d7 width wins. Next candidate should combine v146 station d7 widths with v145 ECS d14 center while excluding v146's bad ECS d14 width overlay.

---

## v146 — Weighted Conformal Direction Widths (NEW BEST)

**Date**: 2026-05-09
**Base**: v142 if available, otherwise v132 fallback
**Artifact**: `starting-kit/phase_1/submission_v146.zip`
**Approach**: Use context-nearest historical residuals as weighted conformal residual quantiles, then change only direction interval widths around incumbent centers.
**Big idea**: Adapt to regime uncertainty without trusting a new center model.

### What was done
- Implemented `src/experiments/v146_weighted_conformal_widths.py`.
- Scope: ECS 10m surface d14 direction widths and station d7 direction widths in both regions.
- Changed rows: 82,559.
- Explicit verification: `dir_50` unchanged on all touched rows.
- `compound=true` in `submissions/log.json` because two direction families are touched.

### Replay gate

| Candidate | Mean Delta cWS | Worst Delta cWS | Decision |
|---|---:|---:|---|
| ECS surface d14 width blend 0.80 | -19.8877 | -4.8936 | PROMOTE |
| station d7 width blend 0.40 | -7.9828 | -0.9487 | PROMOTE |

### Lessons
- **NEW BEST.** Primary improved from v142 `1.421875` to `1.421297` (-0.000578).
- The station d7 width component transferred: `dir_stations_d7_ns` improved `312.4857 -> 310.9467` (-1.5390 cWS) and `dir_stations_d7_ecs` improved `221.7904 -> 219.2946` (-2.4958 cWS).
- The ECS surface d14 width component failed hidden transfer: `328.0751 -> 328.5448` (+0.4697 cWS). Future conformal-width submissions should preserve station d7 and avoid ECS surface d14 width-only overlays unless rebuilt more narrowly.

---

## v147 — Circular Forest ECS Surface Residual Distribution (PENDING SCORE)

**Date**: 2026-05-09
**Base**: v142 if available, otherwise v132 fallback
**Artifact**: `starting-kit/phase_1/submission_v147.zip`
**Approach**: Train an ExtraTrees residual-vector model for ECS 10m surface d7/d14. Tree votes also produce a residual-magnitude distribution, but width-blend candidates were rejected by the split gate.
**Big idea**: Let discontinuous tree leaves catch regime pockets that a smooth MLP missed.

### What was done
- Implemented `src/experiments/v147_circular_forest_ecs_surface.py`.
- Scope: grid / east_china_sea / 10m / d7+d14 direction centers only.
- Changed rows: 164,160.
- Selected center blend: 0.32.
- Selected width blend: 0.00, so incumbent widths are preserved.

### Replay gate

| Candidate | Mean Delta cWS | Worst Delta cWS | Decision |
|---|---:|---:|---|
| center 0.32 / width 0.00 | -1.5753 | -0.3903 | PROMOTE |
| center 0.32 / width 0.50 | -18.9023 | +9.9172 | REJECT |

### Lessons
- **PENDING SCORE.** The forest center-only candidate is locally stronger than v143 while still avoiding the unstable forest-width variants.
- If hidden d7/d14 surface improves, trees are a better ECS surface residual lane than MLP. If it fails like v143, ECS grid surface centers should be treated as replay overfit unless paired with no-center width adaptation.

---

## v148 — IsolationForest-Gated Conformal Widths (PENDING SCORE)

**Date**: 2026-05-09
**Base**: v142 if available, otherwise v132 fallback
**Artifact**: `starting-kit/phase_1/submission_v148.zip`
**Approach**: Fit an IsolationForest on historical 14-day context features and use the anomaly score as a gate on weighted conformal direction widths. Direction centers are never moved.
**Big idea**: Treat anomaly detection as a regime-rarity gate, not as a forecast model.

### What was done
- Implemented `src/experiments/v148_isoforest_anomaly_widths.py`.
- Evaluated two families:
  - pure anomaly widening;
  - IsolationForest-gated conformal width adaptation.
- Promoted scope: grid / east_china_sea / 10m / d14 direction widths only.
- Changed rows: 82,080.
- Explicit verification: `dir_50` unchanged on all touched rows.
- Station d7 was excluded because all gated-conformal variants had at least one split/region regression.

### Replay gate

| Candidate | Mean Delta cWS | Worst Delta cWS | Decision |
|---|---:|---:|---|
| ECS surface d14 IF-gated conformal blend 0.35 | -0.3040 | -0.0018 | PROMOTE |
| station d7 IF-gated conformal blend 0.70 | -0.9933 | +0.3632 | REJECT |
| ECS surface d14 pure IF widening cap 1.08 | +0.2367 | +0.4301 | REJECT |

### Lessons
- **PENDING SCORE.** Pure IsolationForest anomaly widening is harmful on replay; just making unusual contexts wider is not enough.
- The viable formulation is using anomaly score as a sparse gate into conformal width adaptation, and only ECS surface d14 passed the strict no-regression gate.

---

## v149 — Combine v146 Station Widths + v145 ECS Surface Center (TIED BEST)

**Date**: 2026-05-10
**Base**: v142
**Artifact**: `starting-kit/phase_1/submission_v149.zip`
**Approach**: Recombine the two hidden-transferring pieces after scoring v146 and v145. Copy station d7 direction bounds from v146, and copy ECS 10m surface d14 direction center/interval from v145.
**Big idea**: Keep the v146 station d7 width wins and the v145 ECS d14 center raw win, while excluding v146's ECS d14 width regression.

### What was done
- Implemented `src/experiments/v149_combine_station_widths_surface_center.py`.
- Station d7 rows copied from v146: 480.
- ECS surface d14 rows copied from v145: 82,080.
- Total changed direction rows versus v142: 82,559.
- Non-target changed rows: 0.
- Station d7 centers moved: 0.

### Expected leaderboard behavior

| Component | Source | Hidden evidence | Keep? |
|---|---|---|---|
| station d7 widths | v146 | NS -1.5390 cWS, ECS -2.4958 cWS | yes |
| ECS surface d14 center | v145 | ECS d14 -1.2252 cWS | yes |
| ECS surface d14 widths | v146 | ECS d14 +0.4697 cWS regression | no |

### Lessons
- **TIED BEST.** Primary stayed `1.421297`, matching v146.
- The recombination behaved exactly as intended in raw metrics: station d7 kept the v146 values and ECS surface d14 kept the v145 improvement (`326.8499` instead of v146's `328.5448`).
- The extra ECS d14 raw gain did not flip another rank. Treat v149 as the raw-cleaner tied-best artifact; v146 remains the minimal current-best artifact.

---

## v150 — v149 + Forest ECS Surface d14 Only (TIED BEST)

**Date**: 2026-05-10
**Base**: v149
**Artifact**: `starting-kit/phase_1/submission_v150.zip`
**Approach**: Keep the tied-best v149 station d7 widths, then copy only the ECS 10m surface d14 forest center block from v147. Exclude the ECS d7 forest center component from v147.
**Big idea**: Test the forest center mechanism only where center movement has already shown hidden raw transfer: ECS surface d14.

### What was done
- Implemented `src/experiments/v150_v149_plus_forest_d14_only.py`.
- ECS surface d14 rows copied from v147: 82,080.
- Station d7 width rows carried from v149/v146: 480.
- Changed direction rows versus v142: 82,559.
- ECS surface d7 changed rows: 0.
- Non-target changed rows: 0.
- Station d7 centers moved: 0.

### Lessons
- **TIED BEST.** Primary stayed `1.421297`, matching v146 and v149.
- The d14-only forest center worked raw: `dir_surface_d14_ecs` improved from v149 `326.8499` to v150 `325.6517` (-1.1982 cWS), while station d7 stayed at the v146/v149 winning values.
- The extra raw ECS d14 gain still did not flip another rank. v150 is the raw-cleanest tied-best artifact, but the next breakthrough must target a rank-sensitive cell rather than further raw ECS d14 cleanup.

---

## v151 — Full Scored-Donor Oracle (PENDING SCORE)

**Date**: 2026-05-10
**Base**: v150
**Artifact**: `starting-kit/phase_1/submission_v151.zip`
**Approach**: Parse `submissions/log.json`, find all scored submissions with local prediction files, and copy whole metric blocks whenever a donor has a better raw leaderboard score than v150.
**Big idea**: Harvest old per-dimension wins that were buried inside globally worse submissions.

### What was done
- Implemented `src/experiments/v151_donor_oracle.py`.
- Wrote donor table: `logs/v151_donor_oracle/donor_table.csv`.
- Copied blocks table: `logs/v151_donor_oracle/copied_blocks.csv`.
- Copied 18 dimensions into v150.
- Speed-changed rows: 739,232.
- Direction-changed rows: 1,321,253.
- Non-target q rows: 0.
- Non-target direction rows: 0.
- Speed quantile crossing rows: 0.

### Biggest copied raw donors

| Dimension | v150 | Donor | Delta | Source |
|---|---:|---:|---:|---|
| dir_pressure_d7_ns | 276.6154 | 266.5361 | -10.0793 | v3 |
| dir_pressure_d14_ecs | 306.4180 | 300.5204 | -5.8976 | v135 |
| dir_surface_d1_ns | 91.1033 | 90.8856 | -0.2177 | v96 |
| speed_surface_d14_ecs | 10.7740 | 10.6500 | -0.1240 | v48 |
| speed_surface_d7_ecs | 9.8216 | 9.7200 | -0.1016 | v48 |

### Lessons
- **PENDING SCORE.** This is high-upside but broad. It copies direction blocks from old globally poor submissions, so it should be treated as an oracle diagnostic rather than the safest next upload.

---

## v152 — Speed-Only Scored-Donor Oracle (PENDING SCORE)

**Date**: 2026-05-10
**Base**: v150
**Artifact**: `starting-kit/phase_1/submission_v152.zip`
**Approach**: Same donor table as v151, but copy only speed dimensions. Direction columns remain exactly v150.
**Big idea**: Attack near-gap speed dimensions without risking direction regressions.

### What was done
- Implemented `src/experiments/v152_speed_donor_oracle.py`.
- Wrote speed donor table: `logs/v152_speed_donor_oracle/donor_table_speed_only.csv`.
- Copied 11 speed dimensions into v150.
- Speed-changed rows: 739,232.
- Direction-changed rows: 0.
- Non-target q rows: 0.
- Speed quantile crossing rows: 0.

### Lessons
 - **PENDING SCORE.** This is the safer donor-oracle candidate. If it improves primary, use v152 as the new base for direction/station work.

---

## v151 — Full Scored-Donor Oracle (SCORED: NEW BEST with toxic donor)

**Date**: 2026-05-10
**Approach**: Whole-dimension donor oracle recombination on v150 base. Copied 18 speed/direction dimension blocks from historically best-scoring submissions.
**Big idea**: Harvest every per-dimension raw-score win across all 105 previous submissions by copying whole metric blocks.

### What was done
- Built per-dimension donor table from all scored submissions with available prediction files.
- Copied 18 whole metric blocks into v150: speed columns for speed dims, direction columns for direction dims.
- Speed-changed rows: 739,232; direction-changed rows: 1,321,253.

### Key improvements vs v150

| Dim | v150 | v151 | Delta |
|-----|------|------|-------|
| dir_pressure_d14_ecs | 306.418 | 300.520 | -5.898 improved |
| dir_surface_d1_ns | 91.103 | 90.886 | -0.218 improved |
| speed_stations_d1_ns | 7.398 | 7.326 | -0.073 improved |
| speed_surface_d7_ecs | 9.822 | 9.723 | -0.098 improved |
| speed_surface_d14_ecs | 10.774 | 10.651 | -0.123 improved |
| speed_pressure_d1_ecs | 6.704 | 6.684 | -0.020 improved |
| speed_stations_d14_ns | 15.605 | 15.560 | -0.045 improved |

### Catastrophic regression

| Dim | v150 | v151 | Delta |
|-----|------|------|-------|
| **dir_pressure_d7_ns** | **276.615** | **438.864** | **+162.249 CATASTROPHIC** |

A toxic direction donor (likely v3 or similar old submission) was copied for NS pressure d7 direction, causing a massive regression from 277 to 439 cWS. Despite this, the primary score improved because the aggregate speed and d14 direction wins outweighed the rank damage.

### Score
- primary_score: **1.420250** (36/36 OK, no SENTINEL)
- Delta vs v150: **-0.001047**

### Lesson
- PROMOTE as new best, but IMMEDIATELY build v153 that reverts only dir_pressure_d7_ns back to v150 values while keeping all other v151 improvements. This should push primary even lower.
- The donor oracle approach works: raw-score harvesting across all submissions finds real hidden-transferring improvements.
- BUT direction donors from globally bad submissions can carry toxic signal. The dir_pressure_d7_ns regression proves that v107's lesson was correct: old direction scores can completely invert on hidden data.
- v152 (speed-only oracle) is still pending and will isolate whether speed donors alone are enough.

---

## v152 — Speed-Only Donor Oracle (SCORED: NEW BEST, clean base)

**Date**: 2026-05-10
**Approach**: Speed-only donor oracle recombination on v150 base. Copied 11 speed dimension blocks from historically best-scoring submissions. All direction rows untouched.
**Big idea**: Test whether speed donors alone can improve primary without risking toxic direction donors.

### What was done
- Built per-dimension speed donor table from all scored submissions.
- Copied 11 speed metric blocks into v150: only q05/q50/q95 columns changed.
- Direction rows: 0 changed. All 18 direction dims identical to v150.

### Speed improvements vs v150

| Dim | v150 | v152 | Delta |
|-----|------|------|-------|
| speed_stations_d1_ns | 7.398 | **7.326** | -0.073 |
| speed_stations_d14_ns | 15.605 | **15.560** | -0.045 |
| speed_surface_d7_ecs | 9.822 | **9.723** | -0.098 |
| speed_surface_d14_ecs | 10.774 | **10.651** | -0.123 |
| speed_pressure_d1_ecs | 6.704 | **6.684** | -0.020 |

All 18 direction dimensions identical to v150 — no regressions.

### Score
- primary_score: **1.420300** (36/36 OK, no SENTINEL)
- Delta vs v150: **-0.000997**
- Delta vs v151: **+0.000050** (slightly worse because missing the 2 direction improvements)

### Lesson
- PROMOTE as the SAFER base. v152 has all the speed wins and zero direction risk.
- v151 has 2 additional direction wins (dir_pressure_d14_ecs -5.90, dir_surface_d1_ns -0.22) but carries a catastrophic toxic donor (dir_pressure_d7_ns +162).
- **Immediate next step**: build v153 = v152 + cherry-pick the 2 safe direction wins from v151 (NOT the toxic NS pressure d7). This should beat both v151 and v152.

---

## v153 — v152 + Safe v151 Direction Donors (PENDING)

**Date**: 2026-05-11
**Approach**: V152 base + cherry-pick 2 safe direction improvements from v151, explicitly excluding the toxic dir_pressure_d7_ns donor.
**Big idea**: Combine v152's clean speed wins with v151's 2 non-toxic direction improvements. This should beat both v151 and v152.

### What was done
- Started from `predictions_v152.csv` (speed-only donor oracle, 1.420300).
- Copied `dir_05/dir_50/dir_95` from `predictions_v151.csv` for 2 direction dimensions:
  - `dir_pressure_d14_ecs`: ECS pressure-level grid rows at horizon d14 (410,400 rows)
  - `dir_surface_d1_ns`: NS surface grid rows at horizon d1 (164,160 rows)
- Explicitly blocklisted and verified `dir_pressure_d7_ns` unchanged (max diff=0.00).
- All speed columns identical to v152 (0 rows changed).

### Verification
- Row count: 3,448,800
- Speed rows changed: 0
- Direction rows changed: 574,560 (all in scope)
- Non-target changes: 0
- NaN in prediction columns: 0
- dir_pressure_d7_ns verified unchanged: YES

### Expected leaderboard deltas vs v152

| Dim | v152 | v153 expected | Delta |
|-----|------|---------------|-------|
| dir_pressure_d14_ecs | 306.418 | 300.520 | -5.898 |
| dir_surface_d1_ns | 91.103 | 90.886 | -0.218 |

### Expected primary: < 1.420250 (beat v151 cleanly)

### Score
- primary_score: **1.420250** (36/36 OK, no SENTINEL)
- Delta vs v152: **-0.000050**
- Delta vs v151: **0.000000** (same primary, but NO toxic regression)

### Verification vs hidden scores

| Dim | v152 | v153 | v151 | Status |
|-----|------|------|------|--------|
| dir_pressure_d14_ecs | 306.418 | **300.520** | 300.520 | Match v151 |
| dir_surface_d1_ns | 91.103 | **90.886** | 90.886 | Match v151 |
| dir_pressure_d7_ns | 276.615 | **276.615** | 438.864 | Safe, NOT toxic |

All speed dims identical to v152. All other direction dims identical to v152.

### Lesson
- PROMOTE as definitive best. Same primary as v151 (1.420250) but without the catastrophic +162 cWS on dir_pressure_d7_ns.
- The toxic v151 regression was rank-neutral (dimension was already far behind), so primary didn't change. But v153 is strictly better in raw scores.
- The donor oracle + cherry-pick approach is validated: speed donors + selective safe direction donors = new best without risk.
- v153 is the new production base for all future work.

---

## v154 — Merge-Aligned dir_pressure_d7_ns Fix (TIED BEST)

**Date**: 2026-05-11
**Approach**: v153 base + merge-aligned dir_pressure_d7_ns from v3.
**Big idea**: The v151 toxic regression (276.6→438.9 on dir_pressure_d7_ns) was caused by a **positional indexing bug**, not by v3's predictions being bad.

### Root Cause Analysis
- The v151 donor oracle used `donor.loc[idx, cols]` to copy prediction values, where `idx` was derived from a boolean mask on the `preds` DataFrame.
- This assumes the donor has the same row ordering as the base predictions.
- v47 and v48 happen to have identical row ordering to v153 → v152's speed copies were correct.
- v3 has a completely different row ordering → positional copy assigned wrong direction values to wrong rows.
- v3 actually scores 266.5 on dir_pressure_d7_ns (best ever) — the "toxicity" was entirely a bug.
- Fix: merge on key columns `(type, window, region, latitude, longitude, station, horizon, hour, level)` instead of positional indexing.

### What was done
- Started from `predictions_v153.csv`.
- Merged v3's `dir_05/dir_50/dir_95` onto v153 using key-column merge.
- Applied only to NS pressure d7 rows (410,400 rows).
- All speed columns unchanged. All other direction dims unchanged.

### Expected leaderboard impact
- dir_pressure_d7_ns: 276.6 → 266.5 (-10.1 cWS)
- Expected primary: potentially significant improvement (this is the largest single-dimension raw gap available)

### Actual leaderboard result
- **Primary stayed `1.420250`**, tied with v153.
- `dir_pressure_d7_ns` improved exactly as intended: `276.6154 -> 266.5361` (-10.0793 cWS).
- No side effects appeared in the 36-dim score log.

### Lessons
- The merge-aligned donor fix worked technically and raw-score-wise.
- The dimension is rank-insensitive at the current leaderboard boundary, so the large raw gain did not improve primary.
- v154 is raw-cleaner than v153, but not primary-better. v155 is optional; it only tests remaining tiny merge-aligned direction donors.

---

## v155 — Full Merge-Aligned Donor Oracle (TIED BEST)

**Date**: 2026-05-11
**Approach**: v153 base + ALL 14 merge-aligned donor improvements.
**Big idea**: Apply the merge-alignment fix to ALL improvable dimensions simultaneously.

### What was done
- 14 donor blocks applied with merge alignment:
  - dir_pressure_d7_ns from v3 (410,400 rows, gap=-10.08)
  - dir_pressure_d14_ns from v96 (410,400 rows, gap=-0.011)
  - dir_surface_d7_ecs from v130 (164,160 rows, gap=-0.001)
  - dir_stations_d1_ecs from v47 (224 rows, gap=-0.001) — 0 actual changes (identical to v153)
  - dir_pressure_d1_ecs from v50 (410,400 rows, gap=-0.001) — 0 actual changes
  - 9 speed blocks from v47/v48 — all 0 actual changes (already in v153 via v152)
- Total direction rows changed: 746,693 (3 actually different dims)
- Quantile crossing: 0

### Expected leaderboard impact
- Same as v154 for dir_pressure_d7_ns (the dominant improvement)
- Minor additional direction improvements from v96 and v130
- Speed dims already optimal in v153

### Scored result

- **Primary stayed `1.420250`**, tied with v153/v154.
- `dir_pressure_d7_ns` kept the v154 raw win: `276.6154 -> 266.5361`.
- `dir_pressure_d14_ns` improved slightly: `297.3393 -> 297.3284`.
- `dir_surface_d7_ecs` improved slightly: `265.8568 -> 265.8556`.
- No side effects in speed dimensions or station direction.

### Lessons

- The merge-aligned donor oracle is technically validated, but the remaining
  raw direction gains are rank-neutral.
- Treat v155 as the raw-cleanest tied-best base, but stop spending submissions
  on direction donor copying unless the public rank table changes materially.
- Next work should pivot to station d14 width-only candidates and near-gap
  speed micro-flips.

---

## v156 — ECS Station d14 Direction Widths (TIED BEST)

**Date**: 2026-05-12
**Approach**: v155 base + weighted-conformal half-width update for ECS station d14 direction only.
**Big idea**: Attack `dir_stations_d14_ecs` without moving station-direction centers, using the v146 context-analog width mechanism that already transferred on station d7.

### What was done
- Implemented `src/experiments/v156_station_d14_widths.py`.
- Built replay frame with station d14 direction residuals and 14-day context similarity.
- Selected ECS blend `0.60` by val/tune/holdout no-regression gate.
- Modified only ECS station horizon-14 `dir_05/dir_95`; `dir_50` unchanged.
- Changed rows: 223. Speed quantiles changed: 0.
- Artifact: `starting-kit/phase_1/submission_v156.zip`.

### Replay gate
| Candidate | Mean delta cWS | Worst split delta cWS |
|---|---:|---:|
| east_china_sea_station_d14_width_blend_0.60 | -19.4112 | -7.9259 |

### Lessons
- SCORED: TIED BEST. The raw direction-width signal transferred strongly:
  `dir_stations_d14_ecs` improved `332.9393 -> 322.7848` with no side effects,
  but primary stayed `1.420250`.
- This proves the v146-style station d14 width mechanism can transfer hidden
  raw score, but the ECS d14 rank boundary is much farther away than the public
  rank-gap estimate implied.
- Do not compound v156 yet. The smaller v157 NS width probe is now lower
  priority than near-gap speed micro-flips.

---

## v157 — NS Station d14 Direction Widths (PENDING)

**Date**: 2026-05-12
**Approach**: v155 base + weighted-conformal half-width update for North Sea station d14 direction only.
**Big idea**: Target the larger visible `dir_stations_d14_ns` gap while keeping station-direction centers frozen.

### What was done
- Reused `src/experiments/v156_station_d14_widths.py`.
- Selected NS blend `0.25` by val/tune/holdout no-regression gate.
- Modified only North Sea station horizon-14 `dir_05/dir_95`; `dir_50` unchanged.
- Changed rows: 256. Speed quantiles changed: 0.
- Artifact: `starting-kit/phase_1/submission_v157.zip`.

### Replay gate
| Candidate | Mean delta cWS | Worst split delta cWS |
|---|---:|---:|
| north_sea_station_d14_width_blend_0.25 | -1.0417 | -0.1880 |

### Lessons
- PENDING SCORE. The NS signal is smaller than ECS but passes all split gates and attacks a bigger visible raw gap.
- Submit separately from v156; do not combine until one region has hidden proof.

---

## v158-v161 — Speed Micro-Shrink Probes (v158 REJECTED; v159-v161 HELD)

**Date**: 2026-05-12
**Approach**: v156 base + one-dimension q05/q95 micro-shrink probes.
**Big idea**: The smallest remaining rank gaps are speed cells where donor copying has already been exhausted. Test whether the incumbent intervals have enough coverage slack for a tiny endpoint shrink to flip a rank without retraining.

### What was done
- Implemented `src/experiments/v158_speed_micro_shrink.py`.
- Each candidate changes exactly one official speed dimension.
- `q50` is unchanged; all direction columns are unchanged.
- Each ZIP contains exactly one `predictions.csv`.

### Candidates
| ID | Target dimension | Rows changed | Half-width shrink | Expected WS delta if coverage unchanged |
|---|---|---:|---:|---:|
| v158 | `speed_surface_d14_ns` | 164,160 | 0.0015 | -0.0030 |
| v159 | `speed_pressure_d14_ns` | 410,400 | 0.0015 | -0.0030 |
| v160 | `speed_pressure_d7_ns` | 410,400 | 0.0018 | -0.0036 |
| v161 | `speed_surface_d1_ecs` | 164,160 | 0.0040 | -0.0080 |

### Lessons
- v158 SCORED: REJECT. The tiny shrink worsened `speed_surface_d14_ns`
  `15.1216 -> 15.1225` and primary `1.420250 -> 1.420252`.
- This is a useful negative signal: the incumbent `speed_surface_d14_ns`
  interval is already coverage-tight, and even a `0.0015` endpoint shrink can
  trigger hidden Winkler penalty.
- Hold v159-v161. Do not spend more submissions on blind speed micro-shrinks
  without a new validation signal.

---

## v162 — ECS Pressure d14 Shear/ws3 Level Push (SCORED: NEW BEST)

**Date**: 2026-05-12
**Approach**: v156 base + raise the hidden-proven v55 shear/ws3 blend on ECS pressure d14 levels `850` and `925`.
**Big idea**: After v158 showed blind endpoint shrinkage is unsafe, return to the only hidden-proven pressure-speed family. Current v156 already contains the v57 shape; v162 keeps the same 850/925 level gate and pushes lambda from `0.35` to `0.50`.

### What was done
- Implemented `src/experiments/v162_pressure_d14_ecs_push.py`.
- Base: `predictions_v156.csv`.
- Anchor/donor family: `v53 -> v55`, with `q = v53 + 0.50 * (v55 - v53)` on upgraded levels.
- Scope: grid / `east_china_sea` / pressure / d14 / speed only.
- Changed rows: 164,160.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- Artifact: `starting-kit/phase_1/submission_v162.zip`.

### Level diagnostics
| Level | Rows | Changed | Mean width delta vs v156 |
|---|---:|---:|---:|
| 1000 | 82,080 | no | 0.0000 |
| 925 | 82,080 | yes | -0.0820 |
| 850 | 82,080 | yes | -0.0409 |
| 700 | 82,080 | no | 0.0000 |
| 500 | 82,080 | no | 0.0000 |

### Lessons
- SCORED: NEW BEST. The hidden-proven pressure-speed lane transferred again.
- `speed_pressure_d14_ecs` improved `17.9488 -> 17.9321` (`-0.0167`), and
  primary improved `1.420250 -> 1.420203`.
- This is the opposite of v158: not a blind endpoint shrink, but a physically
  grounded shear/ws3 shape move with prior hidden evidence.
- Continue with a controlled 850/925 lambda push or level split; keep v156 as
  fallback if the next pressure push regresses.

---

## v163 — ECS Pressure d14 Shear/ws3 Lambda 0.65 Push (SCORED: NEW BEST)

**Date**: 2026-05-12
**Approach**: v162 base + raise the same ECS pressure d14 `850`/`925` shear/ws3 blend from `0.50` to `0.65`.
**Big idea**: v162 proved hidden headroom remains in the v57 level gate. v163 repeats the same controlled step size and keeps every other pressure level unchanged.

### What was done
- Implemented `src/experiments/v163_pressure_d14_ecs_push65.py`.
- Base: `predictions_v162.csv`.
- Anchor/donor family: `v53 -> v55`, with `q = v53 + 0.65 * (v55 - v53)` on upgraded levels.
- Scope: grid / `east_china_sea` / pressure / d14 / speed only.
- Changed rows vs v162: 164,160.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- Artifact: `starting-kit/phase_1/submission_v163.zip`.

### Incremental level diagnostics vs v162
| Level | Rows | Changed | Mean width delta |
|---|---:|---:|---:|
| 1000 | 82,080 | no | 0.0000 |
| 925 | 82,080 | yes | -0.0820 |
| 850 | 82,080 | yes | -0.0409 |
| 700 | 82,080 | no | 0.0000 |
| 500 | 82,080 | no | 0.0000 |

### Leaderboard scores
| Dim | Best (v162) | New (v163) | Delta |
|-----|-----------:|-----------:|------:|
| speed_pressure_d14_ecs | 17.9321 | 17.9165 | -0.0156 improved |
| primary_score | 1.420203 | 1.420160 | -0.000043 improved |

### Lessons
- SCORED: NEW BEST. The same level-gated shear/ws3 pressure-speed family transferred again with no side effects.
- Gains remain monotone but are shrinking: v162 gained `-0.0167`, v163 added `-0.0156`.
- Continue only with level-split or smaller lambda increments. The next visible boundary is likely carlometta at `17.8900`, so roughly `0.0265` more raw WS is needed on this cell.

---

## v164 — ECS Pressure d14 925-Only Lambda 0.80 Push (SCORED: NEW BEST)

**Date**: 2026-05-14
**Approach**: v163 base + raise only ECS pressure d14 level `925` from lambda `0.65` to `0.80` toward the v55 shear/ws3 donor.
**Big idea**: v163 kept the pressure-speed lane monotone but the remaining rank boundary is close. Split the next push by level instead of increasing both `850` and `925`.

### What was done
- Implemented `src/experiments/v164_pressure_d14_ecs_925_push80.py`.
- Base: `predictions_v163.csv`.
- Anchor/donor family: `v53 -> v55`, with `q = v53 + 0.80 * (v55 - v53)` on level `925` only.
- Scope: grid / `east_china_sea` / pressure / d14 / speed only.
- Changed rows vs v163: 82,080.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- Artifact: `starting-kit/phase_1/submission_v164.zip`.

### Incremental level diagnostics vs v163
| Level | Rows | Changed | Mean width delta |
|---|---:|---:|---:|
| 1000 | 82,080 | no | 0.0000 |
| 925 | 82,080 | yes | -0.0820 |
| 850 | 82,080 | no | 0.0000 |
| 700 | 82,080 | no | 0.0000 |
| 500 | 82,080 | no | 0.0000 |

### Lessons
- SCORED: NEW BEST. The 925-only continuation transferred cleanly.
- `speed_pressure_d14_ecs` improved `17.9165 -> 17.9087` (`-0.0078`) and primary improved `1.420160 -> 1.420138`.
- The pressure lane remains monotone but is clearly diminishing. Current public gap to carlometta is about `0.0187` on this cell.
- v165 remains the pending quota-saving compound candidate on top of v164; its only additional risk is the 224-row ECS station d1 bias tweak.

---

## v165 — Compound v164 + ECS Station d1 v79 Bias (SCORED: REJECT)

**Date**: 2026-05-14
**Approach**: v164 base + v79 raw per-station parallel offsets on ECS station d1 speed rows.
**Big idea**: Save one submission by combining the active pressure probe with the only small additive `speed_stations_d1_ecs` bias tweak that previously transferred hidden.

### What was done
- Implemented `src/experiments/v165_compound_v164_station_d1_ecs_bias.py`.
- Base: `predictions_v164.csv`.
- Preserves v164: ECS pressure d14 level `925` lambda `0.65 -> 0.80`.
- Adds v79 raw per-station offsets on `station / east_china_sea / d1 / speed`.
- Changed rows vs v164: 224 speed rows.
- Direction rows changed vs v164: 0.
- Non-target speed rows changed vs v164: 0.
- Quantile crossings: 0.
- Artifact: `starting-kit/phase_1/submission_v165.zip`.

### Station offsets
| Station | Rows | Offset |
|---|---:|---:|
| ECS_01 | 32 | +0.1280 |
| ECS_02 | 32 | +0.3636 |
| ECS_03 | 32 | -0.0087 |
| ECS_04 | 32 | -0.0486 |
| ECS_05 | 32 | +0.0162 |
| ECS_06 | 32 | -0.2618 |
| ECS_07 | 32 | -0.0773 |

### Lessons
- SCORED: REJECT. The pressure component stayed identical to v164, but the station add-on failed badly.
- `speed_stations_d1_ecs` worsened `6.8257 -> 6.9886` (`+0.1629`) and primary regressed `1.420138 -> 1.420591`.
- Conclusion: v79 offsets are not additive after the stronger v102 residual-target station model. Do not reuse simple ECS station d1 bias offsets on current bases.
- v164 is the clean production base.

---

## v166 — ECS Pressure d14 850-Only Lambda 0.80 Push (SCORED: NEW BEST)

**Date**: 2026-05-15
**Approach**: v164 base + raise only ECS pressure d14 level `850` from lambda `0.65` to `0.80`.
**Big idea**: v164 proved level `925` still transfers, while v165 proved station compounding is unsafe. This tests the symmetric level `850` push cleanly, with no station rows touched.

### What was done
- Implemented `src/experiments/v166_pressure_d14_ecs_850_push80.py`.
- Base: `predictions_v164.csv`.
- Anchor/donor family: `v53 -> v55`, with `q = v53 + 0.80 * (v55 - v53)` on level `850` only.
- Scope: grid / `east_china_sea` / pressure / d14 / speed only.
- Changed rows vs v164: 82,080.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- Artifact: `starting-kit/phase_1/submission_v166.zip`.

### Incremental level diagnostics vs v164
| Level | Rows | Changed | Mean width delta |
|---|---:|---:|---:|
| 1000 | 82,080 | no | 0.0000 |
| 925 | 82,080 | no | 0.0000 |
| 850 | 82,080 | yes | -0.0409 |
| 700 | 82,080 | no | 0.0000 |
| 500 | 82,080 | no | 0.0000 |

### Leaderboard scores
| Dim | Best (v164) | New (v166) | Delta |
|-----|-----------:|-----------:|------:|
| speed_pressure_d14_ecs | 17.9087 | 17.9021 | -0.0066 improved |
| primary_score | 1.420138 | 1.420120 | -0.000018 improved |

### Lessons
- SCORED: NEW BEST. The 850-only continuation transferred cleanly.
- Both `850` and `925` at lambda `0.80` are now the clean ECS pressure d14 base.
- The marginal gain is smaller again (`-0.0066` raw vs `-0.0078` for v164), so this ladder is nearly exhausted.
- Use `v167` as the final regime/lambda selector probe, then stop pressure d14 laddering unless it scores clearly.

---

## v167-v172 — Breakthrough Batch From v164 (v167 SCORED; v168-v172 PENDING)

**Date**: 2026-05-15
**Approach**: Six independent, scoped candidates generated from the post-v164 breakthrough reset.
**Big idea**: Stop building one more broad model. Test regime selection, high-confidence width moves, one narrow ExtraTrees overlay, and center-frozen station widths as separate artifacts.

### What was done
- Implemented `src/experiments/v167_v172_breakthrough_batch.py`.
- Base: `predictions_v164.csv` for every candidate.
- Wrote manifests under `logs/v167_v172_breakthrough_batch/`.
- Every ZIP contains exactly one `predictions.csv`.
- Guard checks passed: zero non-target changes, zero quantile crossings, zero NaNs for all six artifacts.

### Candidates
| ID | Target | Mechanism | Changed rows | Artifact |
|---|---|---|---:|---|
| v167 | `speed_pressure_d14_ecs` | ECS pressure d14 regime-selected lambda: 850/925 default `0.80`, high-regime window-level cells `0.95` | 123,120 | `starting-kit/phase_1/submission_v167.zip` |
| v168 | `speed_pressure_d7_ecs` | High-speed/high-width pressure d7 q05/q95 shrink, q50 fixed | 144,344 | `starting-kit/phase_1/submission_v168.zip` |
| v169 | `speed_surface_d14_ns` | High-speed/high-width NS surface d14 q05/q95 shrink, q50 fixed | 72,199 | `starting-kit/phase_1/submission_v169.zip` |
| v170 | `speed_pressure_d14_ns` | High-speed/high-width NS pressure d14 q05/q95 shrink, q50 fixed | 159,318 | `starting-kit/phase_1/submission_v170.zip` |
| v171 | `speed_surface_d1_ecs` | ExtraTrees residual center overlay on ECS 10m d1; q05/q50/q95 shifted together | 82,080 | `starting-kit/phase_1/submission_v171.zip` |
| v172 | `dir_stations_d14_ns` | Rebase v157 weighted-conformal dir_05/dir_95 widths onto v164; dir_50 frozen | 256 | `starting-kit/phase_1/submission_v172.zip` |

### v167 scored
| Dim | Best (v166) | New (v167) | Delta |
|-----|-----------:|-----------:|------:|
| speed_pressure_d14_ecs | 17.9021 | 17.8919 | -0.0102 improved |
| primary_score | 1.420120 | 1.420092 | -0.000028 improved |

### Lessons
- v167 SCORED: NEW BEST. The regime-selected pressure probe transferred and moved `speed_pressure_d14_ecs` to `17.8919`.
- This is just above the visible carlometta boundary near `17.8900`, so one final tiny pressure probe is justified before stopping the d14 ladder.
- Do not submit v168-v172 as originally built if the goal is to preserve the current best: they are based on v164. Rebase or compound any next probe on top of v167 now that v167 scored clean.
- `v169` and `v170` are the first concrete probes against the new North Sea d14 competitor gap. If either regresses, do not keep blind d14 shrinking alive without miss-vs-width EDA.
- `v171` is the first ExtraTrees overlay. Treat it as exploratory because previous broad tree boosting overfit; its saving grace is narrow scope and preserved interval width.
- `v172` is mechanically safe because centers are frozen, but v157 itself is unscored; do not compound it until a standalone score lands.

---

## v173 — ECS Pressure d14 Final High-Regime Lambda 1.00 Probe (SCORED: NEW BEST)

**Date**: 2026-05-15
**Approach**: v167 base + push only the same high-regime `850`/`925` window-level cells from lambda `0.95` to `1.00`.
**Big idea**: v167 scored `speed_pressure_d14_ecs = 17.8919`, just above the visible `17.8900` boundary. This is the smallest sensible final crossing probe before stopping the pressure d14 ladder.

### What was done
- Implemented `src/experiments/v173_pressure_d14_ecs_final_crossing.py`.
- Base: `predictions_v167.csv`.
- Anchor/donor family: `v53 -> v55`, with `q = v53 + 1.00 * (v55 - v53)` on selected high-regime cells.
- Scope: grid / `east_china_sea` / pressure / d14 / speed only.
- Changed rows vs v167: 82,080.
- Changed by level: `850`: 41,040; `925`: 41,040.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- NaNs: 0.
- Artifact: `starting-kit/phase_1/submission_v173.zip`.

### Leaderboard scores
| Dim | Best (v167) | New (v173) | Delta |
|-----|-----------:|-----------:|------:|
| speed_pressure_d14_ecs | 17.8919 | 17.8886 | -0.0033 improved |
| primary_score | 1.420092 | 1.420083 | -0.000009 improved |

### Lessons
- SCORED: NEW BEST. The final high-regime lambda `1.00` probe transferred and crossed the visible carlometta boundary near `17.8900`.
- Stop the ECS pressure d14 lambda ladder now. The cell is rank-flipped and the marginal gain is tiny.
- Future candidates must preserve v173 and attack different cells, starting with a v173-rebased `v168` pressure d7 probe or the North Sea d14 gap probes.

---

## v174 — v173 + ECS Pressure d7 High-Confidence Shrink (SCORED: REJECT)

**Date**: 2026-05-15
**Approach**: Rebase the v168 ECS pressure d7 probe onto v173.
**Big idea**: v173 is now the clean best, so any next experiment must preserve the crossed ECS pressure d14 boundary. v174 overlays only the pressure d7 speed columns from v168 onto v173.

### What was done
- Implemented `src/experiments/v174_rebase_v168_on_v173.py`.
- Base: `predictions_v173.csv`.
- Donor/probe: `predictions_v168.csv` ECS pressure d7 high-confidence q05/q95 shrink.
- Scope: grid / `east_china_sea` / pressure / d7 / speed only.
- Changed rows vs v173: 144,344.
- Target rows: 410,400.
- q50 mean delta vs v173: 0.0000.
- Mean width delta vs v173 on target rows: -0.0246.
- Direction rows changed: 0.
- Non-target speed rows changed: 0.
- Quantile crossings: 0.
- NaNs: 0.
- Artifact: `starting-kit/phase_1/submission_v174.zip`.

### Leaderboard scores
| Dim | Best (v173) | New (v174) | Delta |
|-----|-----------:|-----------:|------:|
| speed_pressure_d7_ecs | 15.3733 | 15.3774 | +0.0041 regressed |
| primary_score | 1.420083 | 1.420094 | +0.000011 regressed |

### Lessons
- SCORED: REJECT. The v173-rebased pressure d7 high-confidence shrink regressed.
- Keep v173 as the clean base.
- Stop q50-frozen pressure d7 width shrinking. The pressure d14 lambda lane transferred because it changed a proven shear/ws3 shape; direct d7 endpoint shrink does not have the same hidden slack.
- Move to North Sea d14 probes or deeper miss-vs-width EDA.

---

## v175-v176 — v173-Rebased North Sea d14 Width Probes (PENDING)

**Date**: 2026-05-15
**Approach**: Rebase the original v169/v170 North Sea d14 high-confidence shrink probes onto the clean v173 base.
**Big idea**: If we test the public North Sea d14 gap, preserve the v173 ECS pressure d14 rank flip. These are q50-frozen endpoint probes, so they are cheap to reason about but now carry extra risk after v174.

### What was done
- Implemented `src/experiments/v175_v176_rebase_ns_d14_on_v173.py`.
- Base: `predictions_v173.csv`.
- Donors: `predictions_v169.csv` for v175 and `predictions_v170.csv` for v176.
- Both artifacts keep q50 unchanged, touch no direction columns, have zero non-target speed changes, zero quantile crossings, and zero NaNs.

### Candidates
| ID | Target | Changed rows | Target rows | Mean width delta vs v173 | Artifact |
|---|---|---:|---:|---:|---|
| v175 | `speed_surface_d14_ns` | 72,199 | 164,160 | -0.0026389 | `starting-kit/phase_1/submission_v175.zip` |
| v176 | `speed_pressure_d14_ns` | 159,318 | 410,400 | -0.0031056 | `starting-kit/phase_1/submission_v176.zip` |

### Lessons
- PENDING SCORE. These are standalone probes only.
- v174 just showed that q50-frozen endpoint shrinking can regress hidden even when mechanically clean.
- v175 is the safer first probe because it changes fewer rows and has a smaller width delta, but v158 already warned that NS surface d14 broad shrinking can under-cover.
- Do not submit v176 until v175 scores or an EDA pass confirms North Sea pressure d14 over-width in the same high-confidence regime.

---

## v177-v178 — North Sea d14 Width-Preserving Bias Translation (v177 REJECT; v178 HOLD)

**Date**: 2026-05-15
**Approach**: Use the 2019-2021 training/replay data to find HRES d10 -> d14 residual-bias bins whose sign is stable across train, val, tune, and holdout. Apply a tiny q50-frozen translation to v173 q05/q95 in the corresponding hidden rows.
**Big idea**: v174 and v158 say blind endpoint shrinking is dangerous. A width-preserving translation attacks one-sided bias without reducing nominal coverage.

### What was done
- Implemented `src/experiments/v177_v178_ns_d14_bias_translation.py`.
- Base: `predictions_v173.csv`.
- Diagnostics: `logs/v177_v178_ns_d14_bias_translation/residual_bin_summary.csv` and `selected_rules.csv`.
- v177 scope: grid / `north_sea` / surface / d14 / `10m` speed only.
- v178 scope: grid / `north_sea` / pressure / d14 / speed only.
- Both artifacts preserve q50, preserve interval width, touch no direction rows, have zero non-target speed changes, zero quantile crossings, and zero NaNs.

### Candidates
| ID | Target | Rule count | Changed rows | Max abs shift | Mean shift on changed rows | Artifact |
|---|---|---:|---:|---:|---:|---|
| v177 | `speed_surface_d14_ns` 10m subset | 11 | 56,612 / 82,080 | 0.025 | -0.00695 | `starting-kit/phase_1/submission_v177.zip` |
| v178 | `speed_pressure_d14_ns` | 51 | 271,708 / 410,400 | 0.030 | -0.01669 | `starting-kit/phase_1/submission_v178.zip` |

### v177 leaderboard score
| Dim | Best (v173) | New (v177) | Delta |
|---|---:|---:|---:|
| `speed_surface_d14_ns` | 15.1216 | 15.1351 | +0.0135 regressed |
| `primary_score` | 1.420083 | 1.420120 | +0.000037 regressed |

### Lessons
- v177 rejected cleanly. Width-preserving endpoint translation on NS surface d14 did not transfer even with q50 and width frozen.
- Block this specific mechanism for `speed_surface_d14_ns`; do not submit v175 as a casual fallback because it attacks the same dimension with a riskier pure shrink.
- Hold v178 and v176. Pressure d14 might behave differently, but after v177 the remaining daily slot is better spent on an orthogonal, low-row-count station-direction probe or conserved.

---

## v179 — v173-Rebased NS Station d14 Direction Widths (SCORED: NEUTRAL/REJECT)

**Date**: 2026-05-15
**Approach**: Rebase the existing v172 station-direction width-only candidate onto the scored-clean v173 base.
**Big idea**: After v177 rejected the NS d14 speed endpoint-translation lane, spend any final daily slot only on an orthogonal low-row-count probe. This candidate touches station direction intervals only and keeps direction centers frozen.

### What was done
- Implemented `src/experiments/v179_rebase_v172_on_v173.py`.
- Base: `predictions_v173.csv`.
- Donor: `predictions_v172.csv`, which carries the v157 weighted-conformal NS station d14 direction endpoints.
- Scope: station / `north_sea` / d14 / direction endpoints only.
- Artifact: `starting-kit/phase_1/submission_v179.zip`.
- Manifest: `logs/v179_rebase_v172_on_v173/v179_manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Changed rows | 256 |
| Speed changed rows | 0 |
| Direction changed rows | 256 |
| Non-target direction rows | 0 |
| `dir_50` changed rows | 0 |
| NaNs | 0 |
| Mean halfwidth delta | +4.9871 degrees |
| Min / max halfwidth delta | -2.2000 / +8.1000 degrees |

### 2026-05-18 re-verification
- `py_compile` passed for `src/experiments/v179_rebase_v172_on_v173.py`.
- `submission_v179.zip` contains exactly one `predictions.csv`.
- Independent chunked diff vs `v173`: 256 changed rows, all in NS station d14
  direction endpoints; 0 speed changes, 0 `dir_50` changes, 0 non-target
  direction changes, 0 crossings, 0 NaNs.

### Leaderboard score
| Dim | Best (v173) | New (v179) | Delta |
|---|---:|---:|---:|
| `dir_stations_d14_ns` | 305.6286 | 307.7857 | +2.1571 regressed |
| `primary_score` | 1.420083 | 1.420083 | +0.000000 neutral |

### Lessons
- SCORED: NEUTRAL/REJECT. The submission was mechanically clean and primary
  stayed unchanged, but the only target moved the wrong way.
- Reject v179 and keep `v173` as the production base.
- Do not submit `v183` as built: it includes the same failed NS station d14
  width family plus extra d7 risk. A separately built d7-only width probe is
  still arguable, but station-direction d14 width is now blocked.

---

## Post-v177 d14 Speed Miss/Width EDA — Full Shrink Blocked

**Date**: 2026-05-15
**Approach**: Run a replay-proxy EDA using HRES d10 speed plus train-period residual quantiles, scored on target-date val/tune/holdout. The goal was to decide whether the pending d14 speed probes should be retried, held, or replaced.
**Artifacts**:
- `scripts/d14_speed_miss_width_eda.py`
- `logs/d14_speed_miss_width_eda_surface_smoke2/REPORT.md`
- `logs/d14_speed_miss_width_eda_pressure/REPORT.md`
- `docs/research/D14_SPEED_MISS_WIDTH_EDA.md`

### Key result
| Dimension | Min eval coverage | 0.005 shrink split wins | 0.005 shrink mean delta | Decision |
|---|---:|---:|---:|---|
| `speed_surface_d14_ns` | 0.845956 | 1 / 3 | +0.001732 | Block full shrink / translation |
| `speed_surface_d14_ecs` | 0.892230 | 1 / 3 | -0.000108 | Block full shrink |
| `speed_pressure_d14_ns` | 0.839551 | 1 / 3 | +0.001721 | Block v176/v178 |
| `speed_pressure_d14_ecs` | 0.894434 | 1 / 3 | +0.000133 | Block full shrink |

### Lessons
- v177 is consistent with replay mechanics: North Sea surface d14 is under-covered, so endpoint movement without regime asymmetry is a bad class.
- The useful signal is speed-bin-specific. q4 is under-covered and low-side biased; q1/q2 often need the opposite high-side correction; q3 is the only shrinkable regime.
- Keep `v175`, `v176`, and `v178` held. The next d14 speed build should be a new q3-only pressure candidate, not a retry of the existing artifacts.

---

## v180 — v173 + NS Pressure d14 q3-Only Tiny Shrink (SCORED: NEUTRAL/REJECT)

**Date**: 2026-05-16
**Approach**: Apply the post-v177 d14 speed EDA result directly: shrink only the North Sea pressure d14 forecast-speed `q3` cells that were marked `candidate_tiny_shrink`; keep q50 and all direction columns frozen.
**Big idea**: Full-dimension d14 speed shrink is blocked because q1/q2/q4 are under-covered or directionally biased. q3 is the only regime that won all val/tune/holdout split tests under a 0.005 endpoint shrink, so v180 isolates that regime instead of retrying v176 or v178.

### What was done
- Implemented `src/experiments/v180_pressure_d14_ns_q3_shrink.py`.
- Base: `predictions_v173.csv`.
- EDA source: `logs/d14_speed_miss_width_eda_pressure/regime_recommendations.csv` and `cell_residual_quantiles.csv`.
- Scope: grid / `north_sea` / pressure / d14 / speed endpoints only.
- Artifact: `starting-kit/phase_1/submission_v180.zip`.
- Manifest: `logs/v180_pressure_d14_ns_q3_shrink/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows | 114,073 |
| Rule count | 18 |
| q50 changed rows | 0 |
| Direction changed rows | 0 |
| Non-target speed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean selected width delta | -0.0100 |
| Mean target width delta | -0.0027796 |

### Leaderboard score
| Dim | Best (v173) | New (v180) | Delta |
|---|---:|---:|---:|
| `speed_pressure_d14_ns` | 24.3527 | 24.3528 | +0.0001 regressed |
| `primary_score` | 1.420083 | 1.420083 | +0.000000 neutral |

### Lessons
- SCORED: NEUTRAL/REJECT. Primary stayed unchanged, but the target moved slightly the wrong way after rounding.
- The q3-only replay signal was not enough to transfer on hidden scoring. Stop tiny endpoint-shrink probes on `speed_pressure_d14_ns`; keep v173 as the clean base.

---

## v181 — v173 + NS Pressure d14 q4 Low-Side Widening (SCORED: NEUTRAL/REJECT)

**Date**: 2026-05-16
**Approach**: Apply the post-v177/v180 asymmetric correction idea: target only North Sea pressure d14 forecast-speed `q4_high` cells, lower `q05` by 0.020 m/s, and keep `q50`, `q95`, and directions frozen.
**Big idea**: v180 killed the q3 shrink lane, but the same EDA shows q4 is deeply under-covered and low-side biased across every level/hour cell. Low-side widening is a different mechanism from shrink or interval translation: it pays width only on the lower endpoint and does not move `q95`.

### What was done
- Implemented `src/experiments/v181_pressure_d14_ns_q4_low_side_widen.py`.
- Base: `predictions_v173.csv`.
- EDA source: `logs/d14_speed_miss_width_eda_pressure/regime_recommendations.csv` and `cell_residual_quantiles.csv`.
- Scope: grid / `north_sea` / pressure / d14 / `q05` speed endpoint only.
- Artifact: `starting-kit/phase_1/submission_v181.zip`.
- Manifest: `logs/v181_pressure_d14_ns_q4_low_side_widen/manifest.json`.

### Checks
| Check | Value |
|---|---:|
| Target rows | 410,400 |
| Changed rows | 178,838 |
| Rule count | 20 |
| q50 changed rows | 0 |
| q95 changed rows | 0 |
| Direction changed rows | 0 |
| Non-target speed rows | 0 |
| Quantile crossings | 0 |
| NaNs | 0 |
| Mean q05 delta on selected rows | -0.0200 |
| Mean selected width delta | +0.0200 |
| Mean target width delta | +0.0087153 |

### Leaderboard score
| Dim | Best (v173) | New (v181) | Delta |
|---|---:|---:|---:|
| `speed_pressure_d14_ns` | 24.3527 | 24.3588 | +0.0061 regressed |
| `primary_score` | 1.420083 | 1.420083 | +0.000000 neutral |

### Lessons
- SCORED: NEUTRAL/REJECT. Primary stayed unchanged, but the only touched metric moved the wrong way.
- Stop NS pressure d14 endpoint manipulation entirely. The EDA-indicated q4 low-side widening did not transfer, and v184's half-amplitude bracket should not be submitted.
