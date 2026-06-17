#!/usr/bin/env python3
"""Build guarded compounds only after prerequisite score gates prove safe.

This script is intentionally guarded. It refuses to emit a predictions CSV or
submission ZIP while the required prior ingredients are pending, unscored, or
negative against their intended bases. Later speed-chain compounds may include
one unscored next-probe overlay, but only after the previous scored chain is
clean. The goal is to make compounding fast after Codabench scores arrive
without dropping already-proven gains.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import queued_upload_rank_ev as qev  # noqa: E402

LOG_PATH = ROOT / "submissions" / "log.json"
SUBMISSIONS_DIR = ROOT / "submissions"
LOGS_DIR = ROOT / "logs"
EXPERIMENT_LOG_PATH = ROOT / "docs" / "research" / "EXPERIMENT_LOG.md"

KEY_COLS = ("type", "window", "region", "latitude", "longitude", "station", "horizon", "hour", "level")
Q_COLS = ("q05", "q50", "q95")
DIR_COLS = ("dir_05", "dir_50", "dir_95")
EXPECTED_ROWS = 3_448_800
CHUNKSIZE = 200_000

V196_SCORE = 1.419757
V222_TARGETS = ("dir_pressure_d7_ecs", "dir_pressure_d7_ns", "dir_stations_d14_ns")
V225_TARGET = "speed_surface_d1_ecs"
V226_TARGET = "speed_surface_d7_ecs"
V233_TARGET = "speed_pressure_d7_ecs"
V234_TARGET = "speed_surface_d7_ns"
V228_TARGET = "speed_surface_d1_ns"
V229_TARGET = "speed_pressure_d1_ns"
V230_TARGET = "speed_surface_d14_ecs"
V227_TARGET = "dir_stations_d1_ns"
V232_TARGET = "dir_stations_d7_ns"
V235_TARGET = "dir_stations_d1_ecs"
V223_TARGET = "dir_surface_d7_ns"
SPEED_TARGET_DISPLAY = {
    V225_TARGET: "WS ECS Surf d1",
    V226_TARGET: "WS ECS Surf d7",
    V233_TARGET: "WS ECS Pres d7",
    V234_TARGET: "WS NS Surf d7",
    V228_TARGET: "WS NS Surf d1",
    V229_TARGET: "WS NS Pres d1",
    V230_TARGET: "WS ECS Surf d14",
}


@dataclass(frozen=True)
class Overlay:
    version: str
    columns: tuple[str, ...]
    label: str


@dataclass(frozen=True)
class CompoundSpec:
    name: str
    base_version: str
    overlays: tuple[Overlay, ...]


COMPOUNDS: dict[str, CompoundSpec] = {
    "v222_plus_v225": CompoundSpec(
        name="v222_plus_v225",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
        ),
    ),
    "v223_plus_v225": CompoundSpec(
        name="v223_plus_v225",
        base_version="v196",
        overlays=(
            Overlay("v223", DIR_COLS, "direction_compound_v223"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
        ),
    ),
    "v222_plus_v225_plus_v226": CompoundSpec(
        name="v222_plus_v225_plus_v226",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
        ),
    ),
    "v222_plus_v225_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v227": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v227",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
        ),
    ),
    "v222_plus_v225_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v232": CompoundSpec(
        name="v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
            Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
            Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
            Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
            Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
    "v222_plus_v227_plus_v232": CompoundSpec(
        name="v222_plus_v227_plus_v232",
        base_version="v196",
        overlays=(
            Overlay("v222", DIR_COLS, "direction_compound_v222"),
            Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
            Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
        ),
    ),
}

CHAIN_REQUIREMENTS: dict[str, tuple[str, str, str]] = {
    "v222_plus_v225_plus_v226": ("v222_plus_v225", "v226", V226_TARGET),
    "v222_plus_v225_plus_v226_plus_v228": (
        "v222_plus_v225_plus_v226",
        "v228",
        V228_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233": (
        "v222_plus_v225_plus_v226",
        "v233",
        V233_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234": (
        "v222_plus_v225_plus_v226_plus_v233",
        "v234",
        V234_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234",
        "v228",
        V228_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
        "v230",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228": (
        "v222_plus_v225_plus_v226_plus_v233",
        "v228",
        V228_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
        "v230",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v228",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229",
        "v230",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v227": ("v222_plus_v225", "v227", V227_TARGET),
    "v222_plus_v225_plus_v226_plus_v227": (
        "v222_plus_v225_plus_v226",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v228",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v227": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230",
        "v227",
        V227_TARGET,
    ),
    "v222_plus_v225_plus_v232": ("v222_plus_v225", "v232", V232_TARGET),
    "v222_plus_v225_plus_v226_plus_v232": (
        "v222_plus_v225_plus_v226",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v228",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v232": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230",
        "v232",
        V232_TARGET,
    ),
    "v222_plus_v227_plus_v232": ("v227", "v232", V232_TARGET),
}

PRIOR_CHAIN_GATES: dict[str, tuple[str, str]] = {
    "v222_plus_v225": ("v222", V225_TARGET),
    "v222_plus_v225_plus_v226": ("v222_plus_v225", V226_TARGET),
    "v222_plus_v225_plus_v226_plus_v228": ("v222_plus_v225_plus_v226", V228_TARGET),
    "v222_plus_v225_plus_v226_plus_v233": ("v222_plus_v225_plus_v226", V233_TARGET),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234": (
        "v222_plus_v225_plus_v226_plus_v233",
        V234_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234",
        V228_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228": (
        "v222_plus_v225_plus_v226_plus_v233",
        V228_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229": (
        "v222_plus_v225_plus_v226_plus_v228",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230": (
        "v222_plus_v225_plus_v226_plus_v228_plus_v229",
        V230_TARGET,
    ),
    "v227": ("v222", V227_TARGET),
}
PROBE_GATES: dict[str, tuple[str, str]] = {
    "v226": ("v222", V226_TARGET),
    "v233": ("v222", V233_TARGET),
    "v234": ("v222", V234_TARGET),
    "v227": ("v222", V227_TARGET),
    "v228": ("v222", V228_TARGET),
    "v229": ("v222", V229_TARGET),
    "v230": ("v222", V230_TARGET),
    "v232": ("v222", V232_TARGET),
    "v235": ("v222", V235_TARGET),
}

OVERLAY_LIBRARY: dict[str, Overlay] = {
    "v222": Overlay("v222", DIR_COLS, "direction_compound_v222"),
    "v225": Overlay("v225", Q_COLS, "speed_uncertainty_v225"),
    "v226": Overlay("v226", Q_COLS, "speed_d7_probe_v226"),
    "v233": Overlay("v233", Q_COLS, "speed_pressure_d7_ecs_probe_v233"),
    "v234": Overlay("v234", Q_COLS, "speed_surface_d7_ns_probe_v234"),
    "v228": Overlay("v228", Q_COLS, "speed_d1_ns_probe_v228"),
    "v229": Overlay("v229", Q_COLS, "speed_pressure_d1_ns_probe_v229"),
    "v230": Overlay("v230", Q_COLS, "speed_surface_d14_ecs_probe_v230"),
    "v227": Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
    "v232": Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
}


def register_compound(name: str, versions: tuple[str, ...]) -> None:
    COMPOUNDS.setdefault(
        name,
        CompoundSpec(
            name=name,
            base_version="v196",
            overlays=tuple(OVERLAY_LIBRARY[version] for version in versions),
        ),
    )


SKIP_V228_SPEED_CHAINS: dict[str, tuple[tuple[str, ...], str, str, str]] = {
    "v222_plus_v225_plus_v226_plus_v229": (
        ("v222", "v225", "v226", "v229"),
        "v222_plus_v225_plus_v226",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v229_plus_v230": (
        ("v222", "v225", "v226", "v229", "v230"),
        "v222_plus_v225_plus_v226_plus_v229",
        "v230",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v229": (
        ("v222", "v225", "v226", "v233", "v229"),
        "v222_plus_v225_plus_v226_plus_v233",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v229_plus_v230": (
        ("v222", "v225", "v226", "v233", "v229", "v230"),
        "v222_plus_v225_plus_v226_plus_v233_plus_v229",
        "v230",
        V230_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229": (
        ("v222", "v225", "v226", "v233", "v234", "v229"),
        "v222_plus_v225_plus_v226_plus_v233_plus_v234",
        "v229",
        V229_TARGET,
    ),
    "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229_plus_v230": (
        ("v222", "v225", "v226", "v233", "v234", "v229", "v230"),
        "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v229",
        "v230",
        V230_TARGET,
    ),
}


SKIP_V228_DIRECTION_CHAINS: dict[str, tuple[str, str, str]] = {}
SKIP_V228_STATION_D7_CHAINS: dict[str, tuple[str, str, str]] = {}
for _chain_name, (_versions, _prior_chain, _probe_version, _target_key) in SKIP_V228_SPEED_CHAINS.items():
    register_compound(_chain_name, _versions)
    CHAIN_REQUIREMENTS.setdefault(_chain_name, (_prior_chain, _probe_version, _target_key))
    _direction_name = f"{_chain_name}_plus_v227"
    register_compound(_direction_name, (*_versions, "v227"))
    SKIP_V228_DIRECTION_CHAINS[_direction_name] = (_chain_name, "v227", V227_TARGET)
    CHAIN_REQUIREMENTS.setdefault(_direction_name, SKIP_V228_DIRECTION_CHAINS[_direction_name])
    _station_d7_name = f"{_chain_name}_plus_v232"
    register_compound(_station_d7_name, (*_versions, "v232"))
    SKIP_V228_STATION_D7_CHAINS[_station_d7_name] = (_chain_name, "v232", V232_TARGET)
    CHAIN_REQUIREMENTS.setdefault(_station_d7_name, SKIP_V228_STATION_D7_CHAINS[_station_d7_name])


V235_PRIOR_CHAINS: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            "v222_plus_v225",
            "v222_plus_v225_plus_v226",
            "v222_plus_v225_plus_v226_plus_v233",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234",
            "v222_plus_v225_plus_v226_plus_v228",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230",
            "v222_plus_v225_plus_v227",
            "v222_plus_v225_plus_v226_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v227",
            "v222_plus_v225_plus_v226_plus_v228_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v227",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v227",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v227",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v227",
            "v222_plus_v225_plus_v232",
            "v222_plus_v225_plus_v226_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v232",
            "v222_plus_v225_plus_v226_plus_v228_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v232",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v232",
            "v222_plus_v225_plus_v226_plus_v228_plus_v229_plus_v230_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v228_plus_v229_plus_v230_plus_v232",
            "v222_plus_v225_plus_v226_plus_v233_plus_v234_plus_v228_plus_v229_plus_v230_plus_v232",
            *SKIP_V228_SPEED_CHAINS.keys(),
            *SKIP_V228_DIRECTION_CHAINS.keys(),
            *SKIP_V228_STATION_D7_CHAINS.keys(),
            "v227",
            "v232",
            "v222_plus_v227_plus_v232",
        )
    )
)


def v235_compound_name(prior_chain: str) -> str:
    if prior_chain == "v227":
        return "v222_plus_v227_plus_v235"
    if prior_chain == "v232":
        return "v222_plus_v232_plus_v235"
    return f"{prior_chain}_plus_v235"


def compound_spec_for_prior_chain(prior_chain: str) -> CompoundSpec:
    if prior_chain in COMPOUNDS:
        return COMPOUNDS[prior_chain]
    if prior_chain == "v227":
        return CompoundSpec(
            name="v222_plus_v227",
            base_version="v196",
            overlays=(
                Overlay("v222", DIR_COLS, "direction_compound_v222"),
                Overlay("v227", DIR_COLS, "station_d1_ns_direction_probe_v227"),
            ),
        )
    if prior_chain == "v232":
        return CompoundSpec(
            name="v222_plus_v232",
            base_version="v196",
            overlays=(
                Overlay("v222", DIR_COLS, "direction_compound_v222"),
                Overlay("v232", DIR_COLS, "station_d7_ns_direction_probe_v232"),
            ),
        )
    raise KeyError(prior_chain)


for _chain_name, (_prior_chain, _probe_version, _target_key) in tuple(CHAIN_REQUIREMENTS.items()):
    PRIOR_CHAIN_GATES.setdefault(_chain_name, (_prior_chain, _target_key))
PRIOR_CHAIN_GATES.setdefault("v232", ("v222", V232_TARGET))

for _prior_chain in V235_PRIOR_CHAINS:
    _prior_spec = compound_spec_for_prior_chain(_prior_chain)
    _compound_name = v235_compound_name(_prior_chain)
    COMPOUNDS.setdefault(
        _compound_name,
        CompoundSpec(
            name=_compound_name,
            base_version=_prior_spec.base_version,
            overlays=(
                *_prior_spec.overlays,
                Overlay("v235", DIR_COLS, "station_d1_ecs_direction_probe_v235"),
            ),
        ),
    )
    CHAIN_REQUIREMENTS.setdefault(_compound_name, (_prior_chain, "v235", V235_TARGET))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_records() -> dict[str, dict[str, Any]]:
    records = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return {str(record.get("id")): record for record in records if record.get("id")}


def load_record_list(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_record_list(records: list[dict[str, Any]], path: Path = LOG_PATH) -> None:
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_scored(record: dict[str, Any] | None) -> bool:
    return bool(record and isinstance(record.get("mean_rank"), (int, float)) and isinstance(record.get("leaderboard_scores"), dict))


def mean_rank(record: dict[str, Any]) -> float:
    return float(record["mean_rank"])


def score(record: dict[str, Any], key: str) -> float:
    return float(record["leaderboard_scores"][key])


def delta(candidate: dict[str, Any], base: dict[str, Any], key: str) -> float:
    return score(candidate, key) - score(base, key)


def public_rank(record: dict[str, Any], key: str) -> int | None:
    display = SPEED_TARGET_DISPLAY.get(key)
    if display is None:
        return None
    try:
        snapshot = qev.load_json(qev.DEFAULT_SNAPSHOT)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    competitor_scores = [
        float(values[display])
        for values in snapshot["competitors"].values()
        if isinstance(values, dict) and display in values
    ]
    return qev.rank_for(score(record, key), competitor_scores)


def board_freshness_blocker() -> str | None:
    try:
        snapshot = qev.load_json(qev.DEFAULT_SNAPSHOT)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return f"board snapshot could not be loaded: {exc}"
    if not isinstance(snapshot, dict):
        return "board snapshot payload is not a JSON object"
    return qev.snapshot_freshness_blocker(snapshot)


def add_board_freshness_error(errors: list[str]) -> None:
    blocker = board_freshness_blocker()
    if blocker is not None:
        errors.append(f"public-board snapshot blocked: {blocker}")


def add_target_gate_errors(
    candidate: dict[str, Any],
    base: dict[str, Any],
    *,
    candidate_version: str,
    base_version: str,
    key: str,
    errors: list[str],
) -> None:
    value = delta(candidate, base, key)
    if value >= -1e-9:
        errors.append(f"{candidate_version} target {key} did not improve versus {base_version} ({value:+.4f})")
        return
    if key not in SPEED_TARGET_DISPLAY:
        return
    base_rank = public_rank(base, key)
    candidate_rank = public_rank(candidate, key)
    if base_rank is None or candidate_rank is None or candidate_rank >= base_rank:
        errors.append(
            f"{candidate_version} target {key} did not improve visible rank versus "
            f"{base_version} (rank {base_rank}->{candidate_rank})"
        )


def nonworse(candidate: dict[str, Any], base_score: float = V196_SCORE) -> bool:
    return mean_rank(candidate) <= base_score + 1e-12


def check_scored(records: dict[str, dict[str, Any]], version: str, errors: list[str]) -> dict[str, Any] | None:
    record = records.get(version)
    if not is_scored(record):
        state = "missing"
        if record and record.get("_pending_score"):
            state = "pending"
        elif record:
            state = "unscored"
        errors.append(f"{version} is {state}; compound requires a scored positive ingredient")
        return None
    return record


def guard_v222(records: dict[str, dict[str, Any]], errors: list[str]) -> None:
    base = records.get("v196")
    record = check_scored(records, "v222", errors)
    if not base or not is_scored(base) or record is None:
        return
    if not nonworse(record):
        errors.append(f"v222 primary {mean_rank(record):.6f} is worse than v196 {V196_SCORE:.6f}")
    for key in V222_TARGETS:
        value = delta(record, base, key)
        if value > 1e-9:
            errors.append(f"v222 target {key} worsened by {value:+.4f}")


def guard_v225(records: dict[str, dict[str, Any]], errors: list[str]) -> None:
    base = records.get("v196")
    record = check_scored(records, "v225", errors)
    if not base or not is_scored(base) or record is None:
        return
    if not nonworse(record):
        errors.append(f"v225 primary {mean_rank(record):.6f} is worse than v196 {V196_SCORE:.6f}")
    add_target_gate_errors(
        record,
        base,
        candidate_version="v225",
        base_version="v196",
        key=V225_TARGET,
        errors=errors,
    )


def guard_v225_direct_probe(records: dict[str, dict[str, Any]], errors: list[str]) -> None:
    record = records.get("v225")
    if record is None:
        errors.append("v225 is missing; direct compound requires the pending probe artifact ledger record")
    elif is_scored(record):
        guard_v225(records, errors)
    elif not record.get("_pending_score"):
        errors.append("v225 is unscored but not pending; reconcile the ledger before compounding")


def guard_v223(records: dict[str, dict[str, Any]], errors: list[str]) -> None:
    v222 = records.get("v222")
    record = check_scored(records, "v223", errors)
    if not v222 or not is_scored(v222) or record is None:
        return
    if mean_rank(record) > mean_rank(v222) + 1e-12:
        errors.append(f"v223 primary {mean_rank(record):.6f} is worse than v222 {mean_rank(v222):.6f}")
    add_target_gate_errors(
        record,
        v222,
        candidate_version="v223",
        base_version="v222",
        key=V223_TARGET,
        errors=errors,
    )


def guard_scored_chain(records: dict[str, dict[str, Any]], prior_version: str, errors: list[str]) -> dict[str, Any] | None:
    prior = check_scored(records, prior_version, errors)
    if prior is None:
        return None
    base_version, target = PRIOR_CHAIN_GATES.get(prior_version, ("v222", ""))
    base = records.get(base_version)
    if not base or not is_scored(base):
        errors.append(f"{base_version} scored base is missing for {prior_version}")
        return prior
    if mean_rank(prior) > mean_rank(base) + 1e-12:
        errors.append(
            f"{prior_version} primary {mean_rank(prior):.6f} is worse than "
            f"{base_version} {mean_rank(base):.6f}"
        )
    if target:
        add_target_gate_errors(
            prior,
            base,
            candidate_version=prior_version,
            base_version=base_version,
            key=target,
            errors=errors,
        )
    return prior


def guard_pending_probe(records: dict[str, dict[str, Any]], probe_version: str, errors: list[str]) -> None:
    record = records.get(probe_version)
    if record is None:
        errors.append(f"{probe_version} is missing; compound requires the probe artifact ledger record")
    elif is_scored(record):
        base_version, target = PROBE_GATES.get(probe_version, ("", ""))
        base = records.get(base_version)
        if not base or not is_scored(base):
            errors.append(f"{base_version} scored base is missing for {probe_version}")
            return
        if mean_rank(record) > mean_rank(base) + 1e-12:
            errors.append(
                f"{probe_version} primary {mean_rank(record):.6f} is worse than "
                f"{base_version} {mean_rank(base):.6f}"
            )
        add_target_gate_errors(
            record,
            base,
            candidate_version=probe_version,
            base_version=base_version,
            key=target,
            errors=errors,
        )
        return
    elif not record.get("_pending_score"):
        errors.append(f"{probe_version} is unscored but not pending; reconcile the ledger before compounding")


def guard_chain_probe(records: dict[str, dict[str, Any]], spec: CompoundSpec, errors: list[str]) -> None:
    prior_version, probe_version, _ = CHAIN_REQUIREMENTS[spec.name]
    guard_scored_chain(records, prior_version, errors)
    guard_pending_probe(records, probe_version, errors)


def guard_compound(spec: CompoundSpec, records: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    add_board_freshness_error(errors)
    if not is_scored(records.get("v196")):
        errors.append("v196 scored base is missing")
        return errors
    if spec.name == "v222_plus_v225":
        guard_v222(records, errors)
        guard_v225_direct_probe(records, errors)
    elif spec.name == "v223_plus_v225":
        guard_v222(records, errors)
        guard_v223(records, errors)
        guard_v225(records, errors)
    elif spec.name in CHAIN_REQUIREMENTS:
        guard_chain_probe(records, spec, errors)
    else:
        errors.append(f"Unknown compound guard for {spec.name}")
    return errors


def prediction_path(version: str) -> Path:
    return SUBMISSIONS_DIR / f"predictions_{version}.csv"


def output_paths(name: str) -> tuple[Path, Path, Path]:
    out_dir = LOGS_DIR / f"{name}_scored_compound"
    return (
        SUBMISSIONS_DIR / f"predictions_{name}.csv",
        SUBMISSIONS_DIR / f"submission_{name}.zip",
        out_dir / "manifest.json",
    )


def write_blocked_manifest(spec: CompoundSpec, errors: list[str]) -> Path:
    _, _, manifest_path = output_paths(spec.name)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "compound": spec.name,
        "decision": "BLOCKED_NO_COMPOUND_BUILT",
        "recorded_at": utc_now_iso(),
        "errors": errors,
        "required_overlays": [overlay.version for overlay in spec.overlays],
    }
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def preflight_payload(spec: CompoundSpec, errors: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "compound": spec.name,
        "decision": "PREFLIGHT_PASS" if not errors else "PREFLIGHT_BLOCKED",
        "base_version": spec.base_version,
        "required_overlays": [overlay.version for overlay in spec.overlays],
        "errors": errors,
    }
    if not errors:
        csv_path, zip_path, manifest_path = output_paths(spec.name)
        payload.update(
            {
                "would_write": {
                    "csv_path": str(csv_path),
                    "zip_path": str(zip_path),
                    "manifest_path": str(manifest_path),
                },
                "note": "Preflight only; no CSV, ZIP, manifest, ledger, or experiment-log files were written.",
            }
        )
    return payload


def zip_prediction(csv_path: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(csv_path, arcname="predictions.csv")


def changed_mask(base: pd.DataFrame, donor: pd.DataFrame, columns: tuple[str, ...]) -> pd.Series:
    return donor.loc[:, columns].ne(base.loc[:, columns]).any(axis=1)


def validate_keys(base: pd.DataFrame, donor: pd.DataFrame, version: str, chunk_index: int) -> None:
    for key in KEY_COLS:
        left = base[key].fillna("").astype(str)
        right = donor[key].fillna("").astype(str)
        if not left.equals(right):
            raise RuntimeError(f"Row/key mismatch for {version} at chunk {chunk_index}, key {key}")


def build_compound(spec: CompoundSpec) -> dict[str, Any]:
    import pandas as pd

    base_path = prediction_path(spec.base_version)
    donor_paths = {overlay.version: prediction_path(overlay.version) for overlay in spec.overlays}
    csv_path, zip_path, manifest_path = output_paths(spec.name)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    for path in [base_path, *donor_paths.values()]:
        if not path.exists():
            raise FileNotFoundError(path)

    base_reader = pd.read_csv(base_path, chunksize=CHUNKSIZE)
    donor_readers = {
        version: pd.read_csv(path, chunksize=CHUNKSIZE)
        for version, path in donor_paths.items()
    }

    overlay_counts = {overlay.version: 0 for overlay in spec.overlays}
    rows = 0
    wrote_header = False
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    for chunk_index, base_chunk in enumerate(base_reader):
        out_chunk = base_chunk.copy()
        donor_chunks = {version: next(reader) for version, reader in donor_readers.items()}
        for overlay in spec.overlays:
            donor = donor_chunks[overlay.version]
            validate_keys(base_chunk, donor, overlay.version, chunk_index)
            mask = changed_mask(base_chunk, donor, overlay.columns)
            overlay_counts[overlay.version] += int(mask.sum())
            if mask.any():
                out_chunk.loc[mask, list(overlay.columns)] = donor.loc[mask, list(overlay.columns)].to_numpy()
        out_chunk.to_csv(csv_path, mode="w" if not wrote_header else "a", index=False, header=not wrote_header)
        wrote_header = True
        rows += len(out_chunk)

    for version, reader in donor_readers.items():
        try:
            extra = next(reader)
        except StopIteration:
            continue
        raise RuntimeError(f"Donor {version} has extra rows after base ended: {len(extra)}")

    if rows != EXPECTED_ROWS:
        raise RuntimeError(f"Compound row count {rows} != {EXPECTED_ROWS}")

    zip_prediction(csv_path, zip_path)
    zip_sha256 = sha256_file(zip_path)
    manifest = {
        "compound": spec.name,
        "decision": "BUILT_SCORE_GATED_COMPOUND",
        "base_version": spec.base_version,
        "overlays": [
            {"version": overlay.version, "label": overlay.label, "columns": list(overlay.columns), "changed_rows": overlay_counts[overlay.version]}
            for overlay in spec.overlays
        ],
        "rows": rows,
        "csv_path": str(csv_path),
        "zip_path": str(zip_path),
        "zip_sha256": zip_sha256,
        "recorded_at": utc_now_iso(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def overlay_summary(manifest: dict[str, Any]) -> str:
    overlays = manifest.get("overlays", [])
    parts = []
    for overlay in overlays:
        if isinstance(overlay, dict):
            parts.append(f"{overlay.get('version')}:{overlay.get('changed_rows')}")
    return ", ".join(parts)


def pending_record_for_compound(spec: CompoundSpec, manifest: dict[str, Any]) -> dict[str, Any]:
    overlay_versions = [overlay.version for overlay in spec.overlays]
    overlay_counts = overlay_summary(manifest)
    zip_path = Path(str(manifest["zip_path"]))
    if spec.name == "v222_plus_v225":
        description = (
            f"Direct production-preserving speed diagnostic built from {spec.base_version} "
            f"with {', '.join(overlay_versions)} overlays."
        )
        first_change = (
            "Generated by scripts/build_scored_compound.py after v222 scored clean; "
            "v225 remains a pending one-cell speed probe."
        )
        lessons = (
            "PENDING SCORE / DIRECT COMPOUND. Built to test the v225 speed cell on the "
            "v222 production base; do not upload standalone v225 unless attribution is required."
        )
    else:
        description = (
            f"Score-gated compound built from {spec.base_version} with "
            f"{', '.join(overlay_versions)} overlays."
        )
        first_change = "Generated by scripts/build_scored_compound.py after all score gates passed."
        lessons = (
            "PENDING SCORE / SCORE-GATED COMPOUND. Built only after the prerequisite "
            "score gates passed; do not treat as production until Codabench scores it."
        )
    return {
        "id": spec.name,
        "submitted_at": utc_now_iso(),
        "zip_name": zip_path.name,
        "variant": spec.name,
        "description": description,
        "changes_from_previous": [
            first_change,
            f"Base prediction order: {spec.base_version}.",
            f"Overlay versions: {', '.join(overlay_versions)}.",
            f"Overlay changed-row counts: {overlay_counts}.",
            f"Rows: {manifest['rows']:,}.",
            f"Artifact SHA256: {manifest['zip_sha256']}.",
            "Pending Codabench score; record with scripts/record_codabench_score.py after upload.",
        ],
        "local_scores": None,
        "leaderboard_scores": None,
        "_pending_score": True,
        "mean_rank": None,
        "lessons": lessons,
    }


def ensure_pending_log_record(spec: CompoundSpec, manifest: dict[str, Any], path: Path = LOG_PATH) -> str:
    records = load_record_list(path)
    for record in records:
        if record.get("id") == spec.name:
            if record.get("_pending_score"):
                return "existing-pending"
            if isinstance(record.get("mean_rank"), (int, float)):
                return "existing-scored"
            return "existing-unscored"
    records.append(pending_record_for_compound(spec, manifest))
    write_record_list(records, path)
    return "appended-pending"


def next_score_progression_number(table_text: str) -> int:
    numbers = []
    for match in re.finditer(r"^\|\s*(\d+)\s*\|", table_text, flags=re.MULTILINE):
        numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def pending_experiment_section(spec: CompoundSpec, manifest: dict[str, Any]) -> str:
    overlay_versions = ", ".join(overlay.version for overlay in spec.overlays)
    overlay_counts = overlay_summary(manifest)
    zip_path = Path(str(manifest["zip_path"]))
    try:
        zip_display = str(zip_path.relative_to(ROOT))
    except ValueError:
        zip_display = str(zip_path)
    if spec.name == "v222_plus_v225":
        title = f"## {spec.name} — Direct Compound (BUILT, PENDING SCORE)"
        approach = (
            f"Build a direct production-preserving speed diagnostic from `{spec.base_version}` "
            f"using `v222` direction overlays and the pending `v225` one-cell speed overlay."
        )
        generated = (
            "- Generated by `scripts/build_scored_compound.py` after `v222` scored clean; "
            "`v225` remains an unscored one-cell speed probe.\n"
        )
        lesson = (
            "PENDING SCORE / DIRECT COMPOUND. Upload this before standalone `v225`; "
            "use standalone `v225` only if attribution is required.\n"
        )
    else:
        title = f"## {spec.name} — Score-Gated Compound (BUILT, PENDING SCORE)"
        approach = (
            f"Build a guarded compound from `{spec.base_version}` using score-gated overlays "
            f"`{overlay_versions}`."
        )
        generated = "- Generated by `scripts/build_scored_compound.py` after score gates passed.\n"
        lesson = "PENDING SCORE / SCORE-GATED COMPOUND. Upload and score before treating this as production.\n"
    return (
        f"{title}\n\n"
        f"**Date**: {manifest['recorded_at'][:10]}  \n"
        f"**Approach**: {approach}  \n"
        f"**Base**: `{spec.base_version}`\n\n"
        "### What was done\n"
        f"{generated}"
        f"- Overlay changed-row counts: `{overlay_counts}`.\n"
        f"- Rows: `{manifest['rows']:,}`.\n"
        f"- Artifact: `{zip_display}`.\n"
        f"- SHA256: `{manifest['zip_sha256']}`.\n\n"
        "### Lesson\n"
        f"{lesson}"
    )


def ensure_pending_experiment_log(spec: CompoundSpec, manifest: dict[str, Any], path: Path = EXPERIMENT_LOG_PATH) -> str:
    if not path.exists():
        return "experiment-log-missing"
    text = path.read_text(encoding="utf-8")
    if f"| {spec.name} |" in text and f"## {spec.name} " in text:
        return "existing"

    progression_header = "## Score Progression"
    progression_start = text.find(progression_header)
    if progression_start < 0:
        return "score-progression-missing"
    progression_end = text.find("\n---", progression_start)
    if progression_end < 0:
        return "score-progression-end-missing"
    table_text = text[progression_start:progression_end]
    number = next_score_progression_number(table_text)
    overlay_counts = overlay_summary(manifest)
    if spec.name == "v222_plus_v225":
        row = (
            f"| {number} | {spec.name} | PENDING | DIRECT COMPOUND / PENDING SCORE | "
            f"{overlay_counts} | {spec.base_version} + v222 direction + pending v225 speed overlay; "
            "upload before standalone v225 |\n"
        )
    else:
        row = (
            f"| {number} | {spec.name} | PENDING | BUILT COMPOUND / PENDING SCORE | "
            f"{overlay_counts} | {spec.base_version} + score-gated overlays; built by guarded compound script |\n"
        )
    text = text[:progression_end] + row + text[progression_end:]

    section = pending_experiment_section(spec, manifest)
    insert_marker = "\n## s001 "
    section_at = text.find(insert_marker)
    if section_at >= 0:
        text = text[:section_at] + section + "\n" + text[section_at + 1 :]
    else:
        text = text.rstrip() + "\n\n" + section
    path.write_text(text, encoding="utf-8")
    return "appended"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "compound",
        choices=sorted(COMPOUNDS),
        help="Compound to build after score gates pass.",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Evaluate score gates and print the planned outputs without writing files.",
    )
    args = parser.parse_args()

    spec = COMPOUNDS[args.compound]
    errors = guard_compound(spec, load_records())
    if args.preflight:
        print(json.dumps(preflight_payload(spec, errors), indent=2))
        return 0 if not errors else 2

    if errors:
        manifest_path = write_blocked_manifest(spec, errors)
        print(json.dumps({"decision": "BLOCKED_NO_COMPOUND_BUILT", "compound": spec.name, "errors": errors, "manifest": str(manifest_path)}, indent=2))
        return 2

    manifest = build_compound(spec)
    manifest["log_state"] = ensure_pending_log_record(spec, manifest)
    manifest["experiment_log_state"] = ensure_pending_experiment_log(spec, manifest)
    _, _, manifest_path = output_paths(spec.name)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
