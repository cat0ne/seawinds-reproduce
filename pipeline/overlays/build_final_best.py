#!/usr/bin/env python3
"""Final-slot single-cell direction push -> the FINAL_BEST submission.

This is the last hop of the build DAG (see ../../docs/PIPELINE.md). It was the
ad-hoc final-slot edit that produced ``submission_FINAL_BEST.zip``; no committed
script in the original working repo emitted it, so it is reconstructed here from
the exact, verified arithmetic of the project's other direction-shrink builders
(``build_dir_shrink.py`` / ``build_combined_dir_push.py``).

WHAT IT DOES
------------
Starting from the "BEST_FLOOR" base (``predictions_speedshrink_s08.csv``, the
output of ``build_speed_shrink.py 0.08``), it applies a *center-frozen circular
arc shrink* to exactly ONE of the 36 scored cells:

    Dir  North Sea  Pressure-level grid  d7   (region=north_sea, Pres, horizon=7)

The arc [dir_05, dir_95] is shrunk toward its own midpoint; ``dir_50`` (the
forecast direction) is NOT touched, and no other cell or column changes. The cell
was already shrunk to 12% on the floor (by ``build_dir_shrink.py`` upstream); this
hop takes it to a total of 20%, i.e. an *additional* fraction of the current arc:

    additional_fraction = (0.20 - 0.12) / (1 - 0.12) = 1/11 = 0.0909090909...

The direction Winkler score uses only the [dir_05, dir_95] interval, so shrinking
an over-wide, well-covered arc lowers width (and thus the score) on that cell.
On the hidden 2022 board this moved Dir NS Pressure d7 from 247.53 -> 246.11.

BYTE- vs NUMERICAL IDENTITY (read this)
---------------------------------------
The canonical ``predictions_FINAL_BEST.csv`` (sha256 5eed32b3...) computed this
cell as a ONE-STEP 20% shrink of the *unshrunk* upstream base (v256), then grafted
the result onto the floor. Re-deriving it from the on-disk 12%-shrunk floor uses a
mathematically-equal but differently-ordered float multiply that differs in-memory
by at most ~2.8e-14 degrees (1 ULP). When written to CSV and parsed back, every
value rounds to the SAME float64 as the canonical file, so the regenerated
predictions are *numerically identical* to a scorer (identical Winkler scores and
ranks). The raw file sha256 still differs, because pandas writes a few of the
changed values with a longer-but-equivalent decimal string (e.g. '245.88000000000002'
vs '245.88', which parse to the same double). Exact-byte regeneration of the
canonical sha256 requires running the full deterministic chain from the
heavy-notebook base so the unshrunk v256 arc carries its exact float values through
(see ../../docs/PIPELINE.md). ``reproduce_final_best.py`` checks numerical identity;
``verify_artifact.py`` anchors the canonical bytes by sha256.

Usage:
    python build_final_best.py --floor predictions_speedshrink_s08.csv \
                               --out   predictions_final_best.csv [--zip]
"""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SURFACE_LEVELS = {"10m", "100m"}

# The single target cell and its shrink fractions.
TARGET_REGION = "north_sea"
TARGET_SOURCE = "Pres"          # pressure-level grid (level not in {10m, 100m})
TARGET_HORIZON = 7
CURRENT_FRACTION = 0.12         # already applied on the floor by build_dir_shrink.py
TARGET_FRACTION = 0.20          # total shrink after this hop
ADDITIONAL_FRACTION = (TARGET_FRACTION - CURRENT_FRACTION) / (1.0 - CURRENT_FRACTION)

CHUNKSIZE = 200_000
EXPECTED_ROWS = 3_448_800


def source_of(row_type: str, level: str) -> str:
    """Map a row to its data-source family: station / surface grid / pressure grid."""
    if row_type == "station":
        return "Sta"
    return "Surf" if level in SURFACE_LEVELS else "Pres"


