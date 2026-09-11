"""Explicit, read-only public-source research adapter."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import urllib.request


JANELIA_URL = "https://male-cns.janelia.org/download/"


def connectome_source_request(timeout: float = 15.0) -> dict:
    """Fetch only the official MaleCNS download page."""
    started = datetime.now(timezone.utc).isoformat()
    with urllib.request.urlopen(JANELIA_URL, timeout=timeout) as response:
        raw = response.read()
    text = raw.decode("utf-8", errors="replace")
    terms = ("connectome-weights", "body-annotations", "body-neurotransmitters", "CC-BY")
    evidence = [line.strip() for line in text.splitlines() if any(term in line for term in terms)]
    return {
        "url": JANELIA_URL,
        "retrieved_utc": started,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "evidence": evidence[:20],
        "scope": "official source page only, no arbitrary URL or command execution",
    }
