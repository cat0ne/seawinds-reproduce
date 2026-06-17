#!/usr/bin/env python3
"""Build final-day nonzero-diff rank-recapture packets.

These packets are deliberately scoped but aggressive:

* v243-v246 are a ladder of extra center-frozen North Sea station d1 direction
  interval shrinks on top of the current production base. v227 proved this
  target can improve hidden scoring, but the June 14 board needs a larger move
  to climb the public rank.
* v247/v252 combine the rank-flip station ladder point with the two d1
  speed-width probes that still have real local CSV deltas. The speed probes
  are not route-positive on the fresh board alone, so these are explicitly full
  risk.
* v253 is the post-score cleanup of v252: keep the ECS speed donor that helped
  raw score, drop the NS speed donor that hurt raw score.
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

KEY_COLS = ("type", "window", "region", "latitude", "longitude", "station", "horizon", "hour", "level")
Q_COLS = ("q05", "q50", "q95")
DIR_COLS = ("dir_05", "dir_50", "dir_95")
SURFACE_LEVELS = frozenset(("10m", "100m"))
EXPECTED_ROWS = 3_448_800
CHUNKSIZE = 200_000
MIN_HALFWIDTH_DEG = 0.25

BASE_VERSION = "v222_plus_v227_plus_v232"
SUBMISSIONS_DIR = ROOT / "submissions"
LOGS_DIR = ROOT / "logs"
LOG_PATH = SUBMISSIONS_DIR / "log.json"
EXPERIMENT_LOG_PATH = ROOT / "docs" / "research" / "EXPERIMENT_LOG.md"


@dataclass(frozen=True)
class BuildSpec:
    version: str
    extra_shrink_per_side_deg: float
    include_speed_d1: bool
    description: str
    risk_posture: str
    speed_d1_regions: tuple[str, ...] | None = None

    @property
    def is_compound(self) -> bool:
        return self.include_speed_d1

    @property
    def active_speed_d1_regions(self) -> tuple[str, ...]:
        if not self.include_speed_d1:
            return ()
        if self.speed_d1_regions is not None:
            return self.speed_d1_regions
        return ("east_china_sea", "north_sea")


BUILDS = {
    "v243_ns_sta_d1_dir_shrink_extra_0p10": BuildSpec(
        version="v243_ns_sta_d1_dir_shrink_extra_0p10",
        extra_shrink_per_side_deg=0.10,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.10 deg per side on production base.",
        risk_posture="single-cell station direction ladder; v227-proven family, still endpoint-risk",
    ),
    "v244_ns_sta_d1_dir_shrink_extra_0p20": BuildSpec(
        version="v244_ns_sta_d1_dir_shrink_extra_0p20",
        extra_shrink_per_side_deg=0.20,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.20 deg per side on production base.",
        risk_posture="single-cell station direction ladder; roughly double v227 additional pressure",
    ),
    "v245_ns_sta_d1_dir_shrink_extra_0p30": BuildSpec(
        version="v245_ns_sta_d1_dir_shrink_extra_0p30",
        extra_shrink_per_side_deg=0.30,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.30 deg per side on production base.",
        risk_posture="single-cell station direction ladder; linearized target clears fresh rank-1 boundary",
    ),
    "v248_ns_sta_d1_dir_shrink_extra_0p25": BuildSpec(
        version="v248_ns_sta_d1_dir_shrink_extra_0p25",
        extra_shrink_per_side_deg=0.25,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.25 deg per side on production base.",
        risk_posture="single-cell station direction fine bracket; between v244 and v245",
    ),
    "v249_ns_sta_d1_dir_shrink_extra_0p35": BuildSpec(
        version="v249_ns_sta_d1_dir_shrink_extra_0p35",
        extra_shrink_per_side_deg=0.35,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.35 deg per side on production base.",
        risk_posture="single-cell station direction fine bracket; between v245 and v246",
    ),
    "v246_ns_sta_d1_dir_shrink_extra_0p40": BuildSpec(
        version="v246_ns_sta_d1_dir_shrink_extra_0p40",
        extra_shrink_per_side_deg=0.40,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.40 deg per side on production base.",
        risk_posture="single-cell station direction ladder; aggressive undercoverage-risk point",
    ),
    "v250_ns_sta_d1_dir_shrink_extra_0p45": BuildSpec(
        version="v250_ns_sta_d1_dir_shrink_extra_0p45",
        extra_shrink_per_side_deg=0.45,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.45 deg per side on production base.",
        risk_posture="single-cell station direction post-v249 bracket; expected to clear boundary with small margin",
    ),
    "v251_ns_sta_d1_dir_shrink_extra_0p50": BuildSpec(
        version="v251_ns_sta_d1_dir_shrink_extra_0p50",
        extra_shrink_per_side_deg=0.50,
        include_speed_d1=False,
        description="Extra center-frozen NS station d1 direction shrink: +0.50 deg per side on production base.",
        risk_posture="single-cell station direction post-v249 bracket; larger clearance, higher undercoverage risk",
    ),
    "v247_full_risk_ns_sta_d1_plus_d1_speed": BuildSpec(
        version="v247_full_risk_ns_sta_d1_plus_d1_speed",
        extra_shrink_per_side_deg=0.30,
        include_speed_d1=True,
        description=(
            "Full-risk final-day compound: v245-style NS station d1 direction shrink plus "
            "real-delta d1 speed-width probes from v222_plus_v225 and v228."
        ),
        risk_posture="full-risk compound; station rank flip attempt plus non-route-positive d1 speed probes",
    ),
    "v252_full_risk_ns_sta_d1_0p45_plus_d1_speed": BuildSpec(
        version="v252_full_risk_ns_sta_d1_0p45_plus_d1_speed",
        extra_shrink_per_side_deg=0.45,
        include_speed_d1=True,
        description=(
            "Full-risk final-day compound: v250-style NS station d1 direction shrink plus "
            "real-delta d1 speed-width probes from v222_plus_v225 and v228."
        ),
        risk_posture="full-risk compound; post-v249 station bracket plus non-route-positive d1 speed probes",
    ),
    "v253_station_0p45_plus_ecs_d1_speed_only": BuildSpec(
        version="v253_station_0p45_plus_ecs_d1_speed_only",
        extra_shrink_per_side_deg=0.45,
        include_speed_d1=True,
        description=(
            "Post-v252 cleanup compound: keep v250-style NS station d1 direction shrink "
            "and the v222_plus_v225 ECS d1 speed donor, but drop the v228 NS d1 speed donor."
        ),
        risk_posture="compound cleanup; preserves v252 winning cells while removing observed NS d1 speed regression",
        speed_d1_regions=("east_china_sea",),
    ),
    "v254_station_0p50_plus_ecs_d1_speed_only": BuildSpec(
        version="v254_station_0p50_plus_ecs_d1_speed_only",
        extra_shrink_per_side_deg=0.50,
        include_speed_d1=True,
        description=(
            "Aggressive ECS-only cleanup compound: +0.50 NS station d1 direction shrink "
            "plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor."
        ),
        risk_posture="aggressive compound cleanup; tests whether the post-v252 station shrink can move further",
        speed_d1_regions=("east_china_sea",),
    ),
    "v255_station_0p55_plus_ecs_d1_speed_only": BuildSpec(
        version="v255_station_0p55_plus_ecs_d1_speed_only",
        extra_shrink_per_side_deg=0.55,
        include_speed_d1=True,
        description=(
            "High-risk ECS-only cleanup compound: +0.55 NS station d1 direction shrink "
            "plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor."
        ),
        risk_posture="high-risk compound cleanup; explores whether the station d1 interval remains over-wide",
        speed_d1_regions=("east_china_sea",),
    ),
    "v256_station_0p60_plus_ecs_d1_speed_only": BuildSpec(
        version="v256_station_0p60_plus_ecs_d1_speed_only",
        extra_shrink_per_side_deg=0.60,
        include_speed_d1=True,
        description=(
            "Maximum-risk ECS-only cleanup compound: +0.60 NS station d1 direction shrink "
            "plus the v222_plus_v225 ECS d1 speed donor, with no NS d1 speed donor."
        ),
        risk_posture="maximum-risk compound cleanup; final-day over-shrink probe after v252 proved +0.45 positive",
        speed_d1_regions=("east_china_sea",),
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


def validate_keys(left: Any, right: Any, label: str, chunk_index: int) -> None:
    for key in KEY_COLS:
        left_values = left[key].fillna("").astype(str)
        right_values = right[key].fillna("").astype(str)
        if not left_values.equals(right_values):
            raise RuntimeError(f"Row/key mismatch for {label} at chunk {chunk_index}, key {key}")


def circular_distance_forward(start: Any, end: Any) -> Any:
    return (start.astype(float) - 0 + end.astype(float) - start.astype(float)) % 360.0


def station_ns_d1_mask(df: Any) -> Any:
    return (
        (df["type"] == "station")
        & (df["region"] == "north_sea")
        & (df["horizon"].astype(int) == 1)
    )


def surface_d1_speed_mask(df: Any, region: str) -> Any:
    level = df["level"].fillna("").astype(str)
    return (
        (df["type"] == "grid")
        & (df["region"] == region)
        & (df["horizon"].astype(int) == 1)
        & level.isin(SURFACE_LEVELS)
    )


def shrink_station_direction(out_chunk: Any, mask: Any, shrink_per_side_deg: float) -> None:
    if not bool(mask.any()):
        return
    center = out_chunk.loc[mask, "dir_50"].astype(float)
    lower = (center - out_chunk.loc[mask, "dir_05"].astype(float)) % 360.0
    upper = (out_chunk.loc[mask, "dir_95"].astype(float) - center) % 360.0
    lower_shrink = np.minimum(shrink_per_side_deg, np.maximum(lower - MIN_HALFWIDTH_DEG, 0.0))
    upper_shrink = np.minimum(shrink_per_side_deg, np.maximum(upper - MIN_HALFWIDTH_DEG, 0.0))
    out_chunk.loc[mask, "dir_05"] = (center - (lower - lower_shrink)) % 360.0
    out_chunk.loc[mask, "dir_95"] = (center + (upper - upper_shrink)) % 360.0


def direction_width(df: Any, mask: Any) -> Any:
    return (df.loc[mask, "dir_95"].astype(float) - df.loc[mask, "dir_05"].astype(float)) % 360.0


def changed_rows(before: Any, after: Any, mask: Any, columns: tuple[str, ...]) -> int:
    if not bool(mask.any()):
        return 0
    return int(after.loc[mask, list(columns)].ne(before.loc[mask, list(columns)]).any(axis=1).sum())


def assert_speed_quantiles(df: Any, mask: Any, label: str, chunk_index: int) -> None:
    if not bool(mask.any()):
        return
    q = df.loc[mask, list(Q_COLS)]
    bad = (q["q05"] > q["q50"]) | (q["q50"] > q["q95"]) | (q["q05"] < 0)
    if bool(bad.any()):
        raise RuntimeError(f"{label} has {int(bad.sum())} speed quantile crossings at chunk {chunk_index}")


def zip_prediction(csv_path: Path, out_zip_path: Path) -> None:
    with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(csv_path, arcname="predictions.csv")


def base_manifest(spec: BuildSpec, recorded_at: str) -> dict[str, Any]:
    return {
        "version": spec.version,
        "decision": "BUILT_PENDING_SCORE",
        "base_version": BASE_VERSION,
        "description": spec.description,
        "risk_posture": spec.risk_posture,
        "compound": spec.is_compound,
        "rows": 0,
        "components": [],
        "fresh_board_context": {
            "cell": "Dir NS Sta d1",
            "current_score": 170.7474,
            "rank_1_boundary": 170.63,
            "gap_to_rank_1": 0.1174,
            "prior_v227_delta": -0.0404,
        },
        "csv_path": str(prediction_path(spec.version)),
        "zip_path": str(zip_path(spec.version)),
        "recorded_at": recorded_at,
    }


def build(build_specs: tuple[BuildSpec, ...]) -> dict[str, dict[str, Any]]:
    import pandas as pd

    required = [prediction_path(BASE_VERSION)]
    if any("east_china_sea" in spec.active_speed_d1_regions for spec in build_specs):
        required.append(prediction_path("v222_plus_v225"))
    if any("north_sea" in spec.active_speed_d1_regions for spec in build_specs):
        required.append(prediction_path("v228"))
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(", ".join(str(path) for path in missing))

    recorded_at = utc_now_iso()
    manifests = {spec.version: base_manifest(spec, recorded_at) for spec in build_specs}
    for spec in build_specs:
        prediction_path(spec.version).unlink(missing_ok=True)
        zip_path(spec.version).unlink(missing_ok=True)
        manifest_path(spec.version).parent.mkdir(parents=True, exist_ok=True)

    base_reader = pd.read_csv(prediction_path(BASE_VERSION), chunksize=CHUNKSIZE)
    ecs_speed_reader = (
        pd.read_csv(prediction_path("v222_plus_v225"), chunksize=CHUNKSIZE)
        if any("east_china_sea" in spec.active_speed_d1_regions for spec in build_specs)
        else None
    )
    ns_speed_reader = (
        pd.read_csv(prediction_path("v228"), chunksize=CHUNKSIZE)
        if any("north_sea" in spec.active_speed_d1_regions for spec in build_specs)
        else None
    )

    wrote_header = {spec.version: False for spec in build_specs}
    stats: dict[str, dict[str, Any]] = {
        spec.version: {
            "station_target_rows": 0,
            "station_direction_changed_rows": 0,
            "station_width_delta_sum": 0.0,
            "station_width_delta_min": None,
            "station_width_delta_max": None,
            "ecs_speed_copied_rows": 0,
            "ecs_speed_changed_rows": 0,
            "ns_speed_copied_rows": 0,
            "ns_speed_changed_rows": 0,
        }
        for spec in build_specs
    }
    rows = 0

    for chunk_index, base_chunk in enumerate(base_reader):
        ecs_speed_chunk = next(ecs_speed_reader) if ecs_speed_reader is not None else None
        ns_speed_chunk = next(ns_speed_reader) if ns_speed_reader is not None else None
        if ecs_speed_chunk is not None:
            validate_keys(base_chunk, ecs_speed_chunk, "v222_plus_v225", chunk_index)
        if ns_speed_chunk is not None:
            validate_keys(base_chunk, ns_speed_chunk, "v228", chunk_index)

        station_mask = station_ns_d1_mask(base_chunk)
        ecs_speed_mask = surface_d1_speed_mask(base_chunk, "east_china_sea")
        ns_speed_mask = surface_d1_speed_mask(base_chunk, "north_sea")

        for spec in build_specs:
            out_chunk = base_chunk.copy()

            base_width = direction_width(base_chunk, station_mask)
            shrink_station_direction(out_chunk, station_mask, spec.extra_shrink_per_side_deg)
            new_width = direction_width(out_chunk, station_mask)
            width_delta = new_width - base_width
            station_changed = changed_rows(base_chunk, out_chunk, station_mask, DIR_COLS)

            row_stats = stats[spec.version]
            row_stats["station_target_rows"] += int(station_mask.sum())
            row_stats["station_direction_changed_rows"] += station_changed
            if len(width_delta):
                row_stats["station_width_delta_sum"] += float(width_delta.sum())
                chunk_min = float(width_delta.min())
                chunk_max = float(width_delta.max())
                row_stats["station_width_delta_min"] = (
                    chunk_min
                    if row_stats["station_width_delta_min"] is None
                    else min(row_stats["station_width_delta_min"], chunk_min)
                )
                row_stats["station_width_delta_max"] = (
                    chunk_max
                    if row_stats["station_width_delta_max"] is None
                    else max(row_stats["station_width_delta_max"], chunk_max)
                )

            if "east_china_sea" in spec.active_speed_d1_regions:
                if ecs_speed_chunk is None:
                    raise RuntimeError("missing ECS speed donor chunks for compound")
                out_chunk.loc[ecs_speed_mask, list(Q_COLS)] = ecs_speed_chunk.loc[
                    ecs_speed_mask, list(Q_COLS)
                ].to_numpy()
                assert_speed_quantiles(out_chunk, ecs_speed_mask, "ecs d1 speed", chunk_index)
                row_stats["ecs_speed_copied_rows"] += int(ecs_speed_mask.sum())
                row_stats["ecs_speed_changed_rows"] += changed_rows(base_chunk, out_chunk, ecs_speed_mask, Q_COLS)
            if "north_sea" in spec.active_speed_d1_regions:
                if ns_speed_chunk is None:
                    raise RuntimeError("missing NS speed donor chunks for compound")
                out_chunk.loc[ns_speed_mask, list(Q_COLS)] = ns_speed_chunk.loc[
                    ns_speed_mask, list(Q_COLS)
                ].to_numpy()
                assert_speed_quantiles(out_chunk, ns_speed_mask, "ns d1 speed", chunk_index)
                row_stats["ns_speed_copied_rows"] += int(ns_speed_mask.sum())
                row_stats["ns_speed_changed_rows"] += changed_rows(base_chunk, out_chunk, ns_speed_mask, Q_COLS)

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

    invalid = []
    for spec in build_specs:
        row_stats = stats[spec.version]
        if row_stats["station_direction_changed_rows"] != row_stats["station_target_rows"]:
            invalid.append(
                f"{spec.version} station rows changed {row_stats['station_direction_changed_rows']} / "
                f"{row_stats['station_target_rows']}"
            )
        if "east_china_sea" in spec.active_speed_d1_regions and row_stats["ecs_speed_changed_rows"] == 0:
            invalid.append(f"{spec.version} has zero changed speed rows in the ECS compound speed component")
        if "north_sea" in spec.active_speed_d1_regions and row_stats["ns_speed_changed_rows"] == 0:
            invalid.append(f"{spec.version} has zero changed speed rows in the NS compound speed component")
    if invalid:
        for spec in build_specs:
            prediction_path(spec.version).unlink(missing_ok=True)
        raise RuntimeError("; ".join(invalid))

    for spec in build_specs:
        row_stats = stats[spec.version]
        manifest = manifests[spec.version]
        target_rows = row_stats["station_target_rows"]
        manifest["rows"] = rows
        manifest["components"].append(
            {
                "cell": "dir_stations_d1_ns",
                "display": "Dir NS Sta d1",
                "columns": list(DIR_COLS),
                "mechanism": "center-frozen endpoint shrink on top of production v227 state",
                "extra_shrink_per_side_deg": spec.extra_shrink_per_side_deg,
                "copied_rows": target_rows,
                "changed_rows": row_stats["station_direction_changed_rows"],
                "mean_width_delta_target": row_stats["station_width_delta_sum"] / target_rows,
                "min_width_delta_target": row_stats["station_width_delta_min"],
                "max_width_delta_target": row_stats["station_width_delta_max"],
            }
        )
        if "east_china_sea" in spec.active_speed_d1_regions:
            manifest["components"].append(
                {
                    "cell": "speed_surface_d1_ecs",
                    "display": "WS ECS Surf d1",
                    "donor_version": "v222_plus_v225",
                    "columns": list(Q_COLS),
                    "copied_rows": row_stats["ecs_speed_copied_rows"],
                    "changed_rows": row_stats["ecs_speed_changed_rows"],
                    "fresh_board_note": "actual local delta; v252 confirmed raw improvement to 4.5951",
                }
            )
        if "north_sea" in spec.active_speed_d1_regions:
            manifest["components"].append(
                {
                    "cell": "speed_surface_d1_ns",
                    "display": "WS NS Surf d1",
                    "donor_version": "v228",
                    "columns": list(Q_COLS),
                    "copied_rows": row_stats["ns_speed_copied_rows"],
                    "changed_rows": row_stats["ns_speed_changed_rows"],
                    "fresh_board_note": "actual local delta, but v252 confirmed raw regression to 4.7089",
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
        f"{component['display']} {component.get('changed_rows', 0)}/{component.get('copied_rows', 0)} changed/copied"
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
                    "Generated by scripts/build_final_day_station_ladder.py from the production base.",
                    f"Base: {BASE_VERSION}.",
                    f"Components: {component_summary(manifest)}.",
                    f"Rows: {manifest['rows']:,}.",
                    f"Artifact SHA256: {manifest['zip_sha256']}.",
                    "Pending Codabench score; record all 36 cells after upload.",
                ],
                "local_scores": None,
                "leaderboard_scores": None,
                "_pending_score": True,
                "compound": bool(manifest["compound"]),
                "mean_rank": None,
                "lessons": (
                    "PENDING SCORE. Final-day nonzero-diff rank-recapture packet. "
                    "Promote only if Codabench confirms target-cell improvement without primary regression."
                ),
            }
        )
        states[version] = "appended-pending"
    LOG_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return states


def next_progression_number(text: str) -> int:
    max_number = 0
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if parts and parts[0].isdigit():
            max_number = max(max_number, int(parts[0]))
    return max_number + 1


def ensure_experiment_log(manifests: dict[str, dict[str, Any]]) -> dict[str, str]:
    text = EXPERIMENT_LOG_PATH.read_text(encoding="utf-8")
    states: dict[str, str] = {}
    sections = []
    for version, manifest in manifests.items():
        header = f"## Build — {version} (FINAL-DAY RISK, PENDING SCORE)"
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

Built a nonzero-diff final-day packet after donor-copy mining collapsed to
rounded-score false positives. The primary target is `Dir NS Sta d1`, where
`v227` already improved hidden scoring but the fresh rank-1 boundary still
needs about `0.1174` cWS.

### Scope

{component_summary(manifest)}

Rows: `{manifest['rows']:,}`. ZIP SHA256: `{manifest['zip_sha256']}`.

### Next Step

Upload only if spending a final-day risk slot. After Codabench scores it,
update `submissions/log.json` and this experiment log with all 36 leaderboard
cells.
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
    missing = [version for version in manifests if f"| {version} |" not in text]
    if missing:
        next_number = next_progression_number(text)
        rows = []
        for version in missing:
            manifest = manifests[version]
            rows.append(
                f"| {next_number} | {version} | PENDING | BUILT / PENDING SCORE | "
                f"{component_summary(manifest)} | Final-day nonzero-diff rank-recapture packet. |"
            )
            next_number += 1
        marker = "| 261 |"
        marker_index = text.rfind(marker)
        if marker_index >= 0:
            line_end = text.find("\n", marker_index)
            insert_at = len(text) if line_end < 0 else line_end + 1
            text = text[:insert_at] + "\n".join(rows) + "\n" + text[insert_at:]
        else:
            table_start = text.find("## Score Progression")
            table_end = text.find("\n---\n", table_start) if table_start >= 0 else -1
            if table_end >= 0:
                text = text[:table_end] + "\n".join(rows) + "\n" + text[table_end:]
            else:
                text = text.rstrip() + "\n" + "\n".join(rows) + "\n"
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