def apply_arc_shrink(chunk: pd.DataFrame, mask: pd.Series, additional_fraction: float) -> int:
    """Center-frozen circular arc shrink on [dir_05, dir_95]; returns rows changed.

    Identical arithmetic to build_dir_shrink.py / build_combined_dir_push.py.
    """
    if additional_fraction <= 0.0 or not bool(mask.any()):
        return 0
    idx = chunk.index[mask]
    lower = chunk.loc[idx, "dir_05"].astype(float).to_numpy()
    upper = chunk.loc[idx, "dir_95"].astype(float).to_numpy()
    width = (upper - lower) % 360.0
    mid = (lower + width / 2.0) % 360.0
    new_half_width = (width / 2.0) * (1.0 - additional_fraction)
    chunk.loc[idx, "dir_05"] = (mid - new_half_width) % 360.0
    chunk.loc[idx, "dir_95"] = (mid + new_half_width) % 360.0
    return int(len(idx))


def build(floor_csv: Path, out_csv: Path, make_zip: bool = False) -> dict:
    """Regenerate the FINAL_BEST predictions from the BEST_FLOOR base CSV."""
    floor_csv = Path(floor_csv)
    out_csv = Path(out_csv)
    if not floor_csv.exists():
        raise FileNotFoundError(floor_csv)
    out_csv.unlink(missing_ok=True)

    wrote = False
    total_rows = 0
    changed_rows = 0
    for chunk in pd.read_csv(floor_csv, chunksize=CHUNKSIZE, dtype={"level": str}, low_memory=False):
        level = chunk["level"].fillna("").astype(str)
        src = np.where(
            chunk["type"] == "station",
            "Sta",
            np.where(level.isin(SURFACE_LEVELS), "Surf", "Pres"),
        )
        mask = (
            (chunk["region"] == TARGET_REGION)
            & (chunk["horizon"].astype(int) == TARGET_HORIZON)
            & (src == TARGET_SOURCE)
        )
        changed_rows += apply_arc_shrink(chunk, pd.Series(mask, index=chunk.index), ADDITIONAL_FRACTION)
        total_rows += len(chunk)
        chunk.to_csv(out_csv, mode="w" if not wrote else "a", index=False, header=not wrote)
        wrote = True

    digest = sha256_file(out_csv)
    zip_path = None
    if make_zip:
        zip_path = out_csv.with_suffix("").with_name("submission_final_best.zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            zf.write(out_csv, arcname="predictions.csv")

    return {
        "out_csv": str(out_csv),
        "rows": total_rows,
        "changed_rows": changed_rows,
        "additional_fraction": ADDITIONAL_FRACTION,
        "sha256": digest,
        "zip": str(zip_path) if zip_path else None,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--floor", required=True, help="BEST_FLOOR base CSV (predictions_speedshrink_s08.csv)")
    ap.add_argument("--out", default="predictions_final_best.csv", help="output predictions CSV path")
    ap.add_argument("--zip", action="store_true", help="also write submission_final_best.zip")
    args = ap.parse_args()

    info = build(Path(args.floor), Path(args.out), make_zip=args.zip)
    print(f"target cell        : Dir {TARGET_REGION} {TARGET_SOURCE} d{TARGET_HORIZON} "
          f"({CURRENT_FRACTION:.0%} -> {TARGET_FRACTION:.0%}, additional {info['additional_fraction']:.10f})")
    print(f"rows total         : {info['rows']:,}")
    print(f"rows changed (cell): {info['changed_rows']:,}")
    print(f"output             : {info['out_csv']}")
    print(f"output sha256      : {info['sha256']}")
    if info["zip"]:
        print(f"zip                : {info['zip']}")
    if info["rows"] != EXPECTED_ROWS:
        print(f"WARNING: expected {EXPECTED_ROWS:,} data rows, got {info['rows']:,}")


if __name__ == "__main__":
    main()
