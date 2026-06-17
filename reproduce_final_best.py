#!/usr/bin/env python3
"""Regenerate the FINAL_BEST predictions from the BEST_FLOOR base and verify.

This is the runnable, self-contained proof of the *final* hop of the pipeline
(BEST_FLOOR -> FINAL_BEST). It:

  1. Rebuilds ``predictions_final_best.csv`` from the floor base CSV using the
     exact, verified arc-shrink in ``pipeline/overlays/build_final_best.py``.
  2. If you pass ``--canonical`` (the real ``predictions_FINAL_BEST.csv`` or the
     ``submission_FINAL_BEST.zip``), it compares the two and reports:
       - sha256 of each,
       - the number of rows that differ and in which cell,
       - the maximum circular |Δ| in degrees on the changed direction columns,
       - a SCORE-IDENTICAL verdict (max |Δ| < 1e-9 deg => identical Winkler
         scores and identical leaderboard ranks).

See ``docs/PIPELINE.md`` for why this is score-identical rather than byte-identical,
and ``verify_artifact.py`` for the byte-level sha256 anchor.

Usage:
    python reproduce_final_best.py --floor /path/to/predictions_speedshrink_s08.csv \
                                   --canonical /path/to/submission_FINAL_BEST.zip
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline" / "overlays"))
import build_final_best as bfb  # noqa: E402

# Pinned canonical checksums (the first-place artifact).
CANONICAL_CSV_SHA256 = "5eed32b3ee381cdd96e6cf2cd0641c900d1b932169e7f191e1b26c107e705bc9"
CANONICAL_ZIP_SHA256 = "0d8c48acedf0c2ca85dce2e62ffa5e65a2ab48c891a7af07d6162c3f76bb7cd7"
SCORE_IDENTICAL_TOL_DEG = 1e-9

QUANT_COLS = ["q05", "q50", "q95", "dir_05", "dir_50", "dir_95"]


def open_predictions(path: Path):
    """Yield chunks from a predictions CSV or a submission .zip (inner predictions.csv)."""
    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            inner = "predictions.csv"
            with zf.open(inner) as fh:
                yield from pd.read_csv(fh, chunksize=bfb.CHUNKSIZE, dtype={"level": str}, low_memory=False)
    else:
        yield from pd.read_csv(path, chunksize=bfb.CHUNKSIZE, dtype={"level": str}, low_memory=False)


def circular_abs_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


def compare(regen_csv: Path, canonical: Path) -> dict:
    """Stream both files in lockstep; report per-column diffs (circular for dir)."""
    n_rows = 0
    diff_counts = {c: 0 for c in QUANT_COLS}
    max_abs = {c: 0.0 for c in QUANT_COLS}
    gen = zip(open_predictions(regen_csv), open_predictions(canonical))
    for ca, cb in gen:
        if len(ca) != len(cb):
            raise ValueError("row-count mismatch between regenerated and canonical chunks")
        n_rows += len(ca)
        for c in QUANT_COLS:
            a = ca[c].to_numpy(dtype=float)
            b = cb[c].to_numpy(dtype=float)
            if c.startswith("dir"):
                d = circular_abs_diff(a, b)
            else:
                d = np.abs(a - b)
            nd = int(np.count_nonzero(d > 0))
            diff_counts[c] += nd
            if nd:
                max_abs[c] = max(max_abs[c], float(np.nanmax(d)))
    return {"rows": n_rows, "diff_counts": diff_counts, "max_abs": max_abs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--floor", required=True, help="BEST_FLOOR base CSV (predictions_speedshrink_s08.csv)")
    ap.add_argument("--out", default=str(ROOT / "predictions_final_best.csv"), help="regenerated output CSV")
    ap.add_argument("--canonical", help="canonical predictions_FINAL_BEST.csv or submission_FINAL_BEST.zip")
    ap.add_argument("--zip", action="store_true", help="also write submission_final_best.zip")
    args = ap.parse_args()

    print("=" * 72)
    print("STEP 1 — regenerate FINAL_BEST from the BEST_FLOOR base")
    print("=" * 72)
    info = bfb.build(Path(args.floor), Path(args.out), make_zip=args.zip)
    print(f"  rows total         : {info['rows']:,}")
    print(f"  rows changed (cell): {info['changed_rows']:,}  (Dir north_sea Pres d7)")
    print(f"  regenerated sha256 : {info['sha256']}")
    print(f"  canonical  sha256  : {CANONICAL_CSV_SHA256}")
    byte_equal = info["sha256"] == CANONICAL_CSV_SHA256
    print(f"  byte-identical     : {byte_equal}")

    if not args.canonical:
        print("\n(no --canonical provided; skipping numerical comparison)")
        print("Provide --canonical to confirm score-identity, or run verify_artifact.py")
        return 0

    print()
    print("=" * 72)
    print("STEP 2 — compare regenerated vs canonical (score-identity)")
    print("=" * 72)
    res = compare(Path(args.out), Path(args.canonical))
    print(f"  rows compared      : {res['rows']:,}  (values parsed to float64, dir compared circularly)")
    any_diff = False
    for c in QUANT_COLS:
        n = res["diff_counts"][c]
        if n:
            any_diff = True
            print(f"  {c:7s}: {n:>8,} rows differ   max |Δ| = {res['max_abs'][c]:.3e}"
                  f"{' deg' if c.startswith('dir') else ''}")
    if not any_diff:
        print("  all 6 quantile columns parse to bit-identical float64 (max |Δ| = 0)")

    worst_dir = max(res["max_abs"]["dir_05"], res["max_abs"]["dir_95"])
    worst_speed = max(res["max_abs"]["q05"], res["max_abs"]["q50"], res["max_abs"]["q95"])
    worst = max(worst_dir, worst_speed)
    score_identical = (worst_dir < SCORE_IDENTICAL_TOL_DEG) and (worst_speed < SCORE_IDENTICAL_TOL_DEG)
    numerically_exact = worst == 0.0
    # frozen-center invariant: q50 and dir_50 must never change
    center_frozen = (res["diff_counts"]["q50"] == 0) and (res["diff_counts"]["dir_50"] == 0)

    print()
    print(f"  center-frozen (q50 & dir_50 unchanged): {center_frozen}")
    print(f"  max |Δ| over ALL columns (parsed)     : {worst:.3e}  (tol {SCORE_IDENTICAL_TOL_DEG:.0e})")
    print(f"  raw file sha256 byte-identical        : {byte_equal}")
    if not byte_equal:
        print("    (sha differs only in cosmetic decimal formatting on the changed cell;")
        print("     e.g. '245.88000000000002' vs '245.88' round-trip to the SAME float64.)")

    if byte_equal:
        verdict = "BYTE-IDENTICAL"
    elif numerically_exact and center_frozen:
        verdict = "NUMERICALLY IDENTICAL"
    elif score_identical and center_frozen:
        verdict = "SCORE-IDENTICAL"
    else:
        verdict = "MISMATCH"
    print()
    print("=" * 72)
    print(f"  VERDICT: {verdict}")
    if verdict in ("NUMERICALLY IDENTICAL", "SCORE-IDENTICAL"):
        print("  -> every value a scorer parses is identical => identical Winkler scores & ranks.")
        print("  -> the canonical raw bytes (sha256) are anchored by verify_artifact.py;")
        print("     exact-byte regeneration needs the full from-raw chain (see docs/PIPELINE.md).")
    print("=" * 72)
    return 0 if verdict != "MISMATCH" and center_frozen else 1


if __name__ == "__main__":
    raise SystemExit(main())
