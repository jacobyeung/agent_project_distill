# Locate accuracy on existing direct reads

Each rate uses citations of exact, unique raster instances visible on at least one anchor at >=1%. Intervals use 10,000 room-cluster resamples within each read (seed 20261120); the two exports are reported separately. Frames outside 1–32 and fractional frames fail. No synonym substitution is applied.

| Group | Step 400 | Step 600 |
|---|---|---|
| All numeric citations | 12/50: 24.0% [8.9, 37.0] | 10/33: 30.3% [7.4, 51.5] |
| arkitscenes | 4/15: 26.7% [7.1, 43.8] | 3/12: 25.0% [9.1, 45.5] |
| scannet | 0/3: 0.0% [0.0, 0.0] | 0/1: 0.0% [0.0, 0.0] |
| scannetppv2 | 8/32: 25.0% [0.0, 42.5] | 7/20: 35.0% [0.0, 64.0] |
| object_counting | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_easy | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_hard | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_medium | not computable (0 citations) | not computable (0 citations) |
| object_rel_distance | 7/29: 24.1% [0.0, 45.0] | 6/17: 35.3% [0.0, 70.6] |
| object_size_estimation | 5/21: 23.8% [6.2, 37.5] | 4/16: 25.0% [7.7, 43.8] |
| relative_count | not computable (0 citations) | not computable (0 citations) |
| relative_size_object | not computable (0 citations) | not computable (0 citations) |
| route_planning | not computable (0 citations) | not computable (0 citations) |

All nonempty primary groups fall below the 90% point bar. A zero-width bootstrap interval from a tiny stratum is not evidence of population certainty. Relative size has numeric claims but none with an exact unique local instance visible at 1%; other zero-citation types have no numeric Locate claim. Absolute distance is absent from these direct-read manifests.

| Sensitivity | Step 400 | Step 600 |
|---|---|---|
| Include unambiguous worded anchors | 13/51: 25.5% [10.8, 38.2] | 11/35: 31.4% [10.0, 52.0] |
| Numeric, valid 1–32 indices only | 12/36: 33.3% [13.0, 51.2] | 10/27: 37.0% [10.0, 60.6] |
| Any one instance of the exact label | 13/51: 25.5% [11.1, 38.5] | 10/33: 30.3% [7.4, 51.5] |

The worded-anchor sensitivity accepts first/initial, last, and explicit ordinals. It adds 24 claims across the reads; 13 spatial or time descriptions do not specify a unique anchor. It does not reinterpret “frame 70” or “frame 44.9” as timestamps. The numeric contract is the preregistered primary analysis; the worded sensitivity is exploratory.

| Coverage | Step 400 | Step 600 |
|---|---|---|
| Development items | 1339 | 1339 |
| Items with local GT and exact 32-anchor mapping | 485 | 485 |
| Items with numeric frame citations | 144 | 92 |
| Numeric operand citations | 150 | 93 |
| Citations missing a raster | 82 | 47 |
| Citations without a literal GT label | 5 | 4 |
| Citations with multiple same-label instances | 1 | 0 |
| Resolved citations never >=1% on any anchor | 12 | 9 |
| All invalid numeric citations (including missing GT) | 48 | 30 |
| Unparsed numeric-frame lines | 0 | 0 |

There are 38 staged GT captures (23 ARKitScenes, four ScanNet, 11 ScanNet++). Each direct read covers 139 captures; 485/1,339 items map to staged rasters. The funnel’s “38 of 60” denominator belongs to its separate distance slice and is not reused here. For the primary conditional citations there are 22 rooms at step 400 and 17 at step 600. Both reads contain an additional 1,781 anonymized R0-dev items; their GT binding is unavailable, so no R0 visibility rate is claimed. The B2048, B4096 and full traces are identical on all 1,339 dev-S1 items of each read; they are not pooled.

These exports belong to ended run 6ed2c7aa (step 400 accepted direct decision read, step 600 diagnostic forecast), not vehicle N. This result does not certify or reject N’s complete routed gate. The kill test, on-target noninferiority, gap MRA, 95% preceding-Locate coverage and R0 confirmation remain uncomputed. No grounding label is authorized for training by this diagnostic.

Validation: seven focused tests pass. An independent implementation directly counted raw raster pixels for all 105 resolved numeric claims and reproduced every visibility decision. Every numeric-frame line in the two development reads was parsed. All 485 covered items per checkpoint have an exact source_frame_indices match. The raster label IDs are used directly; background is -1.

Artifacts: anchor_analysis.py, validate_locate.py, test_anchor_analysis.py, locate_summary.json (including dataset × type), locate_claims.jsonl, locate_item_audit.json, locate_validation.json, raster_visibility.json, tests.log, validation.log.
