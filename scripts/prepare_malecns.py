"""Download missing official MaleCNS files and validate the versioned manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantum_fly.data_manifest import (  # noqa: E402
    ManifestValidationError,
    load_manifest,
    validate_malecns,
)


def _download_missing(raw_dir: Path, manifest: dict) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for spec in manifest["files"]:
        destination = raw_dir / spec["filename"]
        if destination.exists():
            continue
        partial = destination.with_name(destination.name + ".partial")
        with urllib.request.urlopen(spec["url"], timeout=120) as response, partial.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        partial.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "malecns-v1.0" / "raw")
    parser.add_argument("--manifest", type=Path, default=ROOT / "configs" / "malecns-v1.0-manifest.json")
    parser.add_argument("--download", action="store_true", help="download only missing official files")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.download:
            _download_missing(args.raw_dir, manifest)
        receipt = validate_malecns(args.raw_dir, args.manifest)
    except (ManifestValidationError, OSError, ValueError) as exc:
        print(f"MaleCNS preparation failed: {exc}")
        return 2
    print(f"MaleCNS {receipt['version']} validated: {len(receipt['files'])} files")
    for item in receipt["files"]:
        print(f"- {item['filename']}: {item['bytes']} bytes, {item['rows']} rows, {item['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
