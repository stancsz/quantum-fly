# Reproducible local data preparation

The repository keeps the MaleCNS bytes out of Git. The versioned contract is
[`configs/malecns-v1.0-manifest.json`](../configs/malecns-v1.0-manifest.json),
which records the official URL, expected byte length, SHA256, row count and
required Feather columns for each input.

Validate an existing local download without running an experiment:

```text
python -m scripts.prepare_malecns
```

Download only missing files from the official URLs, then validate the result:

```text
python -m scripts.prepare_malecns --download
```

The preparation command does not replace an existing file. A missing file,
duplicate filename match, wrong version, changed size or hash, corrupt Feather
payload, missing required column, or row-count mismatch fails with an explicit
error. The download uses a `.partial` path and renames it only after the
response completes. The source remains subject to the upstream CC-BY terms;
this repository does not redistribute the data.

FRED CSV caches have a sibling `.meta.json` sidecar. It binds the bytes to the
exact request URL and `cosd`/`coed` range, SHA256, first download timestamp,
and latest validation timestamp. A cache without metadata, a URL/range
mismatch, stale metadata, corrupted bytes, or missing `DATE`/`SP500` columns
fails offline. Delete an old cache before downloading it again, or call the
loader with a separate cache path; the loader never relabels a read as a new
download.
