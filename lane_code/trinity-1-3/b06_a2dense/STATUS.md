# b06_a2dense STATUS (a successor resumes from this file alone)
Updated: 2026-11-16T11:55Z. Lane: headless Claude Opus on trinity-1-3. Brief: orch_n30/briefs/b06_a2dense.md -> queue brief orch_n30/briefs/qs/06_a2_dense_frames_tower_cache.md. Lane folder L=/scratch/jjyeung/orch_n30/b06_a2dense. Events: orch_n30/events/b06_a2dense/. Finish or rotate by 22:30Z.

## Facts established (with evidence)
- Inputs pulled (single small files): L/work/inputs/frame_map.jsonl.gz sha 17aa3e9e (= k6 MAP, 290,880 lines), frame_plan.json.gz 7cc01f36 (keys a: 3,451 ARKit captures, v: 1,246 mp4 scenes, total: 4,697).
- Orchard egress to Apple works from the login node (HTTP 200/206; L/work/oq2.out). Compute-node egress untested.
- ARKit ordinal k = row k of lowres_wide.traj (167/167 known ordinals of 2 captures exact; every traj row has a zip member within 2 ms; total_num_frames = traj rows). L/work/oq2.out.
- Orchard holds the k6 decoder venv /project/community/jjyeung/cp4tk_fr/venv (cv2 4.14.0, numpy 2.2.6, py 3.12.3) and source media tarballs cp4tk_fr/media/scannet.tar.gz (27.6 GB), scannetppv2.tar.gz (21.4 GB); k6 replica cp4tk_fr/k6tk: 12 shard tars in parts/{a0n3,a1n3,a2n3,v0n3,v1n3,v2n3} (sizes match INDEX.json for the ones listed; full member count not yet checked).
- The plan's "993 of 994 in-map d1/d2 clips need no new decode" does NOT hold under the tree's one dense rule (dense_eval.nested_indices midpoints): of the A2 VQA clips only 4/280 d1 and 0/617 d2 are complete from k6; new decodes needed.

## Running
- Orchard login-node extraction (nice, not a job) pid 1115655 in /project/community/jjyeung/okh7/b6d1 (ledger L/work/ORCHARD_LEDGER.jsonl): routing r16, pointing, pool eb3429c5, pose a2v3 full, a3v2 sample. Output o/{rows,clips}.jsonl.gz, summary.json; log.txt.
- Subagent (Claude Opus, high) building the tower cache + shuffled-bank mode in L/cache (deliverables L/cache/out/).

## Code (L/dense)
- sqlro.py: read-only SQLite scanner over split parts / tar members (tests/test_sqlro.py; equal to sqlite3 on the 152,123-row A2 store).
- extract_meta.py: metadata-only clip extraction (no RGB).
- dense_manifest.py: plan (metadata only) / seal (after fetch) / attach (row -> dense_source for r2_dense.build_training). tests/test_dense_manifest.py.
- wa_dense.py: ARKit range fetch wrapping the pinned k6 wa.py (copy at L/work/k1src/p2_build/c5d3/k6bin/bin/wa.py), traj-row timestamps, version pin, parity ordinals.
