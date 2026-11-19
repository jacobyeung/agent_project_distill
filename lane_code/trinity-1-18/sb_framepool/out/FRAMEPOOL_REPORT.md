Training-source rows on the target captures: sealed-VQA slices 919; pool distance 115, room 67, route planning 92; v7 0. Production step-544/R1 coverage is partial.

The positive counts are 1,193 records in archived metadata samples across 125 captures. They establish source-row overlap; optimizer consumption by step-544 or R1 is MISSING.
The archive labels many sealed rows “benchmark_trained_diagnostic” and disables benchmark score nomination. These flags do not prove which checkpoint consumed them.
An evaluation-only explanation is not supported. A clean benchmark claim requires the missing production membership evidence.

`CAPTURES.tsv` and `FRAMEPOOL.json` list every token, native key, dataset, canonical capture, physical room, benchmark, direct/sibling reason, list membership, and per-stream count.
`CAPTURE_MEMBERSHIPS.tsv` reproduces 148 group memberships: 126 STI-Bench/ReSTI + 20 MindCube + 2 venue-381879 captures. There are 146 distinct captures.
The overlap is ScanNet scene0122_00 (d1/vba9dd8cbb0da) and scene0122_01 (d1/vda951d1116f5), each in both STI-Bench/ReSTI and MindCube.
The venue captures are native d3/41159526 → frame token d3/vc6a4b809b958 and d3/41159521 → d3/vf3e2ed14c783. Both are siblings of benchmark capture 41159525.
BENCH v2 contains all 146 targets. Its 511 are physical groups, not captures: it contains 1,212 scene entries. No target requires a missing BENCH entry.
Tokens reproduce `v + sha256("rung1 scene " + native_dataset + "/" + scene)[:12]`; ScanNet++ uses `scannetppv2` in that string.
`r2_policy.py` requires checked banks to include VSI-Bench, VSTI, and ReVSI. STI-Bench/ReSTI and MindCube are outside that scope; BENCH v2 is broader.
The policy permits lineage overlap at venue 381879; this is an exception, not a finding that training is clean.

| Reachable stream or sample | Target rows / supplied rows | Coverage |
|---|---:|---|
| v7 VQA | 0 / 204,413 | Complete supplied store |
| rows_a2 VQA v2/v3/v4/v5/v6 | 0 / 152,123; 152,123; 163,175; 194,597; 195,471 | Complete supplied stores |
| Other local rows_r1/rows_r2 stores and A0 slices | 0 | Per-file counts and copies in JSON; supplied-file coverage only |
| Five b12 archived SQLite stores | 0 / 10,593; 3,132; 31,522; 31,476; 31,422 | Complete supplied stores |
| pool_abs_distance | 115 / 2000 | Partial; full family 13001 rows |
| pool_room | 67 / 672 | Complete family |
| pool_route_planning | 92 / 2000 | Partial; full family 10458 rows |
| sealed_vqa_box_3d | 219 / 2000 | Partial; full family 5135 rows |
| sealed_vqa_obj_appearance_order | 167 / 2000 | Partial; full family 17672 rows |
| sealed_vqa_object_counting | 56 / 2000 | Partial; full family 10787 rows |
| sealed_vqa_object_rel_direction_easy | 87 / 2000 | Partial; full family 14780 rows |
| sealed_vqa_object_rel_direction_hard | 93 / 2000 | Partial; full family 25044 rows |
| sealed_vqa_object_rel_direction_medium | 108 / 2000 | Partial; full family 18327 rows |
| sealed_vqa_object_rel_distance | 95 / 2000 | Partial; full family 24737 rows |
| sealed_vqa_room_size_estimation | 94 / 387 | Complete family |

