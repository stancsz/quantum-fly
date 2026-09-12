import json

import pyarrow as pa
import pyarrow.feather as feather
import pytest

from quantum_fly.data_manifest import ManifestValidationError, sha256_file, validate_malecns


def _make_dataset(tmp_path, *, names=None):
    names = names or {
        "annotations": "body-annotations-male-cns-v1.0-minconf-0.5.feather",
        "neurotransmitters": "body-neurotransmitters-male-cns-v1.0.feather",
        "weights": "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
    }
    tables = {
        "annotations": pa.table({"bodyId": [1, 2]}),
        "neurotransmitters": pa.table({"body": [1, 2], "consensus_nt": ["gaba", ""]}),
        "weights": pa.table({"body_pre": [1], "body_post": [2], "weight": [3]}),
    }
    for role, filename in names.items():
        feather.write_feather(tables[role], tmp_path / filename)
    entries = []
    required = {
        "annotations": ["bodyId"],
        "neurotransmitters": ["body", "consensus_nt"],
        "weights": ["body_pre", "body_post", "weight"],
    }
    for role, filename in names.items():
        path = tmp_path / filename
        entries.append({
            "filename": filename,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "rows": feather.read_table(path, columns=[]).num_rows,
            "required_columns": required[role],
        })
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"dataset": "MaleCNS", "version": "v1.0", "files": entries}), encoding="utf-8")
    return manifest


def test_manifest_validates_exact_files_hashes_and_schema(tmp_path):
    manifest = _make_dataset(tmp_path)
    receipt = validate_malecns(tmp_path, manifest)
    assert receipt["version"] == "v1.0"
    assert {item["role"] for item in receipt["files"]} == {"annotations", "neurotransmitters", "weights"}


def test_manifest_rejects_corrupt_file_and_duplicate_match(tmp_path):
    manifest = _make_dataset(tmp_path)
    (tmp_path / "body-annotations-male-cns-v1.0-minconf-0.5.feather").write_bytes(b"broken")
    with pytest.raises(ManifestValidationError, match="(size|SHA256) mismatch"):
        validate_malecns(tmp_path, manifest)

    tmp_path = tmp_path / "duplicate"
    tmp_path.mkdir()
    _make_dataset(tmp_path)
    (tmp_path / "body-annotations-extra.feather").write_bytes(b"duplicate")
    with pytest.raises(ManifestValidationError, match="exactly one annotations"):
        validate_malecns(tmp_path, tmp_path / "manifest.json")


def test_manifest_rejects_wrong_version_filename(tmp_path):
    manifest = _make_dataset(tmp_path, names={
        "annotations": "body-annotations-male-cns-v1.1-minconf-0.5.feather",
        "neurotransmitters": "body-neurotransmitters-male-cns-v1.0.feather",
        "weights": "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
    })
    with pytest.raises(ManifestValidationError, match="wrong MaleCNS version"):
        validate_malecns(tmp_path, manifest)
