The records build is complete: nine slots remain MISSING, so no component record is issued. Both component phases and all three sealed official-bank gateway probes refuse. Five unchanged policy tests pass on CPU.

All counts below come from `bash work/run_python.sh work/stage2.py`. Slot decisions and the receipt graph come from `bash work/run_python.sh work/build_records.py`. Zero overlap describes only the named population; it does not close inherited ancestry.

| Slot | Status and gap | Membership or identity evidence; missing requirement |
|---|---|---|
| `init_m544` | MISSING — [gap](gaps/init_m544.json) | Prepared receipt 0664bb17 and four admitted streams; step-200 membership configuration and depth-parent preparation remain missing. |
| `heads_pose` | MISSING — [gap](gaps/heads_pose.json) | Step-544 admitted membership and pose order 3cb1ccf5 are recovered; inherited membership remains incomplete. |
| `heads_depth` | MISSING — [gap](gaps/heads_depth.json) | Step-544 membership and fd60ac2f depth identity are recovered; inherited membership remains incomplete. |
| `heads_frame_embeddings` | MISSING — [gap](gaps/heads_frame_embeddings.json) | Step-544 stream membership is recovered; the step-200 and depth-parent chain remains incomplete. |
| `depth_init_vc` | MISSING — [gap](gaps/depth_init_vc.json) | heads.json fd60ac2f pins the missing preparation receipt a60f3a9f; depth-parent overlap is UNKNOWN. |
| `data_rows_r2` | MISSING — [gap](gaps/data_rows_r2.json) | v7, n/z/u removals and three routing slices are audited; N lacks complete family exclusions and frame-host bindings. |
| `geometry_tower` | MISSING — [gap](gaps/geometry_tower.json) | Release, weights, config and runtime identity binding 025b4688 are present; the run-bound frozen optimizer inventory is missing. |
| `segmenter` | MISSING — [gap](gaps/segmenter.json) | Release and checkpoint identities are present; the frozen inventory and N cache/runtime binding are missing. |
| `heads_gf1_connector` | MISSING — [gap](gaps/heads_gf1_connector.json) | N sets geometry_connector=none. This gap awaits the NOT_PRESENT policy status; the tested policy does not accept it. |

There are no record SHA256 values because no record meets the evidence bar. Each gap carries input hashes. The registry copy is `out/kit/registry.json`; its original null bindings remain intact. `out/REGISTRY_PROVENANCE.json` binds the registry and all gaps.

| Population | Rows or entries | Resolved | Scenes / rooms | VSI-Bench / VSTI / ReVSI overlapping rows |
|---|---:|---:|---:|---|
| raw_pointing | 20,239 | 20,239 | 327 / 289 | 0 / 0 / 0 |
| raw_routing | 57,136 | 57,136 | 2,241 / 1,443 | 0 / 0 / 0 |
| raw_vqa | 140,963 | 140,963 | 2,280 / 1,486 | 0 / 0 / 0 |
| raw_a2v3 | 66,934 | 66,934 | 4,051 / 1,933 | 23 / 0 / 23 |
| raw_a3v2 | 203,520 | 203,520 | 2,544 / 1,030 | 0 / 0 / 0 |
| raw_r16 | 76,277 | 76,277 | 356 / 308 | 0 / 0 / 0 |
| m544_admitted_pointing | 20,239 | 20,239 | 327 / 289 | 0 / 0 / 0 |
| m544_admitted_routing | 57,136 | 57,136 | 2,241 / 1,443 | 0 / 0 / 0 |
| m544_admitted_vqa | 114,904 | 114,904 | 2,276 / 1,484 | 0 / 0 / 0 |
| m544_admitted_pose | 194,987 | 194,987 | 2,833 / 1,514 | 0 / 0 / 0 |
| m544_admitted_union | 387,266 | 387,266 | 4,213 / 2,175 | 0 / 0 / 0 |
| m544_frame_universe | 290,880 | 290,880 | 4,697 / 2,411 | 64 / 0 / 64 |
| readout_training_scenes | 4,065 | 4,065 | 4,065 / 1,940 | 2 / 0 / 2 |
| v7_raw | 204,413 | 204,413 | 2,966 / 1,659 | 0 / 0 / 0 |
| v7_minus_nzu | 183,318 | 183,318 | 2,816 / 1,608 | 0 / 0 / 0 |
| N_routing_absolute_distance | 8,315 | 8,315 | 1,690 / 1,125 | 0 / 0 / 0 |
| N_routing_recovery | 994 | 994 | 440 / 384 | 0 / 0 / 0 |
| N_routing_units | 8,577 | 8,577 | 1,770 / 1,171 | 0 / 0 / 0 |

All 6,258 distinct recovered tokens have verified native preimages. The mint is `v + sha256("rung1 scene " + native_dataset + "/" + scene)[:12]`; ScanNet++ uses `scannetppv2`. The audit remints the v7 alias map, native frame-plan names and EVAL_ROOMS candidates, and enumerates ScanNet labels and eight-digit ARKit IDs for unmatched tokens. `Rooms.room` normalises room identities. `out/TOKEN_INVERSION.json` records every mapping and its source method.
BENCH v2 is 3119aa4a. The audited banks contain VSI-Bench 707 captures / 288 rooms, VSTI 312 / 142, and ReVSI 852 / 381. Every listed intersection tests both capture identity and physical room. Full memberships and overlap lists are in `out/POPULATIONS.json`.

