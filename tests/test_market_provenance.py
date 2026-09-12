import json
from datetime import datetime, timedelta, timezone

import pytest

from quantum_fly.market import CacheProvenanceError, load_history, load_or_download


def _csv(columns=("DATE", "SP500"), rows=35) -> bytes:
    lines = [",".join(columns)]
    for index in range(rows):
        values = {"DATE": f"2024-01-{index + 1:02d}", "observation_date": f"2024-01-{index + 1:02d}", "SP500": str(100.0 + index)}
        lines.append(",".join(values.get(column, "x") for column in columns))
    return ("\n".join(lines) + "\n").encode("utf-8")


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, *_args):
        return self.payload


def test_download_records_first_download_and_validation_times(monkeypatch, tmp_path):
    url = "https://example.test/fred.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31"
    payload = _csv()
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response(payload))
    features, provenance = load_or_download(tmp_path / "sp500.csv", url, max_age_days=None)
    assert features.shape == (4,)
    assert provenance["url"] == url
    assert provenance["requested_date_range"] == {"start": "2024-01-01", "end": "2024-12-31"}
    assert provenance["first_download_utc"]
    assert provenance["validated_utc"]
    assert provenance["first_download_utc"] != provenance["validated_utc"]


def test_url_mismatch_is_rejected_offline(tmp_path):
    cache = tmp_path / "sp500.csv"
    cache.write_bytes(_csv())
    (tmp_path / "sp500.csv.meta.json").write_text(json.dumps({
        "url": "https://example.test/old.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31",
        "requested_date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "sha256": "unused",
        "first_download_utc": datetime.now(timezone.utc).isoformat(),
    }), encoding="utf-8")
    with pytest.raises(CacheProvenanceError, match="URL mismatch"):
        load_history(cache, "https://example.test/new.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31", max_age_days=None)


def test_stale_and_corrupt_cache_are_rejected_without_network(tmp_path):
    cache = tmp_path / "sp500.csv"
    payload = _csv()
    cache.write_bytes(payload)
    import hashlib

    metadata = {
        "url": "https://example.test/fred.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31",
        "requested_date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first_download_utc": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
    }
    (tmp_path / "sp500.csv.meta.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(CacheProvenanceError, match="stale"):
        load_history(cache, metadata["url"], max_age_days=1)
    metadata["first_download_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["sha256"] = "not-the-file"
    (tmp_path / "sp500.csv.meta.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(CacheProvenanceError, match="SHA256 mismatch"):
        load_history(cache, metadata["url"], max_age_days=30)


def test_missing_columns_are_rejected_offline(tmp_path):
    cache = tmp_path / "sp500.csv"
    payload = _csv(columns=("DATE", "OTHER"))
    cache.write_bytes(payload)
    import hashlib

    metadata = {
        "url": "https://example.test/fred.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31",
        "requested_date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first_download_utc": datetime.now(timezone.utc).isoformat(),
    }
    (tmp_path / "sp500.csv.meta.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(CacheProvenanceError, match="missing required"):
        load_history(cache, metadata["url"], max_age_days=None)


def test_current_fred_observation_date_header_is_accepted(monkeypatch, tmp_path):
    url = "https://example.test/fred.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31"
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response(_csv(columns=("observation_date", "SP500"))))
    _, provenance = load_history(tmp_path / "sp500.csv", url, max_age_days=None)
    assert provenance["first_date"].startswith("2024-01-")
