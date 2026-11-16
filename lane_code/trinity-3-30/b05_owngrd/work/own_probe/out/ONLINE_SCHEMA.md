# O5 inputs for E-A

E-A accepts O5 agreement rows through `--labels`. It accepts scored candidate groups for T1 fusion through `--fusion-rows`. These inputs must come from the training split of `b2_manifest.jsonl`. Tuning labels serve evaluation only. Missing inputs leave T2, T3 or R1+ pending.

## Agreement JSONL

Each row contains `dataset`, `scan`, canonical `scene`, `split: "train"`, zero-based `slot`, `name`, and `status`. Include the O1 `room` and `authority_sha256` for provenance. The reader validates the whole file before opening masks, then joins `(scene,slot)` against admitted training frames. It refuses rows from validation scenes even when a row claims `split=train`.

```json
{"dataset":"scannet","scan":"scene0400_01","scene":"scannet/scene0400_01","split":"train","slot":4,"name":"chair","status":"POS","joint_score":0.87,"mask_rle":{"size":[2,3],"counts":[1,3,2]}}
```

The example shows the schema only; it is not a training label. RLE uses uncompressed COCO counts in column-major order. Use the mask's actual dimensions. A POS requires `joint_score > 0.5` and a mask. Instead of inline RLE, `mask_ref` can identify either:

- An NPZ array: `path`, file `sha256`, `key` (default `mask`), and optional array `index`.
- A raw SAM payload: `path`, file `sha256`, `phrase`, zero-based `slot`, and `instance_index`.

ABSENT requires `presence < 0.2` and `gt_visible: false`. T3 uses POS and ABSENT; MISS and HARDNEG do not become absence labels. T2 uses POS only. Multiple POS masks for one frame/name are unioned. Both tasks select one name per frame by a seed-17 hash. T2 selects exactly 1,500 distinct eligible training frames and fails clearly if fewer exist. T3 selects up to 1,500 frames and requires both classes. Both run 1,500 optimizer steps, with batch size four and a global permutation each epoch (seed 17), identically for every arm and readout.

## Fusion JSONL

Each row represents one listwise candidate group and includes the same training admission fields, plus:

| Field | Shape / meaning |
|---|---|
| `features` | `[K,D]`, mask-pooled features from this arm, using `own_feats.pool` |
| `name_embedding` | `[4096]`, the frozen token-row mean from `NameEmbedder` |
| `sam_scores` | `[K]`, actual SAM joint scores in `[0,1]` |
| `positive` | `[K]` Boolean on-target labels; at least one true |
| `statuses` | Optional `[K]` O5 statuses |
| `confuser` | Optional `[K]` Booleans identifying confuser HARDNEG candidates |

Features must match the fitted arm, including A8's A2/A4 tap order. No artificial SAM score is assigned to GT regions. A candidate marked HARDNEG and confuser receives denominator weight 0.25; other candidates receive 1.0. T1's feature-only GT fit separately upweights confuser negatives by 4.0. These implementation settings are recorded in `FIT_CONFIG.json` and hashed in results.

Supply O5 outputs before running the dependent phase. If a feature-only T1 phase has already completed, use a new results directory for a fused T1 run; changing its input binding must not silently reuse the old marker. Existing feature shards remain reusable when code, encoder identity and extraction configuration match.

No O5 agreement file or arm-specific fusion file was supplied to this lane. This contract makes those dependencies explicit; the lane does not generate substitute labels.
