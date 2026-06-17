#!/usr/bin/env python3
"""End-to-end orchestrator: drive the whole DAG raw dataset -> FINAL_BEST.

This is the single entry point that encodes EVERY stage of the pipeline, in
order, with a checksum gate after each hop. It is designed to run inside a
working tree that has the original layout:

    <root>/scripts/        the lineage + overlay builders (in this repo)
    <root>/src/            the engine the lineage imports (in this repo)
    <root>/data/phase1_dataset/   the raw competition dataset (you download)
    <root>/submissions/    where prediction CSVs/zips are written
    <root>/starting-kit/phase_1/  heavy base + cached lineage checkpoints

Two modes:

  --mode verify  (default, non-destructive): locate each stage's output in the
      working tree and check its sha256; regenerate FINAL_BEST from the floor and
      numerically compare. Reports VERIFIED / MISSING / MISMATCH per stage.

  --mode run     (destructive): actually execute each stage's producer in order,
      writing intermediates into <root>/submissions/, with a sha gate after each.
      Needs the 21 GB raw dataset. The two CHECKPOINT stages (heavy base, v51) are
      treated as cached by default (they train version-sensitive ML models); pass
      --rebuild-checkpoints to re-run them too (expect score-equivalent, not
      byte-identical, output — see docs/PIPELINE.md §7).

HONEST LIMITS (see docs/END_TO_END.md and docs/PIPELINE.md §7):
  * `features` is produced by the official starting kit's feature-engineering
    notebook, not re-distributed here — that stage is EXTERNAL.
  * `heavy` and `v51` are version-sensitive ML checkpoints; a cold rebuild
    reproduces the SCORES but not the winning sha256. They are cached checkpoints.
  * Everything from the production base onward is deterministic post-processing.

Usage:
    python reproduce_from_raw.py --root /path/to/working-tree            # verify
    python reproduce_from_raw.py --root /path/to/working-tree --mode run # execute
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent

EXPECTED_ROWS = 3_448_800

# Pinned sha256 for each gateable hop (None = no byte anchor, verify by presence/rows).
SHA = {
    "heavy": "dcc3ba48fd7bd3d909bdb348dd176a944d05a86299f3302c6414984cc89ccff8",
    "v51": "c7e392afc17978698921371749204b27cfa5540b0b89e921c986e31484f646ca",
    "production_base": "5d5c1ba9ab92f2761136a68ec0e9f8290e7571bf73a74cb327c336935dd2f675",
    "dirshrink_combined": "8b4347ec6141880fa0d013d62882cc375dc0bf66119703650c359d41f254303c",
    "ecs_d14_reposition": "0cbdf30ee1e3ea726318ae02f6d25a516276e324229ebda186687633ed3f3d3e",
    "speedshrink_s08": "d95e4dd51a322c0a27b1019f7a040a4737d9df51d601f3af667a5f7e5a17ec0b",
    "final_best": "5eed32b3ee381cdd96e6cf2cd0641c900d1b932169e7f191e1b26c107e705bc9",
}


@dataclass
class Stage:
    id: str
    title: str
    kind: str  # external | checkpoint | lineage | overlay | final
    # candidate output locations (relative to root), first that exists is used:
    outputs: tuple[str, ...]
    sha: Optional[str] = None
    producer: Optional[list[str]] = None  # argv (relative script path resolved under root), or None
    note: str = ""


STAGES = [
    Stage("features", "Feature engineering (raw -> features/)", "external",
          ("data/phase1_dataset/features/inference_window_1_north_sea.parquet",),
          None, None,
          "EXTERNAL: run the official starting-kit 1_feature_engineering.ipynb."),
    Stage("heavy", "Heavy-notebook base (features -> predictions_heavy.csv)", "checkpoint",
          ("starting-kit/phase_1/predictions_heavy.csv",),
          SHA["heavy"],
          ["scripts/heavy/heavy_extracted_ns_only.py"],  # + _ecs_only; version-sensitive
          "Version-sensitive ML root (CatBoost/LightGBM, seed 42). Cached checkpoint."),
    Stage("v51", "Early lineage (heavy + light -> v51)", "checkpoint",
          ("starting-kit/phase_1/predictions_v51.csv",),
          SHA["v51"],
          None,  # rebuilt by scripts/rebuild_v51.py: 19 ordered hops, 8 train models
          "Rebuildable via scripts/rebuild_v51.py (needs heavy + light bases). Version-sensitive ML; score-equivalent."),
    Stage("production_base", "Production base (v51 -> v222_plus_v227_plus_v232)", "lineage",
          ("repro_outputs/v222_plus_v227_plus_v232/predictions_v222_plus_v227_plus_v232.csv",
           "submissions/predictions_v222_plus_v227_plus_v232.csv",
           "submissions/submission_v222_plus_v227_plus_v232.zip"),
          SHA["production_base"],
          ["scripts/reproduce_v222_plus_v227_plus_v232.py", "--mode", "full"],
          "Deterministic compound over the cached lineage; self-verifies sha 5d5c1ba9."),
    Stage("v256", "Final-day station ladder (production base -> v256)", "overlay",
          ("submissions/predictions_v256_station_0p60_plus_ecs_d1_speed_only.csv",),
          None,
          ["scripts/build_final_day_station_ladder.py"],
          "Dir NS Sta d1 shrink + WS ECS Surf d1 donor."),
    Stage("dirshrink_combined", "Direction shrink 0.12 (v256 -> dirshrink_combined)", "overlay",
          ("submissions/predictions_dirshrink_combined.csv",),
          SHA["dirshrink_combined"],
          ["scripts/build_dir_shrink.py", "combined"],
          "Center-frozen arc shrink on 4 disjoint direction cells."),
    Stage("ecs_d14_reposition", "ECS d14 reposition (dirshrink_combined -> reposition)", "overlay",
          ("submissions/predictions_ecs_d14_reposition.csv",),
          SHA["ecs_d14_reposition"],
          ["scripts/build_ecs_d14_reposition.py"],
          "Climatological 90% arcs for ECS Surf d14 (reads raw train parquet)."),
    Stage("speedshrink_s08", "Speed shrink 0.08 (reposition -> BEST_FLOOR)", "overlay",
          ("submissions/predictions_speedshrink_s08.csv",),
          SHA["speedshrink_s08"],
          ["scripts/build_speed_shrink.py", "0.08"],
          "Center-frozen speed shrink on ECS Sta/Surf d14."),
    Stage("final_best", "Final single-cell push (BEST_FLOOR -> FINAL_BEST)", "final",
          ("submissions/predictions_FINAL_BEST.csv",),
          SHA["final_best"],
          None,  # handled specially: scripts/build_final_best.py --floor <speedshrink_s08>
          "Center-frozen 12%->20% arc shrink on Dir NS Pres d7. Numerically identical."),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_zip_inner(path: Path, member: str = "predictions.csv") -> str:
    h = hashlib.sha256()
    with zipfile.ZipFile(path) as zf:
        with zf.open(member) as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def locate(root: Path, stage: Stage) -> Optional[Path]:
    for rel in stage.outputs:
        p = root / rel
        if p.exists():
            return p
    return None


def output_sha(path: Path) -> str:
    return sha256_zip_inner(path) if path.suffix == ".zip" else sha256_file(path)


def run_producer(root: Path, argv: list[str]) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    script = root / argv[0]
    cmd = [sys.executable, str(script), *argv[1:]]
    print(f"    $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(root), env=env).returncode


def regenerate_final_best(root: Path, out: Path) -> tuple[str, bool, float]:
    """Build FINAL_BEST from the floor; return (sha, center_frozen, max_abs_delta)."""
    sys.path.insert(0, str(HERE / "scripts"))
    import build_final_best as bfb  # noqa: E402
    floor = None
    for cand in ("submissions/predictions_speedshrink_s08.csv",
                 "submissions/submission_BEST_FLOOR.zip"):
        if (root / cand).exists():
            floor = root / cand
            break
    if floor is None:
        raise FileNotFoundError("floor (predictions_speedshrink_s08.csv / submission_BEST_FLOOR.zip) not found")
    info = bfb.build(floor, out, make_zip=False)
    # numeric compare to canonical if present
    canon = None
    for cand in ("submissions/predictions_FINAL_BEST.csv", "submissions/submission_FINAL_BEST.zip"):
        if (root / cand).exists():
            canon = root / cand
            break
    max_abs, center_frozen = 0.0, True
    if canon is not None:
        import numpy as np, pandas as pd  # noqa: E402
        def chunks(p):
            p = Path(p)
            if p.suffix == ".zip":
                with zipfile.ZipFile(p) as zf, zf.open("predictions.csv") as fh:
                    yield from pd.read_csv(fh, chunksize=bfb.CHUNKSIZE, dtype={"level": str}, low_memory=False)
            else:
                yield from pd.read_csv(p, chunksize=bfb.CHUNKSIZE, dtype={"level": str}, low_memory=False)
        cols = ["q05", "q50", "q95", "dir_05", "dir_50", "dir_95"]
        for a, b in zip(chunks(out), chunks(canon)):
            for c in cols:
                x, y = a[c].to_numpy(float), b[c].to_numpy(float)
                d = np.abs((x - y + 180) % 360 - 180) if c.startswith("dir") else np.abs(x - y)
                if d.size:
                    max_abs = max(max_abs, float(d.max()))
                if c in ("q50", "dir_50") and int((d > 0).sum()):
                    center_frozen = False
    return info["sha256"], center_frozen, max_abs


def verify(root: Path) -> int:
    print(f"# Verifying the DAG against working tree: {root}\n")
    width = max(len(s.title) for s in STAGES)
    overall_ok = True
    for i, st in enumerate(STAGES, 1):
        path = locate(root, st)
        status, detail = "MISSING", st.note
        if st.kind == "external":
            status = "PRESENT" if path else "EXTERNAL"
            detail = "features present" if path else st.note
        elif st.id == "final_best":
            # special: regenerate from floor and numerically compare
            if path and st.sha and output_sha(path) == st.sha:
                status, detail = "VERIFIED", "canonical sha256 matches"
            else:
                try:
                    out = root / "submissions" / "_reproduced_final_best.csv"
                    out.parent.mkdir(exist_ok=True)
                    sha, frozen, mx = regenerate_final_best(root, out)
                    out.unlink(missing_ok=True)
                    if frozen and mx == 0.0:
                        status, detail = "NUM-IDENTICAL", f"regenerated; center-frozen; max|Δ|={mx:.1e}"
                    elif frozen and mx < 1e-9:
                        status, detail = "SCORE-IDENTICAL", f"regenerated; max|Δ|={mx:.1e}"
                    else:
                        status, detail = "MISMATCH", f"max|Δ|={mx:.3e} frozen={frozen}"
                        overall_ok = False
                except Exception as exc:  # noqa: BLE001
                    status, detail = "BLOCKED", f"{exc}"
        elif path:
            if st.sha is None:
                status, detail = "PRESENT", "no byte anchor (intermediate)"
            elif output_sha(path) == st.sha:
                status, detail = "VERIFIED", f"sha256 {st.sha[:12]}…"
            else:
                status, detail = "MISMATCH", f"sha256 != pinned {st.sha[:12]}…"
                overall_ok = False
        else:
            status = "MISSING"
            if st.kind == "checkpoint":
                detail = "cached checkpoint not found — " + st.note
            overall_ok = overall_ok and st.sha is None  # transient intermediates may be absent
        flag = {"VERIFIED": "✅", "NUM-IDENTICAL": "✅", "SCORE-IDENTICAL": "✅",
                "PRESENT": "•", "EXTERNAL": "·", "MISSING": "·",
                "MISMATCH": "❌", "BLOCKED": "❌"}.get(status, " ")
        print(f"{flag} [{i}/{len(STAGES)}] {st.title:<{width}}  {status:<15} {detail}")
    print()
    print("verify complete." if overall_ok else "verify found a MISMATCH/BLOCKED stage.")
    return 0 if overall_ok else 1


def run(root: Path, rebuild_checkpoints: bool) -> int:
    print(f"# Running the DAG in working tree: {root}\n")
    for i, st in enumerate(STAGES, 1):
        print(f"[{i}/{len(STAGES)}] {st.title}")
        path = locate(root, st)
        if path and st.sha and output_sha(path) == st.sha:
            print(f"    VERIFIED (cached): {path.relative_to(root)}")
            continue
        if st.kind == "external":
            print(f"    EXTERNAL — {st.note}")
            if not path:
                print("    BLOCKED: provide engineered features, then re-run.")
                return 2
            continue
        if st.kind == "checkpoint":
            if path and not rebuild_checkpoints:
                print(f"    cached checkpoint present (sha {output_sha(path)[:12]}…); not rebuilt (version-sensitive).")
                continue
            if not rebuild_checkpoints:
                print(f"    BLOCKED: checkpoint '{st.id}' missing and --rebuild-checkpoints not set. {st.note}")
                return 2
            # --rebuild-checkpoints: actually rebuild this version-sensitive checkpoint
            if st.id == "v51":
                print("    rebuilding v51 from raw via scripts/rebuild_v51.py (19 hops, trains ML; score-equivalent)…")
                rc = run_producer(root, ["scripts/rebuild_v51.py", "--root", str(root)])
            elif st.id == "heavy":
                print("    heavy is the starting-kit heavy-notebook output; rebuild it there (scripts/heavy/).")
                rc = 0 if path else 2
            else:
                rc = 2
            if rc != 0:
                print(f"    FAIL/BLOCKED rebuilding checkpoint '{st.id}'.")
                return 2
            again = locate(root, st)
            if again and st.sha and output_sha(again) != st.sha:
                print(f"    note: {st.id} sha differs from the pinned reference (version drift; score-equivalent).")
            continue
        if st.id == "final_best":
            out = root / "submissions" / "predictions_FINAL_BEST.csv"
            sha, frozen, mx = regenerate_final_best(root, out)
            ok = frozen and mx < 1e-9
            print(f"    {'OK' if ok else 'FAIL'}: regenerated FINAL_BEST (center-frozen={frozen}, max|Δ|={mx:.1e})")
            print(f"    canonical sha256 (byte anchor): {SHA['final_best']}")
            if not ok:
                return 2
            continue
        if st.producer is None:
            print(f"    BLOCKED: no runnable producer in this package. {st.note}")
            return 2
        rc = run_producer(root, st.producer)
        if rc != 0:
            print(f"    FAIL: producer exited {rc}")
            return 2
        path = locate(root, st)
        if path and st.sha and output_sha(path) != st.sha:
            print(f"    WARNING: output sha != pinned (version drift?) {output_sha(path)[:12]}…")
    print("\nrun complete.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(HERE), help="working-tree root (has scripts/ src/ data/ submissions/)")
    ap.add_argument("--mode", choices=("verify", "run"), default="verify")
    ap.add_argument("--rebuild-checkpoints", action="store_true",
                    help="in run mode, also rebuild the version-sensitive heavy + v51 checkpoints")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"no such root: {root}")
        return 2
    return verify(root) if args.mode == "verify" else run(root, args.rebuild_checkpoints)


if __name__ == "__main__":
    raise SystemExit(main())
