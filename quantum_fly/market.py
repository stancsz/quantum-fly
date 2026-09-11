"""Small cached public market input loader."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import csv
import urllib.request
import numpy as np


URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2024-01-01&coed=2024-12-31"


def load_or_download(cache: Path, url: str = URL) -> tuple[np.ndarray, dict]:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        with urllib.request.urlopen(url, timeout=30) as response:
            cache.write_bytes(response.read())
    raw = cache.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    close = np.asarray(
        [float(row["SP500"]) for row in rows if row["SP500"] not in ("", ".")],
        dtype=float,
    )
    if len(close) < 30 or not np.all(np.isfinite(close)):
        raise ValueError("market source did not provide enough finite closes")
    returns = close[1:] / close[:-1] - 1.0
    features = np.array([
        returns[-1],
        np.mean(returns[-5:]),
        np.std(returns[-20:]),
        (close[-1] / close[-20]) - 1.0,
    ], dtype=float)
    provenance = {
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "symbol": "S&P 500 index proxy for stock/ETF research smoke test",
        "chronological": True,
    }
    return np.clip(features, -1.0, 1.0), provenance


def load_history(cache: Path, url: str = URL) -> tuple[np.ndarray, dict]:
    """Return chronological closes and provenance for offline backtesting."""
    if not cache.exists():
        load_or_download(cache, url)
    raw = cache.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    dates = []
    closes = []
    for row in rows:
        value = row.get("SP500", "")
        if value not in ("", "."):
            dates.append(row.get("DATE", row.get("observation_date", "")))
            closes.append(float(value))
    values = np.asarray(closes, dtype=float)
    if len(values) < 30 or not np.all(np.isfinite(values)):
        raise ValueError("market history did not provide enough finite closes")
    return values, {
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
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
