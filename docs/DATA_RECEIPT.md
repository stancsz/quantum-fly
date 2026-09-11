# MaleCNS v1.0 数据接收凭证

本仓库只保存官方 MaleCNS v1.0 的三个 Feather 文件。原始文件位于 gitignored 的 `data/malecns-v1.0/raw/`，不会进入 Git。下载时间为 2026-09-11，时区 America/Denver。来源为 [Janelia 官方下载页](https://male-cns.janelia.org/download/)，没有使用第三方镜像或重打包模型。

## 文件与校验

| 文件 | 官方对象长度 | 本地字节数 | Google Storage ETag | 本地 SHA256 |
|---|---:|---:|---|---|
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 14,483,314 | 14,483,314 | `50a7718770c57220f160ba4f431ab89e` | `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2` |
| `body-neurotransmitters-male-cns-v1.0.feather` | 43,282,834 | 43,282,834 | `3d842b12fe5c49eefade528d7dd24a1f` | `95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621` |
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1,051,241,946 | 1,051,241,946 | `f30e9dcca25cfd021bf1e7b3d975599e` | `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1` |

## 官方 URL

- `https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather`
- `https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-neurotransmitters-male-cns-v1.0.feather`
- `https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/connectome-weights-male-cns-v1.0-minconf-0.5.feather`

## Verified Feather contents

- `body-annotations...`: 211,577 rows. Includes `bodyId`, neuron type/class fields, side and status fields, and other curated annotations. It is an annotation table, not a claim that every row is a unique biological neuron across every interpretation.
- `body-neurotransmitters...`: 1,835,518 rows. Includes `body`, `cell_type`, prediction counts, confidence, predicted neurotransmitter and consensus fields.
- `connectome-weights...`: 151,856,684 rows with `body_pre: int64`, `body_post: int64`, `weight: int64`.

The official page describes the weights as the full segment-to-segment connection graph, excluding segments with no synapses, with the published `minconf-0.5` threshold. These are anatomy-derived contact-count weights, not trained model weights, quantum weights or trading weights. Do not equate the weight-row count with the annotation-row count or neuron count.

The downloaded source is licensed CC-BY according to the official page. Keep that data attribution separate from this repository's software license, which is still not selected. The official page also lists body-stats, synapse points, synaptic partners and per-synapse neurotransmitter tables; they were intentionally not downloaded because they are not needed for this current scope.

The first local runnable integration uses a deterministic bounded selection of 4,096 sorted annotated segment IDs and scans the first 10,000,000 rows of the official weight table. This is an execution boundary for the smoke test, not a claim about the full graph. The complete downloaded file remains available for a later profiled pass.

On 2026-09-11, `python -m scripts.scan_full_connectome --output outputs/full-connectome-scan.json` streamed the complete downloaded weight file in 2,318 bounded batches. It scanned 151,856,684 rows, found 0 invalid endpoint rows, and completed in 1.311 seconds. The receipt recorded a 1,242,943,488-byte peak Windows process working set and a 1,248,602-byte Python `tracemalloc` peak. This validates full-file scanning only. It deliberately does not retain a whole graph, so it is not evidence that a 211,577-node executable graph fits the local resource budget.

## Verification method

Object metadata was read from the official Google Storage URLs with `Content-Length`, `ETag` and `Last-Modified`. Files were downloaded with resumable `.partial` paths and renamed only after curl succeeded. SHA256 was computed locally. Feather schemas and row counts were inspected with PyArrow 25.0.1. No simulation, graph filtering, market integration or biological-dynamics claim was made.
