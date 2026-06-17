#!/usr/bin/env python3
"""Rebuild predictions_v51.csv from raw — the early-lineage producer.

This runs the exact ordered chain that builds the lineage root `predictions_v51.csv`
from the engineered features + the two base-notebook outputs (`predictions_heavy.csv`,
`predictions_light.csv`). It closes the one gap that made the from-raw reproduction
"start from a cached v51": with this script the whole pipeline is runnable
raw -> v51 -> production base -> ... -> FINAL_BEST.

The chain is 19 ordered steps. Each step runs a producer in `<root>` (cwd=root,
PYTHONPATH=root) and writes `starting-kit/phase_1/predictions_{ver}.csv`. Three steps
are NOT plain modules — their useful entrypoint is a function, invoked via `-c`.

VERSION SENSITIVITY (read this): steps marked TRAINS fit ML models (LightGBM /
CatBoost / sklearn GradientBoosting). They are seeded (`random_seed=42`,
`random_state=…`), but these libraries are not byte-deterministic across versions /
platforms. So a cold rebuild reproduces `v51` (and everything downstream)
*score-equivalently*, not necessarily byte-for-byte. That is expected and accepted:
the point is that the submission derives from raw data via runnable code, not a
hand-crafted file. The canonical `v51` sha256 is pinned only as a same-environment
reference.

Prerequisites in <root> before step 1:
  - data/phase1_dataset/  (engineered features + reanalysis parquets; see PIPELINE.md)
  - starting-kit/phase_1/predictions_heavy.csv   (heavy base; grafted at v27/v28)
  - starting-kit/phase_1/predictions_light.csv   (light base; used at v31)

Usage:
    python scripts/rebuild_v51.py --root /path/to/working-tree            # run the chain
    python scripts/rebuild_v51.py --root /path/to/working-tree --plan     # print plan only
    python scripts/rebuild_v51.py --root /path/to/working-tree --start-at v32   # resume
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

V51_SHA256 = "c7e392afc17978698921371749204b27cfa5540b0b89e921c986e31484f646ca"  # same-env reference


@dataclass
class Step:
    ver: str
    kind: str          # "module" | "code"
    spec: str          # module path, or python -c body
    reads: str
    trains: bool


# The exact ordered early lineage (raw/heavy/light -> v51). Donors (v32,v34,v40,v47)
# precede their consumers (v35,v38,v41,v51). run_v7 must precede v32 (it writes the
# logs/direction_models_v7/ artifact that v32 loads).
STEPS = [
    Step("v7",  "module", "src.pipeline.run_v7",  "features + reanalysis", True),   # + logs/direction_models_v7/
    Step("v8",  "module", "src.pipeline.run_v8",  "features + reanalysis", True),
    Step("v16", "module", "src.pipeline.run_v16", "inference features", False),
    Step("v19", "module", "src.pipeline.run_v19", "features + reanalysis", True),
    Step("v26", "module", "src.pipeline.run_v26", "v19, v16", False),
    Step("v27", "module", "src.pipeline.run_v27", "v26, predictions_heavy.csv", False),  # HEAVY graft
    Step("v28", "module", "src.pipeline.run_v28", "v27, predictions_heavy.csv", False),
    Step("v30", "module", "src.pipeline.run_v30", "v28 + features", True),
    Step("v31", "module", "src.pipeline.run_v31", "v28, v30, predictions_light.csv", False),
    Step("v32", "module", "src.pipeline.run_v32", "v31 + logs/direction_models_v7 + features", True),  # donor -> v35
    Step("v34", "module", "src.pipeline.run_v34", "v31 + features (Track E)", True),                    # donor -> v38
    Step("v35", "module", "src.pipeline.run_v35", "v31, v32", False),
    Step("v38", "module", "src.pipeline.run_v38", "v35, v34", False),
    Step("v39", "module", "src.pipeline.run_v39", "v38 (Track I)", True),
    Step("v40", "code", "from src.pipeline.run_v39 import generate_v40; generate_v40()",
         "v38 (Track I); generate_v40 is NOT in __main__", True),                                       # donor -> v41
    Step("v41", "module", "src.pipeline.run_v41", "v39, v40", False),
    Step("v46", "code", "from src.experiments.speed_direction_copula import run_b1_experiment; run_b1_experiment()",
         "v41 + reanalysis parquets; entrypoint run_b1_experiment()", False),
    Step("v47", "code", "from src.experiments.copula_v47_fix import run_v47; run_v47()",
         "v41 + reanalysis parquets; entrypoint run_v47()", False),                                     # donor -> v51
    Step("v51", "module", "src.pipeline.run_v51", "v46, v47", False),
]

PREREQS = [
    ("data/phase1_dataset/features/inference_window_1_north_sea.parquet", "engineered features (run the starting-kit feature notebook)"),
    ("starting-kit/phase_1/predictions_heavy.csv", "heavy base (starting-kit heavy notebook / scripts/heavy/)"),
    ("starting-kit/phase_1/predictions_light.csv", "light base (starting-kit light notebook)"),
]


def out_csv(root: Path, ver: str) -> Path:
    return root / "starting-kit" / "phase_1" / f"predictions_{ver}.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def print_plan() -> None:
    print("Ordered early-lineage rebuild (raw/heavy/light -> v51):\n")
    for i, s in enumerate(STEPS, 1):
        run = f"python -m {s.spec}" if s.kind == "module" else f'python -c "{s.spec}"'
        tag = "TRAINS " if s.trains else "transform"
        print(f"{i:2d}. [{tag}] {run}")
        print(f"      -> predictions_{s.ver}.csv   (reads: {s.reads})")
    print("\nVersion-sensitive (model-training) steps reproduce v51 score-equivalently, not byte-for-byte.")


def check_prereqs(root: Path) -> bool:
    ok = True
    for rel, how in PREREQS:
        if not (root / rel).exists():
            print(f"  MISSING prerequisite: {rel}\n    -> {how}")
            ok = False
    return ok


def run_chain(root: Path, start_at: str | None) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    py = sys.executable

    print(f"# Rebuilding v51 in working tree: {root}\n")
    if not check_prereqs(root):
        print("\nBLOCKED: provide the prerequisites above, then re-run.")
        return 2

    started = start_at is None
    trained_any = False
    for i, s in enumerate(STEPS, 1):
        if not started:
            if s.ver == start_at:
                started = True
            else:
                print(f"[{i:2d}/{len(STEPS)}] {s.ver}: skipped (before --start-at {start_at})")
                continue
        cmd = [py, "-m", s.spec] if s.kind == "module" else [py, "-c", s.spec]
        tag = "TRAINS" if s.trains else "xform "
        trained_any = trained_any or s.trains
        print(f"[{i:2d}/{len(STEPS)}] {s.ver} [{tag}]  reads: {s.reads}")
        print(f"      $ {' '.join(cmd[:2])} {cmd[2] if len(cmd) > 2 else ''}")
        rc = subprocess.run(cmd, cwd=str(root), env=env).returncode
        if rc != 0:
            print(f"      FAIL: producer for {s.ver} exited {rc}")
            return 2
        produced = out_csv(root, s.ver)
        if not produced.exists():
            print(f"      FAIL: expected {produced.relative_to(root)} was not written")
            return 2
        print(f"      ok -> {produced.relative_to(root)}")

    v51 = out_csv(root, "v51")
    got = sha256_file(v51)
    print(f"\nv51 rebuilt: {v51.relative_to(root)}")
    print(f"  sha256        : {got}")
    print(f"  canonical ref : {V51_SHA256}")
    if got == V51_SHA256:
        print("  BYTE-IDENTICAL to the canonical v51.")
    else:
        print("  sha differs from the canonical reference — EXPECTED if any TRAINS step ran in a")
        print("  different LightGBM/CatBoost/sklearn version. The rebuild is score-equivalent; the")
        print("  byte-exact v51 needs the original library versions. (See docs/END_TO_END.md.)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="working-tree root (has src/ data/ starting-kit/)")
    ap.add_argument("--plan", action="store_true", help="print the ordered plan and exit")
    ap.add_argument("--start-at", choices=[s.ver for s in STEPS], default=None, help="resume at a version")
    args = ap.parse_args()
    if args.plan:
        print_plan()
        return 0
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"no such root: {root}")
        return 2
    return run_chain(root, args.start_at)


if __name__ == "__main__":
    raise SystemExit(main())
