#!/usr/bin/env python3
"""Build pushed direction-shrink packets on top of dirshrink_combined.

``dirshrink_combined`` proved four selective direction shrinks were raw-positive
and public-rank-positive/non-worse. The public board after that upload still
needs roughly five rank positions to climb. This builder keeps the
scored combined base intact and only increases shrink fractions on the same
winner cells that remain close to public rank boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUBMISSIONS_DIR = ROOT / "submissions"
LOGS_DIR = ROOT / "logs"
LOG_PATH = SUBMISSIONS_DIR / "log.json"
EXPERIMENT_LOG_PATH = ROOT / "docs" / "research" / "EXPERIMENT_LOG.md"
BASE_VERSION = "dirshrink_combined"
BASE_CSV = SUBMISSIONS_DIR / "predictions_dirshrink_combined.csv"
EXPECTED_ROWS = 3_448_800
CHUNKSIZE = 200_000
SURFACE_LEVELS = frozenset(("10m", "100m"))
Q_COLS = ("q05", "q50", "q95")
DIR_COLS = ("dir_05", "dir_50", "dir_95")


@dataclass(frozen=True)
class Target:
    region: str
    source: str
    horizon: int
    current_fraction: float
    target_fraction: float
    display: str
    cell: str

    @property
    def additional_fraction_of_current_width(self) -> float:
        if self.target_fraction < self.current_fraction:
            raise ValueError(f"{self.display} target fraction is below current fraction")
        return (self.target_fraction - self.current_fraction) / (1.0 - self.current_fraction)


@dataclass(frozen=True)
class BuildSpec:
    version: str
    targets: tuple[Target, ...]
    description: str
    risk_posture: str


BASE_WINNERS = {
    "ns_pres_d7": Target(
        region="north_sea",
        source="Pres",
        horizon=7,
        current_fraction=0.12,
        target_fraction=0.12,
        display="Dir NS Pres d7",
        cell="dir_pressure_d7_ns",
    ),
    "ns_surf_d7": Target(
        region="north_sea",
        source="Surf",
        horizon=7,
        current_fraction=0.12,
        target_fraction=0.12,
        display="Dir NS Surf d7",
        cell="dir_surface_d7_ns",
    ),
    "ecs_surf_d7": Target(
        region="east_china_sea",
        source="Surf",
        horizon=7,
        current_fraction=0.12,
        target_fraction=0.12,
        display="Dir ECS Surf d7",
        cell="dir_surface_d7_ecs",
    ),
    "ns_sta_d14": Target(
        region="north_sea",
        source="Sta",
        horizon=14,
        current_fraction=0.12,
        target_fraction=0.12,
        display="Dir NS Sta d14",
        cell="dir_stations_d14_ns",
    ),
}


def target_with_fraction(key: str, fraction: float) -> Target:
    base = BASE_WINNERS[key]
    return Target(
        region=base.region,
        source=base.source,
        horizon=base.horizon,
        current_fraction=base.current_fraction,
        target_fraction=fraction,
        display=base.display,
        cell=base.cell,
    )


BUILDS = {
    "v260_combined_dirpush_hint": BuildSpec(
        version="v260_combined_dirpush_hint",
        targets=(
            target_with_fraction("ns_pres_d7", 0.28),
            target_with_fraction("ns_surf_d7", 0.20),
            target_with_fraction("ecs_surf_d7", 0.25),
            target_with_fraction("ns_sta_d14", 0.12),
        ),
        description=(
            "dirshrink_combined + hinted pushed shrink totals: NS Pres d7 28%, "
            "NS Surf d7 20%, ECS Surf d7 25%, NS Sta d14 unchanged at 12%."
        ),
        risk_posture="high-risk public-rank push on already raw-positive direction cells",
    ),
    "v261_combined_dirpush_mid": BuildSpec(
        version="v261_combined_dirpush_mid",
        targets=(
            target_with_fraction("ns_pres_d7", 0.20),
            target_with_fraction("ns_surf_d7", 0.16),
            target_with_fraction("ecs_surf_d7", 0.18),
            target_with_fraction("ns_sta_d14", 0.12),
        ),
        description=(
            "dirshrink_combined + medium pushed shrink totals: NS Pres d7 20%, "
            "NS Surf d7 16%, ECS Surf d7 18%, NS Sta d14 unchanged at 12%."
        ),
        risk_posture="medium-risk bracket between proven 12% and hinted push",
    ),
}

DEFAULT_BUILD_ORDER = tuple(BUILDS)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def prediction_path(version: str) -> Path:
    return SUBMISSIONS_DIR / f"predictions_{version}.csv"


def zip_path(version: str) -> Path:
    return SUBMISSIONS_DIR / f"submission_{version}.zip"


def manifest_path(version: str) -> Path:
    return LOGS_DIR / version / "manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_array(df: Any) -> Any:
    level = df["level"].fillna("").astype(str)
    return np.where(df["type"] == "station", "Sta", np.where(level.isin(SURFACE_LEVELS), "Surf", "Pres"))


def target_mask(df: Any, src: Any, target: Target) -> Any:
    return (
        (df["region"] == target.region)
        & (df["horizon"].astype(int) == target.horizon)
        & (src == target.source)
    )


def circular_width(df: Any, mask: Any) -> Any:
    return (df.loc[mask, "dir_95"].astype(float) - df.loc[mask, "dir_05"].astype(float)) % 360.0


def apply_width_fraction_push(chunk: Any, mask: Any, additional_fraction: float) -> None:
    if additional_fraction <= 0.0 or not bool(mask.any()):
        return
    idx = chunk.index[mask]
    lower = chunk.loc[idx, "dir_05"].astype(float).to_numpy()
    upper = chunk.loc[idx, "dir_95"].astype(float).to_numpy()
    width = (upper - lower) % 360.0
    mid = (lower + width / 2.0) % 360.0
    new_half_width = (width / 2.0) * (1.0 - additional_fraction)
    chunk.loc[idx, "dir_05"] = (mid - new_half_width) % 360.0
    chunk.loc[idx, "dir_95"] = (mid + new_half_width) % 360.0


def changed_rows(before: Any, after: Any, mask: Any, columns: tuple[str, ...]) -> int:
    if not bool(mask.any()):
        return 0
    return int(after.loc[mask, list(columns)].ne(before.loc[mask, list(columns)]).any(axis=1).sum())


def zip_prediction(csv_path: Path, out_zip_path: Path) -> None:
    with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(csv_path, arcname="predictions.csv")


def build(specs: tuple[BuildSpec, ...]) -> dict[str, dict[str, Any]]:
    import pandas as pd

    if not BASE_CSV.exists():
        raise FileNotFoundError(BASE_CSV)
    recorded_at = utc_now_iso()
    manifests: dict[str, dict[str, Any]] = {}
    wrote_header = {spec.version: False for spec in specs}
    stats: dict[str, dict[str, dict[str, Any]]] = {}
    for spec in specs:
        prediction_path(spec.version).unlink(missing_ok=True)
        zip_path(spec.version).unlink(missing_ok=True)
        manifest_path(spec.version).parent.mkdir(parents=True, exist_ok=True)
        manifests[spec.version] = {
            "version": spec.version,
            "decision": "BUILT_PENDING_SCORE",
            "base_version": BASE_VERSION,
            "description": spec.description,
            "risk_posture": spec.risk_posture,
            "compound": True,
            "rows": 0,
            "components": [],
            "csv_path": str(prediction_path(spec.version)),
            "zip_path": str(zip_path(spec.version)),
            "recorded_at": recorded_at,
        }
        stats[spec.version] = {
            target.cell: {
                "display": target.display,
                "target_rows": 0,
                "changed_rows": 0,
                "width_delta_sum": 0.0,
                "width_delta_min": None,
                "width_delta_max": None,
                "current_fraction": target.current_fraction,
                "target_fraction": target.target_fraction,
                "additional_fraction": target.additional_fraction_of_current_width,
            }
            for target in spec.targets
        }

    rows = 0
    for base_chunk in pd.read_csv(BASE_CSV, chunksize=CHUNKSIZE, dtype={"level": str}):
        src = source_array(base_chunk)
        for spec in specs:
            out_chunk = base_chunk.copy()
            for target in spec.targets:
                mask = target_mask(base_chunk, src, target)
                before_width = circular_width(base_chunk, mask)
                apply_width_fraction_push(out_chunk, mask, target.additional_fraction_of_current_width)
                after_width = circular_width(out_chunk, mask)
                width_delta = after_width - before_width
                stat = stats[spec.version][target.cell]
                stat["target_rows"] += int(mask.sum())
                stat["changed_rows"] += changed_rows(base_chunk, out_chunk, mask, DIR_COLS)
                if len(width_delta):
                    stat["width_delta_sum"] += float(width_delta.sum())
                    chunk_min = float(width_delta.min())
                    chunk_max = float(width_delta.max())
                    stat["width_delta_min"] = chunk_min if stat["width_delta_min"] is None else min(stat["width_delta_min"], chunk_min)
                    stat["width_delta_max"] = chunk_max if stat["width_delta_max"] is None else max(stat["width_delta_max"], chunk_max)
            out_chunk.to_csv(
                prediction_path(spec.version),
                mode="w" if not wrote_header[spec.version] else "a",
                index=False,
                header=not wrote_header[spec.version],
            )
            wrote_header[spec.version] = True
        rows += len(base_chunk)

    if rows != EXPECTED_ROWS:
        raise RuntimeError(f"Output row count {rows} != {EXPECTED_ROWS}")
    for spec in specs:
        manifest = manifests[spec.version]
        manifest["rows"] = rows
        for target in spec.targets:
            stat = stats[spec.version][target.cell]
            if target.target_fraction > target.current_fraction and stat["changed_rows"] != stat["target_rows"]:
                raise RuntimeError(
                    f"{spec.version} {target.display} changed {stat['changed_rows']} / {stat['target_rows']}"
                )
            manifest["components"].append(
                {
                    "cell": target.cell,
                    "display": target.display,
                    "columns": list(DIR_COLS),
                    "mechanism": "center-frozen circular arc shrink on top of dirshrink_combined",
                    "current_shrink_fraction": stat["current_fraction"],
                    "target_shrink_fraction": stat["target_fraction"],
                    "additional_fraction_of_current_width": stat["additional_fraction"],
                    "copied_rows": stat["target_rows"],
                    "changed_rows": stat["changed_rows"],
                    "mean_width_delta_target": (
                        stat["width_delta_sum"] / stat["target_rows"] if stat["target_rows"] else 0.0
                    ),
                    "min_width_delta_target": stat["width_delta_min"],
                    "max_width_delta_target": stat["width_delta_max"],
                }
            )
        csv_path = prediction_path(spec.version)
        out_zip_path = zip_path(spec.version)
        zip_prediction(csv_path, out_zip_path)
        manifest["csv_sha256"] = sha256_file(csv_path)
        manifest["zip_sha256"] = sha256_file(out_zip_path)
        manifest_path(spec.version).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifests


def component_summary(manifest: dict[str, Any]) -> str:
    return "; ".join(
        (
            f"{component['display']} {component.get('current_shrink_fraction', 0):.2f}->"
            f"{component.get('target_shrink_fraction', 0):.2f}, "
            f"{component.get('changed_rows', 0)}/{component.get('copied_rows', 0)} changed"
        )
        for component in manifest["components"]
    )


def ensure_log_records(manifests: dict[str, dict[str, Any]]) -> dict[str, str]:
    records = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    existing = {record.get("id"): record for record in records}
    states: dict[str, str] = {}
    for version, manifest in manifests.items():
        if version in existing:
            states[version] = "existing"
            continue
        records.append(
            {
                "id": version,
                "submitted_at": manifest["recorded_at"],
                "zip_name": Path(str(manifest["zip_path"])).name,
                "variant": version,
                "description": manifest["description"],
                "changes_from_previous": [
                    "Generated by scripts/build_combined_dir_push.py.",
                    f"Base: {BASE_VERSION}.",
                    f"Components: {component_summary(manifest)}.",
                    f"Rows: {manifest['rows']:,}.",
                    f"Artifact SHA256: {manifest['zip_sha256']}.",
                    "Pending Codabench score; record all 36 cells after upload.",
                ],
                "local_scores": None,
                "leaderboard_scores": None,
                "_pending_score": True,
                "compound": True,
                "mean_rank": None,
                "lessons": (
                    "PENDING SCORE. Final-hour public-rank push on the raw-positive direction shrink cells, "
                    "preserving dirshrink_combined's scored gains."
                ),
            }
        )
        states[version] = "appended-pending"
    LOG_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return states


def ensure_experiment_log(manifests: dict[str, dict[str, Any]]) -> dict[str, str]:
    text = EXPERIMENT_LOG_PATH.read_text(encoding="utf-8")
    states: dict[str, str] = {}
    sections = []
    for version, manifest in manifests.items():
        header = f"## Build — {version} (FINAL-HOUR DIR PUSH, PENDING SCORE)"
        if header in text:
            states[version] = "existing-section"
            continue
        sections.append(
            f"""{header}