VSI-Bench and ReVSI each overlap `arkitscenes/41159526` and `arkitscenes/41159521`, both room `arkitscenes/venue381879`. Raw a2v3 contains 12 and 11 rows respectively; example qids are `p7eced979894217fedefe2f63` and `p539342c170337712e1872304`. The frame universe contains 32 frames from each capture; the readout list names both captures. VSTI has no observed intersection. No other in-scope overlap appears in the recovered populations.
The frame universe and readout list are not proof of checkpoint consumption. The pinned admitted step-544 indices exclude both captures. The lineage gaps preserve their venue disclosure, and no gap claims that missing ancestors are clean. A future record must retain all overlaps; policy permits venue 381879 only when disclosed.

Prepared membership uses pointing 93c4fed5, routing 613a9f9e, VQA f9dc4a2d, pose scene order 3cb1ccf5 and pose mix order d8d33340. The pose tuples address the a2v3 and a3v2 row stores by source index and row i. These files prove admitted populations, not the exact batches sampled through step 544.
The six recovered row files are scene projections, not SQLite databases. `SOURCES_13.tsv` attests the original full-database hashes faa0cfc4, c48d5b62, 5deb54bc, b32359ce, 0b95850a and 3d1d2d05; this build hashes the supplied gzip bytes separately. The local v7 SQLite hash 210b2534 is independently checked before its full-row scan.
v7 minus n/z/u retains 183,318 rows: 21,095 distinct rows are removed. The ordered lists u/n/z remove 2,637 / 601 / 17,857 rows; z matches 17,879 rows, including 22 already removed. The other lists in w19 component_rows remove no additional v7 rows. N’s n1fix2 config binds the six kit lists and n only; this build does not claim that it binds z/u.
The 8,315-row absolute-distance audit uses aedd3b54, while n1fix2 row_sources binds 1b6bc0ce. Recovery and units hashes match their named source bindings. The audit preserves this difference instead of certifying every N family from the three slices.

The directly pinned missing depth preparation is `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/97a6a3eb/arm/frozen/b19a1200/receipt.json`, SHA256 a60f3a9f72beeb49e1cc7ee0497903bb000458a7faf99b76d9e0bc16a8c1537b.
The step-200 artifact requires configuration hash 3ef158ce572c7e3b76525508dc42298758c715d24deff9eaa9e037a92a510838 under the 49becb79 run; its exact config filename and membership receipt are not specified. The depth config hash is 45d21dd2ed5314b356ead59a43b8850f22aa382916be242fd57912db293b33f4. No filename is invented.
`out/RECEIPT_GRAPH.json` follows every recovered root receipt. It distinguishes recovered metadata, recovered scene projections and missing references. Exact upstream missing stores include `ap/8865619b/u/7c9f2d84/rows.sqlite` (c09bb5ca) and `ap/1742c666/s/q127808/vxm_m4/rows.sqlite` (c180e779); the readout inventory also names `ap/544dcf9b/in/ce7286a1/19c85a70.jsonl.gz` (63366c1f). Full expected paths and hashes are retained in the graph and relevant gaps.
N’s pointing binding names the missing 25,020-row upstream store, not the recovered 20,239-row prepared store. Its routing binding requires `admitted_routing_receipt`; its host receipt and scene rebuild are null. Complete post-filter family manifests are not established.

Genuine archive members include frame_map 17aa3e9e, frame_plan 7cc01f36, tokenizer 5f9e4d49 and source archive 845b1789 from h1/chain_r1/build/fx/k/, plus base model cc724d5e from old_lanes_3_30_a.tar. `out/REVIEW_PIN_RECOVERY.json` records these and the runtime tower binding. Member hashes cover the uncompressed member bytes. Geometry’s gap does not request release identity that is already present.
The frame-pool audit reports 1,193 archived sample rows across 125 target captures, all outside the three-bank claim scope; no sample hits either venue-381879 capture. Its `work/verify_hits.py` produces that count. `out/FRAMEPOOL_CONTEXT.json` binds its report and distinguishes its source coverage from the recovered projections used here. The audit establishes neither checkpoint consumption nor an evaluation-only explanation.

`bash work/run_python.sh work/self_check.py` produces `out/SELF_CHECK.json`: every requested slot refuses individually for missing evidence; training and native_evaluation refuse at init_m544; synthetic sealed VSI-Bench, VSTI and ReVSI gateway probes refuse for the same reason. Native evaluation additionally requires five program-choice records outside this task.
`bash work/run_python.sh work/test_policy.py` produces `out/policy_tests.log`: 5 tests pass against the unchanged copied policy and test bytes. No GPU, network, official bank items or model weights are used.
`python work/stage1.py` copies sources and recovers genuine archive members. `bash work/run_python.sh work/stage2.py` computes all counts and overlaps; `bash work/run_python.sh work/build_records.py` writes the graph, nine gaps and registry. Run the test and self-check commands above, then `bash work/run_python.sh work/package.py` to validate and package.
`sha256sum FILE` reproduces any content hash. `out/VALIDATION.json` verifies input hashes, complete row accounting, the unchanged registry and expected policy refusals. It certifies this evidence bundle, not component eligibility.
The deliverable is `out/sb_records.tar`; its SHA256 is in `out/sb_records.tar.sha256`. The tar includes this report, records/gaps, the kit-root source copies, unchanged policy code and reproduction scripts. It excludes itself, its checksum sidecar, training databases and scratch test artifacts.
The no-archaeology skill governs this report. No historical-process sentence requires an exception.
