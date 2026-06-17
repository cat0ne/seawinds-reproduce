#!/usr/bin/env python3
"""Verify a Sea Winds submission against the pinned checksum registry.

Checks the byte-level identity (sha256) of a submission file against the known
checksums of the chain artifacts, and — for a submission .zip — that the inner
file is named ``predictions.csv`` and has the expected number of data rows.

This is the byte-level anchor for the first-place artifact: download
``submission_FINAL_BEST.zip`` from the GitHub Release and run

    python verify_artifact.py /path/to/submission_FINAL_BEST.zip

A PASS proves you hold the exact bytes that scored first place.

Usage:
    python verify_artifact.py <file.zip | file.csv> [--expect <name>]
    python verify_artifact.py --list
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import zipfile
from pathlib import Path

EXPECTED_DATA_ROWS = 3_448_800

# Pinned sha256 registry for the verified build DAG (see docs/CHECKSUMS.md).
REGISTRY = {
    # ----- the first-place artifact -----
    "submission_FINAL_BEST.zip":        "0d8c48acedf0c2ca85dce2e62ffa5e65a2ab48c891a7af07d6162c3f76bb7cd7",
    "predictions_FINAL_BEST.csv":       "5eed32b3ee381cdd96e6cf2cd0641c900d1b932169e7f191e1b26c107e705bc9",
    # ----- the floor chain (each hop is on-disk verifiable) -----
    "submission_BEST_FLOOR.zip":        "17bde40362671bac983d21559394b9dc6322689dbf0456c75ef04ba62130f38e",
    "predictions_speedshrink_s08.csv":  "d95e4dd51a322c0a27b1019f7a040a4737d9df51d601f3af667a5f7e5a17ec0b",
    "predictions_ecs_d14_reposition.csv": "0cbdf30ee1e3ea726318ae02f6d25a516276e324229ebda186687633ed3f3d3e",
    "predictions_dirshrink_combined.csv": "8b4347ec6141880fa0d013d62882cc375dc0bf66119703650c359d41f254303c",
    # ----- the production base (deep-lineage output) -----
    "submission_v222_plus_v227_plus_v232.zip": "13c9fa055374733e757dbb396a5166ea0070f376d773fd348a28db54e9f1656f",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inner_csv_info(zip_path: Path) -> tuple[str, int]:
    """Return (inner_name, data_row_count) for a submission zip."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if "predictions.csv" not in names:
            raise ValueError(f"zip does not contain predictions.csv (has: {names})")
        rows = 0
        with zf.open("predictions.csv") as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8")
            for _ in text:
                rows += 1
        return ("predictions.csv", rows - 1)  # minus header


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="submission .zip or predictions .csv to verify")
    ap.add_argument("--expect", help="registry name to check against (default: match by filename)")
    ap.add_argument("--list", action="store_true", help="print the checksum registry and exit")
    args = ap.parse_args()

    if args.list or not args.path:
        print("Pinned sha256 registry:")
        for name, digest in REGISTRY.items():
            print(f"  {digest}  {name}")
        return 0

    path = Path(args.path)
    if not path.exists():
        print(f"FAIL: no such file: {path}")
        return 2

    digest = sha256_file(path)
    key = args.expect or path.name
    print(f"file   : {path}")
    print(f"sha256 : {digest}")

    if path.suffix == ".zip":
        try:
            inner, rows = inner_csv_info(path)
            ok_rows = rows == EXPECTED_DATA_ROWS
            print(f"inner  : {inner}  ({rows:,} data rows, expected {EXPECTED_DATA_ROWS:,}: {ok_rows})")
        except Exception as exc:  # noqa: BLE001
            print(f"inner  : could not read inner csv: {exc}")

    expected = REGISTRY.get(key)
    if expected is None:
        print(f"NOTE   : '{key}' is not in the registry; sha256 reported above (use --expect to pin).")
        return 0
    if digest == expected:
        print(f"PASS   : matches pinned '{key}'.")
        return 0
    print(f"FAIL   : does NOT match pinned '{key}'")
    print(f"         expected {expected}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