**Recorded**: {manifest['recorded_at']}
**Artifact**: `submissions/{Path(str(manifest['zip_path'])).name}`
**Base**: `{BASE_VERSION}`
**Posture**: {manifest['risk_posture']}

### Approach

Built on scored `dirshrink_combined` and increased shrink only on direction
cells that were raw-positive in the combined score. This targets public rank
positions rather than the already-rank-1 `Dir NS Sta d1` margin.

### Scope

{component_summary(manifest)}

Rows: `{manifest['rows']:,}`. ZIP SHA256: `{manifest['zip_sha256']}`.

### Next Step

Upload as a final-hour risk slot. If any pushed cell regresses, back off to the
medium bracket or keep `dirshrink_combined` selected.
"""
        )
        states[version] = "appended"
    if sections:
        marker = "\n---\n\n"
        marker_index = text.find(marker)
        block = "\n".join(sections) + "\n"
        if marker_index >= 0:
            insert_at = marker_index + len(marker)
            text = text[:insert_at] + block + text[insert_at:]
        else:
            text = text.rstrip() + "\n\n" + block
        EXPERIMENT_LOG_PATH.write_text(text, encoding="utf-8")
    return states


def parse_versions(raw_versions: list[str] | None) -> tuple[BuildSpec, ...]:
    if not raw_versions:
        raw_versions = list(DEFAULT_BUILD_ORDER)
    unknown = [version for version in raw_versions if version not in BUILDS]
    if unknown:
        raise SystemExit(f"Unknown build version(s): {', '.join(unknown)}")
    return tuple(BUILDS[version] for version in raw_versions)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="append", help="Build one version; repeat for multiple.")
    parser.add_argument("--list", action="store_true", help="List known build versions and exit.")
    parser.add_argument("--no-ledger", action="store_true", help="Build artifacts only; do not update trackers.")
    args = parser.parse_args()
    if args.list:
        for version, spec in BUILDS.items():
            print(f"{version}\t{spec.description}")
        return 0
    specs = parse_versions(args.version)
    manifests = build(specs)
    if not args.no_ledger:
        log_states = ensure_log_records(manifests)
        exp_states = ensure_experiment_log(manifests)
        for version, manifest in manifests.items():
            manifest["log_state"] = log_states.get(version)
            manifest["experiment_log_state"] = exp_states.get(version)
            manifest_path(version).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifests, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