The positive samples are in `/scratch/jjyeung/n30_mirror/old_lanes_3_30/old_lanes_3_30_b.tar::tree_rebuild/work/rows_slices/slices_v3/`; `COUNTS.json` binds their hashes and full-family scene lists.
Full-family per-capture row counts are MISSING where the supplied sample is smaller than its family. A sample zero is not a full-family zero. JSON records both scene-list membership and observed counts.
No supplied sample hits either venue-381879 capture; the 15 ARKit sample hits belong to four MindCube captures. Missing production pose/routing rows prevent a venue-level clean verdict.

| Production receipt | Pointing / pose / routing / VQA rows declared | Row-level coverage |
|---|---:|---|
| step-544 kit, run 469ddece | 20,239 / 194,987 / 57,136 / 114,904 | Partial; production databases MISSING |
| head preparation, run 359fcc3c | 20,239 / 194,987 / 47,732 / 152,123 | Partial; production databases MISSING |
| R1/P staged run 6ed2c7aa | 20,239 / 194,987 / 47,898 / 185,933 | Partial; production databases MISSING |
| R1 staged run 673bc60f | 20,239 / 194,987 / 47,898 / 203,812 | Partial; production databases MISSING |

JSON gives each missing database’s exact original path and SHA256 from its receipt, plus every surviving index/order location. Pose uses source stores `f02f16ad/s/a2v3/rows.sqlite` and `f02f16ad/s/a3v2/rows.sqlite`; both are MISSING.
Surviving scene indices are integers; pose orders are source/index pairs. They do not identify captures without the pinned source databases. Equal row totals in other stores do not establish identity.
P’s H1 routing/VQA index pins are also MISSING. W’s real SQLite files lie in test/proof trees; its JSON stubs named `.sqlite` contain no production rows.
All 13 pool source payloads are MISSING; 12 selected-index files survive (SCENE_room_sppK is deferred). `pool_exclusion_*.tsv` and `remove_*.jsonl` are exclusion instructions, not training membership proofs.
The reachable archive/W metadata, h1_headsft, b08_headrows, r1_ops6, and cont_ops configurations are indexed by hash in the JSON evidence; receipt claims are kept separate from observed counts.

The frame universe contains 290,880 frames in 4,697 captures. Frame-map fields are only d, s, i, path, sha256, w, h; the plan gives source videos/URLs, needed indices, and totals. Neither identifies train/evaluation use.
The scan found no exact target-capture or frame-hash matches in 150 candidate item files. Official VSI/ReVSI cohorts and R0/DEV item sets were checked; unresolved anonymous scene labels remain partial.
Official STI-Bench/ReSTI and MindCube item banks with exact frame references are MISSING from the named reachable inputs. Benchmark room membership alone cannot assign these frames to an evaluation set.
B06 dense plans reference target clips but provide no per-stream row join; they are training-frame demand metadata, not evidence of evaluation-only staging.

Commands: `/usr/bin/python3 work/captures.py` produces capture/frame/list counts; `work/scan_rows.py` and `work/scan_archive_stores.py` produce store counts.
`/usr/bin/python3 work/scan_metadata_rows.py` produces slice counts; `work/verify_hits.py` rechecks all 1,193 positives directly against archive bytes and exact target tokens.
`/usr/bin/python3 work/eval_join.py` produces item/frame joins; `work/build_report.py` produces family, pool, receipt, and report counts. Run each script with `/usr/bin/python3` from this workspace.
Input SHA256 values, source-member locations, missing pins, coverage, and commands are recorded in `FRAMEPOOL.json`. The metadata reader detects gzip archives by content before using their members.
The reviewer’s frame-universe script/capture list is MISSING under the named `sb_evrev/notes`; the surviving `recompute_recovery.py` audits recovery rows. The capture intersection here is independently reproduced.
The standalone sb_alias2 per-row map is MISSING in its out directory/archive; v7 was scanned using each row plus TIERED_ALIAS_MAP.json and checked against ROOM_AUDIT_TIERED.json.
`sb_framepool.tar.sha256` records the package hash. The package contains the report, JSON, capture tables, scripts, positive-row evidence, and summarized scans.
