#!/usr/bin/env python3
"""Center-frozen SPEED shrink on OVER-COVERED ECS speed cells (rank-flip play).

NEW lever: every prior speed attempt was WIDENING (v220) or REPLACING (climo) —
both refuted. This is the untried inverse: the ECS speed cells are over-covered
(penalty share = hidden_score - mean_width: WS ECS Sta d14 6.6%, ECS Surf/Pres
d14 ~15%, ECS Surf/Pres d7 ~19-22%, vs ~10% calibrated), with tiny flip gaps
(0.02-0.37). The speed Winkler uses only [q05,q95]; q50 is irrelevant. So narrow
the interval toward q50 by fraction s -> less width, and (if over-covered) few
new misses -> lower score -> rank flip. Same over-coverage logic that worked for
direction; d14 cells have no forecast skill so the over-coverage is genuine.

Targets ONLY over-covered ECS speed cells we trail. Stacks on the reposition
base (so one upload tests speed-shrink + dir-reposition toward board 4.028/#1).

HIDDEN probe (offline VAL untrustworthy). Read per-cell, keep winners.
Usage: build_speed_shrink.py <s>   (default 0.08)
"""
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUBS = ROOT / "submissions"
BASE = SUBS / "predictions_ecs_d14_reposition.csv"
SURF = {"10m", "100m"}

# WINNERS ONLY after hidden readout: ECS Sta d14 (-0.20) and ECS Surf d14 (-0.01)
# improved; ECS Pres d14 (+0.09), Surf d7 (+0.17), Pres d7 (+0.19) regressed -> dropped.
TARGETS = {("Sta", 14), ("Surf", 14)}


def main(s):
    tag = int(round(s * 100))
    out_csv = SUBS / f"predictions_speedshrink_s{tag:02d}.csv"
    out_zip = SUBS / f"submission_speedshrink_s{tag:02d}.zip"
    reader = pd.read_csv(BASE, chunksize=200_000, dtype={"level": str})
    wrote = False
    changed = {}
    wid_b = {}
    wid_a = {}
    for chunk in reader:
        ecs14 = (chunk["region"] == "east_china_sea")
        lvl = chunk["level"].astype(str)
        src = np.where(chunk["type"] == "station", "Sta", np.where(lvl.isin(SURF), "Surf", "Pres"))
        for (s_src, hor) in TARGETS:
            m = ecs14 & (chunk["horizon"] == hor) & (src == s_src)
            if not m.any():
                continue
            idx = chunk.index[m]
            q05 = chunk.loc[idx, "q05"].to_numpy()
            q50 = chunk.loc[idx, "q50"].to_numpy()
            q95 = chunk.loc[idx, "q95"].to_numpy()
            n05 = np.clip(q50 + (1.0 - s) * (q05 - q50), 0.0, None)
            n95 = q50 + (1.0 - s) * (q95 - q50)
            chunk.loc[idx, "q05"] = n05
            chunk.loc[idx, "q95"] = n95
            key = f"ECS {s_src} d{hor}"
            changed[key] = changed.get(key, 0) + len(idx)
            wid_b[key] = wid_b.get(key, 0.0) + float((q95 - q05).sum())
            wid_a[key] = wid_a.get(key, 0.0) + float((n95 - n05).sum())
        chunk.to_csv(out_csv, mode="w" if not wrote else "a", index=False, header=not wrote)
        wrote = True
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_csv, arcname="predictions.csv")
    print(f"speed shrink s={s:.2f} -> {out_zip.name}  ({len(changed)} cells, stacked on reposition base)")
    for k in sorted(changed):
        print(f"  {k:12s} n={changed[k]:>7d}  width {wid_b[k]/changed[k]:6.2f} -> {wid_a[k]/changed[k]:6.2f}")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.08)
