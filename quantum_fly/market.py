"""Small cached public market input loader with auditable provenance."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import csv
import json
from urllib.parse import parse_qs, urlparse
import urllib.request
import numpy as np


URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31"
CACHE_METADATA_SUFFIX = ".meta.json"
CACHE_MAX_AGE_DAYS = 365


class CacheProvenanceError(ValueError):
    """Raised when a cached response cannot be tied to the requested source."""


def _metadata_path(cache: Path) -> Path:
    return cache.with_name(cache.name + CACHE_METADATA_SUFFIX)


def _requested_range(url: str) -> dict[str, str | None]:
    query = parse_qs(urlparse(url).query)
    return {
        "start": (query.get("cosd") or [None])[0],
        "end": (query.get("coed") or [None])[0],
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_metadata(cache: Path) -> dict:
    metadata_path = _metadata_path(cache)
    if not metadata_path.exists():
        raise CacheProvenanceError(
            f"cache metadata is missing for {cache.name}; remove the cache or refresh it"
        )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CacheProvenanceError(f"cache metadata is unreadable: {metadata_path.name}") from exc
    if not isinstance(metadata, dict):
        raise CacheProvenanceError("cache metadata must be a JSON object")
    return metadata


def _write_metadata(cache: Path, metadata: dict) -> None:
    metadata_path = _metadata_path(cache)
    temporary = metadata_path.with_name(metadata_path.name + ".partial")
    temporary.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(metadata_path)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _parse_rows(raw: bytes) -> tuple[list[dict[str, str]], np.ndarray]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CacheProvenanceError("FRED cache is not valid UTF-8") from exc
    reader = csv.DictReader(text.splitlines())
    date_columns = {"DATE", "observation_date"}
    if not reader.fieldnames or "SP500" not in reader.fieldnames or not date_columns.intersection(reader.fieldnames):
        found = ", ".join(reader.fieldnames or ()) or "none"
        raise CacheProvenanceError(f"FRED cache is missing required date and SP500 columns (found: {found})")
    rows = list(reader)
    try:
        close = np.asarray(
            [float(row["SP500"]) for row in rows if row["SP500"] not in ("", ".")],
            dtype=float,
        )
    except (TypeError, ValueError) as exc:
        raise CacheProvenanceError("FRED cache contains a non-numeric SP500 value") from exc
    if len(close) < 30 or not np.all(np.isfinite(close)):
        raise CacheProvenanceError("market source did not provide enough finite closes")
    return rows, close


def _validate_cached_bytes(
    cache: Path,
    url: str,
    *,
    max_age_days: int | None = CACHE_MAX_AGE_DAYS,
) -> tuple[list[dict[str, str]], np.ndarray, dict]:
    metadata = _read_metadata(cache)
    requested_range = _requested_range(url)
    if metadata.get("url") != url:
        raise CacheProvenanceError(
            f"cache URL mismatch: metadata has {metadata.get('url')!r}, request is {url!r}"
        )
    if metadata.get("requested_date_range") != requested_range:
        raise CacheProvenanceError("cache requested date range does not match the requested URL")
    raw = cache.read_bytes()
    digest = _sha256(raw)
    if metadata.get("sha256") != digest:
        raise CacheProvenanceError(
            f"cache content SHA256 mismatch: metadata has {metadata.get('sha256')!r}, computed {digest}"
        )
    first_download = metadata.get("first_download_utc")
    if not first_download:
        raise CacheProvenanceError("cache metadata is missing first_download_utc")
    if max_age_days is not None:
        try:
            age_seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(first_download)).total_seconds()
        except (TypeError, ValueError) as exc:
            raise CacheProvenanceError("cache first_download_utc is not a valid timestamp") from exc
        if age_seconds < 0 or age_seconds > max_age_days * 86400:
            raise CacheProvenanceError(
                f"cache is stale: first download is older than {max_age_days} days"
            )
    rows, close = _parse_rows(raw)
    metadata["validated_utc"] = _utc_now()
    _write_metadata(cache, metadata)
    return rows, close, metadata


def _features(close: np.ndarray) -> np.ndarray:
    returns = close[1:] / close[:-1] - 1.0
    values = np.array([
        returns[-1],
        np.mean(returns[-5:]),
        np.std(returns[-20:]),
        (close[-1] / close[-20]) - 1.0,
    ], dtype=float)
    return np.clip(values, -1.0, 1.0)


def load_or_download(
    cache: Path,
    url: str = URL,
    *,
    max_age_days: int | None = CACHE_MAX_AGE_DAYS,
) -> tuple[np.ndarray, dict]:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        temporary = cache.with_name(cache.name + ".partial")
        temporary.write_bytes(raw)
        temporary.replace(cache)
        now = _utc_now()
        _write_metadata(cache, {
            "schema_version": 1,
            "url": url,
            "requested_date_range": _requested_range(url),
            "sha256": _sha256(raw),
            "first_download_utc": now,
            "validated_utc": None,
        })
    rows, close, metadata = _validate_cached_bytes(cache, url, max_age_days=max_age_days)
    features = _features(close)
    provenance = {
        **metadata,
        "cache_path": str(cache),
        "metadata_path": str(_metadata_path(cache)),
        "rows": len(rows),
        "symbol": "S&P 500 index proxy for stock/ETF research smoke test",
        "chronological": True,
    }
    return np.clip(features, -1.0, 1.0), provenance


def load_history(
    cache: Path,
    url: str = URL,
    *,
    max_age_days: int | None = CACHE_MAX_AGE_DAYS,
) -> tuple[np.ndarray, dict]:
    """Return chronological closes and provenance for offline backtesting."""
    if not cache.exists():
        load_or_download(cache, url, max_age_days=max_age_days)
    rows, values, metadata = _validate_cached_bytes(cache, url, max_age_days=max_age_days)
    dates = []
    for row in rows:
        value = row.get("SP500", "")
        if value not in ("", "."):
            dates.append(row.get("DATE", row.get("observation_date", "")))
    return values, {
        **metadata,
        "cache_path": str(cache),
        "metadata_path": str(_metadata_path(cache)),
        "rows_raw": len(rows),
        "rows_valid_close": len(values),
        "first_date": dates[0],
        "last_date": dates[-1],
        "symbol": "S&P 500 index proxy for stock/ETF research smoke test",
    }


def causal_features(closes: np.ndarray, t: int) -> np.ndarray:
    """Create four features using closes through t only."""
    if t < 20 or t >= len(closes):
        raise ValueError("t must have a 20-close history and be in range")
    returns = closes[1 : t + 1] / closes[:t] - 1.0
    values = np.array([returns[-1], np.mean(returns[-5:]), np.std(returns[-20:]), closes[t] / closes[t - 20] - 1.0])
    return np.clip(values, -1.0, 1.0)
