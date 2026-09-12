"""Machine-readable MaleCNS v1.0 manifest and bounded validation helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow.feather as feather


MALECNS_VERSION = "v1.0"
MALECNS_SOURCE_PAGE = "https://male-cns.janelia.org/download/"
ROLE_GLOBS = {
    "annotations": "body-annotations*.feather",
    "neurotransmitters": "body-neurotransmitters*.feather",
    "weights": "connectome-weights*.feather",
}
EXPECTED_FILENAMES = {
    "annotations": "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "neurotransmitters": "body-neurotransmitters-male-cns-v1.0.feather",
    "weights": "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
}


class ManifestValidationError(ValueError):
    """Raised when the local MaleCNS input cannot satisfy its manifest."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"MaleCNS manifest is unreadable: {manifest_path}") from exc
    if not isinstance(manifest, dict):
        raise ManifestValidationError("MaleCNS manifest must be a JSON object")
    if manifest.get("dataset") != "MaleCNS" or manifest.get("version") != MALECNS_VERSION:
        raise ManifestValidationError("MaleCNS manifest has an unsupported dataset version")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestValidationError("MaleCNS manifest must contain a non-empty files list")
    names = [entry.get("filename") for entry in files if isinstance(entry, dict)]
    if len(names) != len(files) or len(names) != len(set(names)):
        raise ManifestValidationError("MaleCNS manifest contains duplicate or malformed filenames")
    return manifest


def _file_spec_by_role(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = {entry["filename"]: entry for entry in manifest["files"]}
    result: dict[str, dict[str, Any]] = {}
    for role, pattern in ROLE_GLOBS.items():
        matches = [entry for name, entry in files.items() if Path(name).match(pattern)]
        if len(matches) != 1:
            raise ManifestValidationError(
                f"MaleCNS manifest must define exactly one {role} file matching {pattern}"
            )
        if matches[0]["filename"] != EXPECTED_FILENAMES[role]:
            raise ManifestValidationError(
                f"wrong MaleCNS version in manifest for {role}: {matches[0]['filename']}"
            )
        result[role] = matches[0]
    return result


def _candidate_paths(raw_dir: Path, pattern: str) -> list[Path]:
    return sorted(path for path in raw_dir.glob(pattern) if path.is_file())


def _check_schema(path: Path, required_columns: list[str]) -> list[str]:
    try:
        schema = feather.read_table(path, columns=[]).schema
    except Exception as exc:  # pyarrow raises several concrete invalid-file errors
        raise ManifestValidationError(f"MaleCNS Feather file is corrupt or unreadable: {path.name}") from exc
    missing = [column for column in required_columns if column not in schema.names]
    if missing:
        raise ManifestValidationError(
            f"MaleCNS schema missing required columns in {path.name}: {', '.join(missing)}"
        )
    return list(schema.names)


def validate_malecns(raw_dir: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate exact files, bytes, hashes, schemas and row counts from a manifest."""
    manifest = load_manifest(manifest_path)
    specs = _file_spec_by_role(manifest)
    raw_dir = raw_dir.resolve()
    if not raw_dir.exists():
        raise ManifestValidationError(f"MaleCNS raw directory is missing: {raw_dir}")

    validated_files: list[dict[str, Any]] = []
    for role, spec in specs.items():
        expected_name = spec["filename"]
        candidates = _candidate_paths(raw_dir, ROLE_GLOBS[role])
        if len(candidates) != 1:
            names = ", ".join(path.name for path in candidates) or "none"
            raise ManifestValidationError(
                f"expected exactly one {role} Feather file matching {ROLE_GLOBS[role]}; found {names}"
            )
        path = candidates[0]
        if path.name != expected_name:
            raise ManifestValidationError(
                f"wrong MaleCNS version for {role}: found {path.name}, expected {expected_name}"
            )
        expected_size = spec.get("size_bytes")
        actual_size = path.stat().st_size
        if not isinstance(expected_size, int) or actual_size != expected_size:
            raise ManifestValidationError(
                f"MaleCNS size mismatch for {path.name}: expected {expected_size}, got {actual_size}"
            )
        expected_hash = spec.get("sha256")
        actual_hash = sha256_file(path)
        if not isinstance(expected_hash, str) or actual_hash != expected_hash:
            raise ManifestValidationError(
                f"MaleCNS SHA256 mismatch for {path.name}: expected {expected_hash}, got {actual_hash}"
            )
        columns = spec.get("required_columns")
        if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
            raise ManifestValidationError(f"manifest required_columns is malformed for {path.name}")
        schema_names = _check_schema(path, columns)
        expected_rows = spec.get("rows")
        try:
            actual_rows = feather.read_table(path, columns=[]).num_rows
        except Exception as exc:
            raise ManifestValidationError(f"MaleCNS row count could not be read for {path.name}") from exc
        if isinstance(expected_rows, int) and actual_rows != expected_rows:
            raise ManifestValidationError(
                f"MaleCNS row count mismatch for {path.name}: expected {expected_rows}, got {actual_rows}"
            )
        validated_files.append({
            "role": role,
            "filename": expected_name,
            "bytes": actual_size,
            "sha256": actual_hash,
            "rows": actual_rows,
            "schema": schema_names,
        })

    return {
        "dataset": manifest["dataset"],
        "version": manifest["version"],
        "manifest": str(manifest_path),
        "raw_dir": str(raw_dir),
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "files": validated_files,
    }
