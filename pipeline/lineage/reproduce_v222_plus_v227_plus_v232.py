#!/usr/bin/env python
"""Reproduce the v222+v227+v232 guarded compound submission.

This script is intentionally conservative.  The final competition artifact is a
direction-only compound built from historical, scored prediction artifacts:

    base v196 -> overlay v222 -> overlay v227 -> overlay v232

The overlay order and "copy only where donor differs from base" rule match
``scripts/build_scored_compound.py``.  The default ``--mode full`` verifies the
official raw dataset, source scripts, and lineage artifacts before rebuilding
the final CSV/ZIP.  Passing ``--force`` in full mode also reruns the historical
lineage scripts in place, which can be expensive and can overwrite generated
artifacts under ``submissions/`` and ``logs/``.

Exact ZIP bytes are not asserted because ZIP metadata can vary.  Exact CSV
content is mandatory and is checked by SHA256.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import warnings
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "data" / "phase1_dataset"
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"
STARTING_KIT_PHASE1 = PROJECT_ROOT / "starting-kit" / "phase_1"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "repro_outputs" / "v222_plus_v227_plus_v232"

EXPECTED_ROWS = 3_448_800
EXPECTED_FINAL_CSV_SHA256 = (
    "5d5c1ba9ab92f2761136a68ec0e9f8290e7571bf73a74cb327c336935dd2f675"
)
EXPECTED_REFERENCE_ZIP_SHA256 = (
    "13c9fa055374733e757dbb396a5166ea0070f376d773fd348a28db54e9f1656f"
)

FINAL_NAME = "v222_plus_v227_plus_v232"
BASE_VERSION = "v196"
CHUNKSIZE = 200_000

KEY_COLUMNS = [
    "type",
    "window",
    "region",
    "latitude",
    "longitude",
    "station",
    "horizon",
    "hour",
    "level",
]
Q_COLUMNS = ["q05", "q50", "q95"]
DIR_COLUMNS = ["dir_05", "dir_50", "dir_95"]
PREDICTION_COLUMNS = Q_COLUMNS + DIR_COLUMNS
SUBMISSION_COLUMNS = KEY_COLUMNS + PREDICTION_COLUMNS
CSV_KEY_DTYPES = {"station": "string", "level": "string"}

REFERENCE_FINAL_CSV = SUBMISSIONS_DIR / f"predictions_{FINAL_NAME}.csv"
REFERENCE_FINAL_ZIP = SUBMISSIONS_DIR / f"submission_{FINAL_NAME}.zip"

pd = None


@dataclass(frozen=True)
class OverlaySpec:
    version: str
    label: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class LineageStep:
    version: str
    script: str
    output: str
    description: str


OVERLAYS = (
    OverlaySpec("v222", "direction_compound_v222", tuple(DIR_COLUMNS)),
    OverlaySpec("v227", "station_d1_ns_direction_probe_v227", tuple(DIR_COLUMNS)),
    OverlaySpec("v232", "station_d7_ns_direction_probe_v232", tuple(DIR_COLUMNS)),
)

LINEAGE_STEPS = (
    LineageStep(
        "v53",
        "src/experiments/pressure_shear_v53.py",
        "predictions_v53.csv",
        "Pressure-speed ladder root.",
    ),
    LineageStep(
        "v55",
        "src/experiments/pressure_shear_v55.py",
        "predictions_v55.csv",
        "Pressure-speed ladder refinement.",
    ),
    LineageStep(
        "v162",
        "src/experiments/v162_pressure_d14_ecs_push.py",
        "predictions_v162.csv",
        "ECS pressure d14 speed push root.",
    ),
    LineageStep(
        "v163",
        "src/experiments/v163_pressure_d14_ecs_push65.py",
        "predictions_v163.csv",
        "ECS pressure d14 speed push amplitude 65.",
    ),
    LineageStep(
        "v164",
        "src/experiments/v164_pressure_d14_ecs_925_push80.py",
        "predictions_v164.csv",
        "ECS pressure d14 925 hPa speed push.",
    ),
    LineageStep(
        "v166",
        "src/experiments/v166_pressure_d14_ecs_850_push80.py",
        "predictions_v166.csv",
        "ECS pressure d14 850 hPa speed push.",
    ),
    LineageStep(
        "v167",
        "src/experiments/v167_v172_breakthrough_batch.py",
        "predictions_v167.csv",
        "Breakthrough batch member used by v173 lineage.",
    ),
    LineageStep(
        "v173",
        "src/experiments/v173_pressure_d14_ecs_final_crossing.py",
        "predictions_v173.csv",
        "Clean production base before Lane A direction work.",
    ),
    LineageStep(
        "v191",
        "src/experiments/v191_ecs_pressure_d7_direction_response.py",
        "predictions_v191.csv",
        "ECS pressure d7 direction response.",
    ),
    LineageStep(
        "v196",
        "src/experiments/v196_ecs_pressure_d7_direction_mild_plus.py",
        "predictions_v196.csv",
        "Production base for the final guarded compound.",
    ),
    LineageStep(
        "v183",
        "src/experiments/v183_station_direction_asymmetric_widths.py",
        "predictions_v183.csv",
        "Station direction asymmetric width ingredient.",
    ),
    LineageStep(
        "v202",
        "src/experiments/v202_ns_pressure_d7_direction_aggressive.py",
        "predictions_v202.csv",
        "NS pressure d7 direction aggressive response.",
    ),
    LineageStep(
        "v203",
        "src/experiments/v203_ns_surface_d7_direction_shrink.py",
        "predictions_v203.csv",
        "NS surface d7 direction shrink ingredient.",
    ),
    LineageStep(
        "v204",
        "src/experiments/v204_stations_d14_ns_climo_widening.py",
        "predictions_v204.csv",
        "Station d14 NS climatological widening, later undone.",
    ),
    LineageStep(
        "v207",
        "src/experiments/v207_compound_v191_v202_v203_v204.py",
        "predictions_v207.csv",
        "Compound of v191/v202/v203/v204.",
    ),
    LineageStep(
        "v209",
        "src/experiments/v209_lane_a_ecs_pressure_d7_dir.py",
        "predictions_v209.csv",
        "Lane A ECS pressure d7 direction endpoint response.",
    ),
    LineageStep(
        "v211",
        "src/experiments/v211_lane_a_ns_pressure_d7_dir.py",
        "predictions_v211.csv",
        "Lane A NS pressure d7 direction endpoint response.",
    ),
    LineageStep(
        "v212",
        "src/experiments/v212_compound_v209_v211_lane_a.py",
        "predictions_v212.csv",
        "Lane A pressure d7 compound.",
    ),
    LineageStep(
        "v222",
        "src/experiments/v222_v212_plus_undo_v204.py",
        "predictions_v222.csv",
        "v212 plus v204 station d14 NS undo.",
    ),
    LineageStep(
        "v227",
        "src/experiments/v227_station_d1_ns_direction_micro_shrink.py",
        "predictions_v227.csv",
        "Station d1 NS direction center-frozen micro shrink.",
    ),
    LineageStep(
        "v232",
        "src/experiments/v232_station_d7_ns_asymmetric_width_salvage.py",
        "predictions_v232.csv",
        "Station d7 NS direction endpoints copied from v183.",
    ),
)

REQUIRED_RAW_FILES = (
    "scoring/sample_submission.csv",
    "scoring/station_metadata.csv",
    "train/reanalysis_north_sea_6h.parquet",
    "train/reanalysis_east_china_sea_6h.parquet",
    "train/reanalysis_pressure_north_sea.parquet",
    "train/reanalysis_pressure_east_china_sea.parquet",
    "train/hres_north_sea.parquet",
    "train/hres_east_china_sea.parquet",
    "train/hres_pressure_north_sea.parquet",
    "train/hres_pressure_east_china_sea.parquet",
    "train/stations_north_sea_6h.parquet",
    "train/stations_east_china_sea_6h.parquet",
    "features/inference_window_1_north_sea.parquet",
    "features/inference_window_1_east_china_sea.parquet",
    "features/inference_window_2_north_sea.parquet",
    "features/inference_window_2_east_china_sea.parquet",
    "features/inference_window_3_north_sea.parquet",
    "features/inference_window_3_east_china_sea.parquet",
    "features/inference_window_4_north_sea.parquet",
    "features/inference_window_4_east_china_sea.parquet",
    "features/inference_window_5_north_sea.parquet",
    "features/inference_window_5_east_china_sea.parquet",
    "features/inference_window_6_north_sea.parquet",
    "features/inference_window_6_east_china_sea.parquet",
    "features/inference_window_7_north_sea.parquet",
    "features/inference_window_7_east_china_sea.parquet",
    "features/inference_window_8_north_sea.parquet",
    "features/inference_window_8_east_china_sea.parquet",
)


class ReproductionError(RuntimeError):
    """Raised when a reproducibility invariant fails."""


def require_pandas():
    global pd
    if pd is None:
        pd = importlib.import_module("pandas")
    return pd


def ensure_project_venv() -> dict[str, str]:
    exe = Path(sys.executable)
    venv_root = (PROJECT_ROOT / ".venv").resolve()
    candidates = [
        exe,
        Path(sys.prefix),
        Path(os.environ["VIRTUAL_ENV"]) if os.environ.get("VIRTUAL_ENV") else None,
    ]
    in_venv = False
    for candidate in candidates:
        if candidate is None:
            continue
        try:
            resolved = candidate.resolve()
            if resolved.is_relative_to(venv_root):
                in_venv = True
                break
        except AttributeError:
            resolved = candidate.resolve()
            if str(resolved).startswith(str(venv_root)):
                in_venv = True
                break
    if not in_venv:
        raise ReproductionError(
            "Run this script with the project venv: "
            f"{PROJECT_ROOT / '.venv' / 'bin' / 'python'}"
        )

    pandas = require_pandas()
    numpy = importlib.import_module("numpy")
    return {
        "python": sys.version.split()[0],
        "executable": str(exe),
        "executable_resolved": str(exe.resolve()),
        "prefix": sys.prefix,
        "pandas": pandas.__version__,
        "numpy": numpy.__version__,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_zip_member(zip_path: Path, member_name: str) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member_name, "r") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def require_existing(path: Path, label: str) -> None:
    if not path.exists():
        raise ReproductionError(f"Missing {label}: {path}")


def verify_required_raw_files() -> list[dict[str, Any]]:
    require_existing(DATASET_DIR, "official dataset directory")
    records = []
    missing = []
    for rel in REQUIRED_RAW_FILES:
        path = DATASET_DIR / rel
        if not path.exists():
            missing.append(str(path))
            continue
        records.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": path.stat().st_size,
            }
        )
    if missing:
        raise ReproductionError(
            "Missing required official dataset files:\n" + "\n".join(missing)
        )
    return records


def verify_source_scripts() -> list[dict[str, Any]]:
    scripts = ["scripts/build_scored_compound.py"] + [
        step.script for step in LINEAGE_STEPS
    ]
    records = []
    missing = []
    for rel in scripts:
        path = PROJECT_ROOT / rel
        if not path.exists():
            missing.append(str(path))
            continue
        records.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    if missing:
        raise ReproductionError(
            "Missing source scripts for the encoded DAG:\n" + "\n".join(missing)
        )
    return records


def prediction_path(version: str) -> Path:
    candidates = [
        SUBMISSIONS_DIR / f"predictions_{version}.csv",
        STARTING_KIT_PHASE1 / f"predictions_{version}.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ReproductionError(
        f"Missing prediction artifact for {version}; checked: "
        + ", ".join(str(p) for p in candidates)
    )


def zip_path(version: str) -> Path:
    candidates = [
        SUBMISSIONS_DIR / f"submission_{version}.zip",
        STARTING_KIT_PHASE1 / f"submission_{version}.zip",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ReproductionError(
        f"Missing submission ZIP for {version}; checked: "
        + ", ".join(str(p) for p in candidates)
    )


def read_header(path: Path) -> list[str]:
    with path.open("r", newline="") as fh:
        reader = csv.reader(fh)
        return next(reader)


def validate_prediction_csv(path: Path, *, deep: bool = False) -> dict[str, Any]:
    pandas = require_pandas()
    header = read_header(path)
    if header != SUBMISSION_COLUMNS:
        raise ReproductionError(
            f"{path} has unexpected columns.\n"
            f"Expected: {SUBMISSION_COLUMNS}\nActual:   {header}"
        )

    rows = 0
    q_crossings = 0
    negative_q05 = 0
    nan_rows = 0

    read_kwargs: dict[str, Any] = {
        "chunksize": CHUNKSIZE,
        "dtype": CSV_KEY_DTYPES,
    }
    if not deep:
        read_kwargs["usecols"] = PREDICTION_COLUMNS

    for chunk in pandas.read_csv(path, **read_kwargs):
        rows += len(chunk)
        pred = chunk[PREDICTION_COLUMNS]
        nan_rows += int(pred.isna().any(axis=1).sum())
        q_crossings += int(
            ((chunk["q05"] > chunk["q50"]) | (chunk["q50"] > chunk["q95"])).sum()
        )
        negative_q05 += int((chunk["q05"] < 0).sum())

    if rows != EXPECTED_ROWS:
        raise ReproductionError(f"{path} row count {rows:,} != {EXPECTED_ROWS:,}")
    if nan_rows:
        raise ReproductionError(f"{path} contains {nan_rows:,} rows with NaNs")
    if q_crossings:
        raise ReproductionError(
            f"{path} contains {q_crossings:,} speed quantile crossings"
        )
    if negative_q05:
        raise ReproductionError(f"{path} contains {negative_q05:,} negative q05")

    return {
        "path": str(path),
        "rows": rows,
        "columns": header,
        "sha256": sha256_file(path),
        "nan_rows": nan_rows,
        "q_crossings": q_crossings,
        "negative_q05": negative_q05,
    }


def validate_zip_structure(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if names != ["predictions.csv"]:
            raise ReproductionError(
                f"{path} must contain exactly one predictions.csv; got {names}"
            )
        inner_hash = sha256_zip_member(path, "predictions.csv")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "members": names,
        "inner_predictions_sha256": inner_hash,
    }


def normalize_keys(df):
    keys = df[KEY_COLUMNS].astype("string").fillna("")
    # Some historical CSVs serialize pressure levels as 700 while the final
    # scored compound serializes the same key as 700.0 near chunk boundaries.
    # The scorer treats both as the same level after parsing; the reproducer
    # normalizes only the stable key representation, never prediction values.
    keys["level"] = keys["level"].str.replace(r"\.0$", "", regex=True)
    return keys.astype(str)


def assert_same_keys(left, right, left_label: str, right_label: str) -> None:
    mismatch = normalize_keys(left).ne(normalize_keys(right)).any(axis=1)
    if bool(mismatch.any()):
        first = int(mismatch.idxmax())
        raise ReproductionError(
            f"Stable key mismatch between {left_label} and {right_label} "
            f"near parsed row index {first}"
        )


def changed_mask(base, donor, columns: Iterable[str]):
    return donor[list(columns)].ne(base[list(columns)]).any(axis=1)


def build_final_compound(output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    pandas = require_pandas()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_csv = output_dir / f"predictions_{FINAL_NAME}.csv"
    out_zip = output_dir / f"submission_{FINAL_NAME}.zip"

    base_path = prediction_path(BASE_VERSION)
    donor_paths = {overlay.version: prediction_path(overlay.version) for overlay in OVERLAYS}
    overlay_counts = {overlay.version: 0 for overlay in OVERLAYS}
    rows = 0

    # Do not force key dtypes in build mode.  The submitted CSV hash depends on
    # pandas' original mixed-type parsing/serialization behavior from
    # scripts/build_scored_compound.py.
    base_iter = pandas.read_csv(base_path, chunksize=CHUNKSIZE)
    donor_iters = {
        version: pandas.read_csv(path, chunksize=CHUNKSIZE)
        for version, path in donor_paths.items()
    }

    with out_csv.open("w", newline="") as out_fh:
        first = True
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pandas.errors.DtypeWarning)
            for base_chunk in base_iter:
                result = base_chunk.copy()
                rows += len(base_chunk)
                for overlay in OVERLAYS:
                    donor_chunk = next(donor_iters[overlay.version])
                    assert_same_keys(
                        base_chunk,
                        donor_chunk,
                        BASE_VERSION,
                        overlay.version,
                    )
                    mask = changed_mask(base_chunk, donor_chunk, overlay.columns)
                    overlay_counts[overlay.version] += int(mask.sum())
                    result.loc[mask, list(overlay.columns)] = donor_chunk.loc[
                        mask, list(overlay.columns)
                    ]
                result.to_csv(out_fh, index=False, header=first)
                first = False

    if rows != EXPECTED_ROWS:
        raise ReproductionError(f"Built row count {rows:,} != {EXPECTED_ROWS:,}")

    write_zip(out_csv, out_zip)
    build_info = {
        "base_version": BASE_VERSION,
        "base_path": str(base_path),
        "overlays": [
            {
                "version": overlay.version,
                "label": overlay.label,
                "columns": list(overlay.columns),
                "source_path": str(donor_paths[overlay.version]),
                "changed_rows": overlay_counts[overlay.version],
            }
            for overlay in OVERLAYS
        ],
        "rows": rows,
    }
    return out_csv, out_zip, build_info


def write_zip(csv_path: Path, zip_out: Path) -> None:
    with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname="predictions.csv")


def target_mask_station_ns(chunk, horizon: int):
    return (
        chunk["type"].eq("station")
        & chunk["region"].eq("north_sea")
        & chunk["horizon"].eq(horizon)
    )


def verify_compound_logic(final_csv: Path) -> dict[str, Any]:
    pandas = require_pandas()
    base_path = prediction_path(BASE_VERSION)
    donor_paths = {overlay.version: prediction_path(overlay.version) for overlay in OVERLAYS}

    base_iter = pandas.read_csv(base_path, chunksize=CHUNKSIZE, dtype=CSV_KEY_DTYPES)
    final_iter = pandas.read_csv(final_csv, chunksize=CHUNKSIZE, dtype=CSV_KEY_DTYPES)
    donor_iters = {
        version: pandas.read_csv(path, chunksize=CHUNKSIZE, dtype=CSV_KEY_DTYPES)
        for version, path in donor_paths.items()
    }

    overlay_counts = {overlay.version: 0 for overlay in OVERLAYS}
    rows = 0
    speed_change_rows = 0
    v227_dir50_target_changes = 0
    v232_dir50_target_changes = 0
    q_crossings = 0
    negative_q05 = 0
    nan_rows = 0

    for base_chunk in base_iter:
        final_chunk = next(final_iter)
        rows += len(base_chunk)
        assert_same_keys(base_chunk, final_chunk, BASE_VERSION, FINAL_NAME)
        expected = base_chunk.copy()
        donor_chunks = {}

        for overlay in OVERLAYS:
            donor_chunk = next(donor_iters[overlay.version])
            donor_chunks[overlay.version] = donor_chunk
            assert_same_keys(base_chunk, donor_chunk, BASE_VERSION, overlay.version)
            mask = changed_mask(base_chunk, donor_chunk, overlay.columns)
            overlay_counts[overlay.version] += int(mask.sum())
            expected.loc[mask, list(overlay.columns)] = donor_chunk.loc[
                mask, list(overlay.columns)
            ]

        mismatch = final_chunk[PREDICTION_COLUMNS].ne(expected[PREDICTION_COLUMNS])
        if bool(mismatch.any(axis=None)):
            bad_cols = mismatch.any(axis=0)
            bad_rows = int(mismatch.any(axis=1).sum())
            raise ReproductionError(
                f"{final_csv} does not match deterministic compound logic; "
                f"{bad_rows:,} mismatched rows, columns "
                f"{list(bad_cols[bad_cols].index)}"
            )

        speed_change_rows += int(final_chunk[Q_COLUMNS].ne(base_chunk[Q_COLUMNS]).any(axis=1).sum())
        q_crossings += int(
            (
                (final_chunk["q05"] > final_chunk["q50"])
                | (final_chunk["q50"] > final_chunk["q95"])
            ).sum()
        )
        negative_q05 += int((final_chunk["q05"] < 0).sum())
        nan_rows += int(final_chunk[PREDICTION_COLUMNS].isna().any(axis=1).sum())

        donor_v222 = donor_chunks["v222"]
        v227_mask = target_mask_station_ns(final_chunk, 1)
        v232_mask = target_mask_station_ns(final_chunk, 7)
        v227_dir50_target_changes += int(
            final_chunk.loc[v227_mask, "dir_50"]
            .ne(donor_v222.loc[v227_mask, "dir_50"])
            .sum()
        )
        v232_dir50_target_changes += int(
            final_chunk.loc[v232_mask, "dir_50"]
            .ne(donor_v222.loc[v232_mask, "dir_50"])
            .sum()
        )

    if rows != EXPECTED_ROWS:
        raise ReproductionError(f"Compound logic checked {rows:,} rows, expected {EXPECTED_ROWS:,}")
    if speed_change_rows:
        raise ReproductionError(
            f"Direction-only final compound changed speed columns in "
            f"{speed_change_rows:,} rows"
        )
    if v227_dir50_target_changes:
        raise ReproductionError(
            "v227 station d1 NS direction target changed dir_50 relative to v222 "
            f"in {v227_dir50_target_changes:,} rows"
        )
    if v232_dir50_target_changes:
        raise ReproductionError(
            "v232 station d7 NS direction target changed dir_50 relative to v222 "
            f"in {v232_dir50_target_changes:,} rows"
        )
    if q_crossings or negative_q05 or nan_rows:
        raise ReproductionError(
            "Final compound pathology detected: "
            f"q_crossings={q_crossings}, negative_q05={negative_q05}, nan_rows={nan_rows}"
        )

    return {
        "rows": rows,
        "overlay_changed_rows": overlay_counts,
        "speed_change_rows_vs_base": speed_change_rows,
        "v227_dir50_target_changes_vs_v222": v227_dir50_target_changes,
        "v232_dir50_target_changes_vs_v222": v232_dir50_target_changes,
        "q_crossings": q_crossings,
        "negative_q05": negative_q05,
        "nan_rows": nan_rows,
    }


def verify_final_artifacts(csv_path: Path, zip_out: Path) -> dict[str, Any]:
    csv_info = validate_prediction_csv(csv_path, deep=False)
    if csv_info["sha256"] != EXPECTED_FINAL_CSV_SHA256:
        raise ReproductionError(
            f"Final CSV SHA256 mismatch.\n"
            f"Expected: {EXPECTED_FINAL_CSV_SHA256}\n"
            f"Actual:   {csv_info['sha256']}"
        )

    zip_info = validate_zip_structure(zip_out)
    if zip_info["inner_predictions_sha256"] != EXPECTED_FINAL_CSV_SHA256:
        raise ReproductionError(
            f"ZIP inner predictions.csv SHA256 mismatch: "
            f"{zip_info['inner_predictions_sha256']}"
        )

    reference_zip_info = None
    if REFERENCE_FINAL_ZIP.exists():
        reference_zip_info = validate_zip_structure(REFERENCE_FINAL_ZIP)
    return {
        "csv": csv_info,
        "zip": zip_info,
        "reference_zip": reference_zip_info,
        "expected_csv_sha256": EXPECTED_FINAL_CSV_SHA256,
        "expected_reference_zip_sha256": EXPECTED_REFERENCE_ZIP_SHA256,
    }


def verify_intermediate_artifacts(*, deep: bool = False) -> list[dict[str, Any]]:
    versions = [BASE_VERSION] + [overlay.version for overlay in OVERLAYS]
    records = []
    for version in versions:
        path = prediction_path(version)
        info = validate_prediction_csv(path, deep=deep)
        info["version"] = version
        records.append(info)
    return records


def run_lineage_scripts(force: bool, start_at: str | None = None) -> list[dict[str, Any]]:
    results = []
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not existing_pythonpath
        else f"{PROJECT_ROOT}{os.pathsep}{existing_pythonpath}"
    )
    if not force:
        for step in LINEAGE_STEPS:
            path = prediction_path(step.version)
            results.append(
                {
                    "version": step.version,
                    "script": step.script,
                    "status": "verified_existing_artifact",
                    "output": str(path),
                    "description": step.description,
                }
            )
        return results

    started = start_at is None
    for step in LINEAGE_STEPS:
        if not started:
            if step.version == start_at:
                started = True
            else:
                results.append(
                    {
                        "version": step.version,
                        "script": step.script,
                        "status": f"skipped_before_start_at_{start_at}",
                        "output": str(prediction_path(step.version)),
                        "description": step.description,
                    }
                )
                continue
        stage_legacy_inputs_for_step(step.version)
        script_path = PROJECT_ROOT / step.script
        require_existing(script_path, f"lineage script for {step.version}")
        started = dt.datetime.now(dt.timezone.utc)
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        ended = dt.datetime.now(dt.timezone.utc)
        record = {
            "version": step.version,
            "script": step.script,
            "status": "executed" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "description": step.description,
        }
        if proc.returncode != 0:
            results.append(record)
            raise ReproductionError(
                f"Lineage script failed for {step.version}: {step.script}\n"
                f"stderr tail:\n{proc.stderr[-4000:]}"
            )
        path = prediction_path(step.version)
        record["output"] = str(path)
        results.append(record)
    return results


def stage_legacy_prediction(version: str) -> dict[str, Any]:
    source = SUBMISSIONS_DIR / f"predictions_{version}.csv"
    dest = STARTING_KIT_PHASE1 / f"predictions_{version}.csv"
    require_existing(source, f"canonical predictions for {version}")
    STARTING_KIT_PHASE1.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return {
            "version": version,
            "status": "already_present",
            "path": str(dest),
            "sha256": sha256_file(dest),
        }
    shutil.copy2(source, dest)
    return {
        "version": version,
        "status": "copied_from_submissions",
        "source": str(source),
        "path": str(dest),
        "sha256": sha256_file(dest),
    }


def stage_legacy_inputs_for_step(version: str) -> list[dict[str, Any]]:
    if version == "v53":
        return [stage_legacy_prediction("v51")]
    if version == "v55":
        return [stage_legacy_prediction("v53")]
    if version == "v162":
        return [
            stage_legacy_prediction("v156"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
        ]
    if version == "v163":
        return [
            stage_legacy_prediction("v162"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
        ]
    if version == "v164":
        return [
            stage_legacy_prediction("v163"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
        ]
    if version == "v166":
        return [
            stage_legacy_prediction("v164"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
        ]
    if version == "v167":
        return [
            stage_legacy_prediction("v164"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
            stage_legacy_prediction("v157"),
        ]
    if version == "v173":
        return [
            stage_legacy_prediction("v167"),
            stage_legacy_prediction("v53"),
            stage_legacy_prediction("v55"),
        ]
    if version == "v207":
        return [
            stage_legacy_prediction("v191"),
            stage_legacy_prediction("v202"),
            stage_legacy_prediction("v203"),
            stage_legacy_prediction("v204"),
            stage_legacy_prediction("v173"),
        ]
    if version == "v212":
        return [
            stage_legacy_prediction("v207"),
            stage_legacy_prediction("v209"),
            stage_legacy_prediction("v211"),
        ]
    return []


def load_score_summary() -> dict[str, Any]:
    log_path = SUBMISSIONS_DIR / "log.json"
    if not log_path.exists():
        return {}
    data = json.loads(log_path.read_text())
    wanted = {
        "v196",
        "v222",
        "v227",
        "v232",
        FINAL_NAME,
    }
    summary = {}
    for record in data:
        record_id = record.get("id")
        if record_id in wanted:
            summary[record_id] = {
                "variant": record.get("variant"),
                "zip_name": record.get("zip_name"),
                "mean_rank": record.get("mean_rank"),
                "leaderboard_scores": record.get("leaderboard_scores"),
                "lessons": record.get("lessons"),
                "pending": record.get("_pending_score", False),
            }
    return summary


def make_manifest(
    *,
    args: argparse.Namespace,
    env_info: dict[str, str],
    output_dir: Path,
    raw_files: list[dict[str, Any]] | None,
    source_scripts: list[dict[str, Any]],
    lineage_results: list[dict[str, Any]],
    intermediate_info: list[dict[str, Any]],
    build_info: dict[str, Any] | None,
    final_verification: dict[str, Any],
    compound_checks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "artifact": FINAL_NAME,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "command": " ".join([str(Path(sys.executable).resolve()), *sys.argv]),
        "mode": args.mode,
        "verify_only": args.verify_only,
        "force": args.force,
        "start_at": args.start_at,
        "output_dir": str(output_dir),
        "environment": env_info,
        "raw_dataset_files": raw_files,
        "source_scripts": source_scripts,
        "lineage": [asdict(step) for step in LINEAGE_STEPS],
        "lineage_results": lineage_results,
        "intermediate_artifacts": intermediate_info,
        "compound_spec": {
            "base_version": BASE_VERSION,
            "overlays": [asdict(overlay) for overlay in OVERLAYS],
            "rule": (
                "For each overlay in order, copy the listed columns where the "
                "donor differs from the base version."
            ),
        },
        "build": build_info,
        "compound_checks": compound_checks,
        "final_verification": final_verification,
        "score_summary": load_score_summary(),
    }


def write_manifest_and_report(output_dir: Path, manifest: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "reproduction_manifest.json"
    report_path = output_dir / "lineage_report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    report_path.write_text(render_lineage_report(manifest))


def render_lineage_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Reproduction Report: {FINAL_NAME}",
        "",
        f"- Created at: `{manifest['created_at']}`",
        f"- Mode: `{manifest['mode']}`",
        f"- Verify only: `{manifest['verify_only']}`",
        f"- Force: `{manifest['force']}`",
        f"- Python: `{manifest['environment']['executable']}`",
        f"- pandas/numpy: `{manifest['environment']['pandas']}` / `{manifest['environment']['numpy']}`",
        "",
        "## Final Verification",
        "",
        f"- CSV SHA256: `{manifest['final_verification']['csv']['sha256']}`",
        f"- Expected CSV SHA256: `{manifest['final_verification']['expected_csv_sha256']}`",
        f"- ZIP path: `{manifest['final_verification']['zip']['path']}`",
        f"- ZIP members: `{manifest['final_verification']['zip']['members']}`",
        f"- Inner predictions.csv SHA256: `{manifest['final_verification']['zip']['inner_predictions_sha256']}`",
        "",
        "## Compound Spec",
        "",
        f"- Base: `{BASE_VERSION}`",
        "",
        "| Order | Donor | Label | Columns | Changed Rows |",
        "|---:|---|---|---|---:|",
    ]
    overlay_counts = manifest["compound_checks"]["overlay_changed_rows"]
    for idx, overlay in enumerate(manifest["compound_spec"]["overlays"], start=1):
        version = overlay["version"]
        lines.append(
            f"| {idx} | `{version}` | {overlay['label']} | "
            f"`{', '.join(overlay['columns'])}` | {overlay_counts.get(version, 0):,} |"
        )

    lines += [
        "",
        "## Frozen Checks",
        "",
        f"- Speed-change rows vs base: `{manifest['compound_checks']['speed_change_rows_vs_base']}`",
        f"- v227 dir_50 target changes vs v222: `{manifest['compound_checks']['v227_dir50_target_changes_vs_v222']}`",
        f"- v232 dir_50 target changes vs v222: `{manifest['compound_checks']['v232_dir50_target_changes_vs_v222']}`",
        f"- q crossings: `{manifest['compound_checks']['q_crossings']}`",
        f"- negative q05 rows: `{manifest['compound_checks']['negative_q05']}`",
        f"- NaN rows: `{manifest['compound_checks']['nan_rows']}`",
        "",
        "## Lineage DAG",
        "",
        "| Version | Script | Status | Description |",
        "|---|---|---|---|",
    ]
    status_by_version = {
        result["version"]: result.get("status", "not_recorded")
        for result in manifest["lineage_results"]
    }
    for step in manifest["lineage"]:
        lines.append(
            f"| `{step['version']}` | `{step['script']}` | "
            f"{status_by_version.get(step['version'], 'not_recorded')} | "
            f"{step['description']} |"
        )

    score_summary = manifest.get("score_summary", {})
    if score_summary:
        lines += [
            "",
            "## Score Summary",
            "",
            "| Version | Mean Rank | Notes |",
            "|---|---:|---|",
        ]
        for version in ["v196", "v222", "v227", "v232", FINAL_NAME]:
            record = score_summary.get(version)
            if not record:
                continue
            pending = " PENDING" if record.get("pending") else ""
            lessons = record.get("lessons") or ""
            lines.append(
                f"| `{version}` | {record.get('mean_rank')}{pending} | "
                f"{str(lessons).replace('|', '/')} |"
            )

    lines += [
        "",
        "## Audit Command",
        "",
        "```bash",
        ".venv/bin/python scripts/reproduce_v222_plus_v227_plus_v232.py "
        "--mode full --output-dir repro_outputs/v222_plus_v227_plus_v232 --force",
        "```",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce and verify submission_v222_plus_v227_plus_v232.zip."
    )
    parser.add_argument(
        "--mode",
        choices=("full", "fast"),
        default="full",
        help="full verifies the raw dataset and encoded DAG; fast uses existing intermediates.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for rebuilt outputs and reproduction reports.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Force rebuild cached outputs. In full mode this reruns historical "
            "lineage scripts in place."
        ),
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing artifacts and write manifest/report without rebuilding.",
    )
    parser.add_argument(
        "--start-at",
        choices=[step.version for step in LINEAGE_STEPS],
        default=None,
        help=(
            "Resume full-mode lineage execution at a specific version after a "
            "previous interrupted audit run. Ignored in fast mode."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    env_info = ensure_project_venv()
    source_scripts = verify_source_scripts()
    raw_files = verify_required_raw_files() if args.mode == "full" else None

    lineage_results: list[dict[str, Any]]
    if args.mode == "full":
        lineage_results = run_lineage_scripts(
            args.force and not args.verify_only,
            start_at=args.start_at,
        )
    else:
        lineage_results = [
            {
                "version": version,
                "status": "verified_existing_artifact",
                "output": str(prediction_path(version)),
            }
            for version in [BASE_VERSION, *[overlay.version for overlay in OVERLAYS]]
        ]

    intermediate_info = verify_intermediate_artifacts(deep=False)

    if args.verify_only:
        final_csv = REFERENCE_FINAL_CSV
        final_zip = REFERENCE_FINAL_ZIP
        build_info = None
    else:
        final_csv, final_zip, build_info = build_final_compound(output_dir)

    require_existing(final_csv, "final prediction CSV")
    require_existing(final_zip, "final submission ZIP")
    compound_checks = verify_compound_logic(final_csv)
    final_verification = verify_final_artifacts(final_csv, final_zip)

    manifest = make_manifest(
        args=args,
        env_info=env_info,
        output_dir=output_dir,
        raw_files=raw_files,
        source_scripts=source_scripts,
        lineage_results=lineage_results,
        intermediate_info=intermediate_info,
        build_info=build_info,
        final_verification=final_verification,
        compound_checks=compound_checks,
    )
    write_manifest_and_report(output_dir, manifest)

    print(f"[ok] {FINAL_NAME} reproduced/verified")
    print(f"[ok] manifest: {output_dir / 'reproduction_manifest.json'}")
    print(f"[ok] report:   {output_dir / 'lineage_report.md'}")
    print(f"[ok] csv sha:  {final_verification['csv']['sha256']}")
    print(f"[ok] zip inner predictions.csv sha: {final_verification['zip']['inner_predictions_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReproductionError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(2)
