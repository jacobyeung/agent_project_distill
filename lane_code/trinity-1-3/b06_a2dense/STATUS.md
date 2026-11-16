# b06_a2dense STATUS (a successor resumes from this file alone)
Updated: 2026-11-16T13:20Z. Lane: Devin successor on trinity-1-3 (Claude lane stopped 11:59Z at its weekly limit). Brief: orch_n30/briefs/b06_a2dense.md -> queue brief orch_n30/briefs/qs/06_a2_dense_frames_tower_cache.md. Lane folder L=/scratch/jjyeung/orch_n30/b06_a2dense. Events: orch_n30/events/b06_a2dense/. Finish or rotate by 22:30Z.

## Facts established (with evidence)
- Inputs pulled (single small files): L/work/inputs/frame_map.jsonl.gz sha 17aa3e9e (= k6 MAP, 290,880 lines), frame_plan.json.gz 7cc01f36 (keys a: 3,451 ARKit captures, v: 1,246 mp4 scenes, total: 4,697).
- Orchard egress to Apple works from the login node (HTTP 200/206; L/work/oq2.out). Compute-node egress untested.
- ARKit ordinal k = row k of lowres_wide.traj (167/167 known ordinals of 2 captures exact; every traj row has a zip member within 2 ms; total_num_frames = traj rows). L/work/oq2.out.
- Orchard holds the k6 decoder venv /project/community/jjyeung/cp4tk_fr/venv (cv2 4.14.0, numpy 2.2.6, py 3.12.3) and source media tarballs cp4tk_fr/media/scannet.tar.gz (27.6 GB), scannetppv2.tar.gz (21.4 GB); k6 replica cp4tk_fr/k6tk: 12 shard tars in parts/{a0n3,a1n3,a2n3,v0n3,v1n3,v2n3} (sizes match INDEX.json for the ones listed; full member count not yet checked).
- The plan's "993 of 994 in-map d1/d2 clips need no new decode" does NOT hold under the tree's one dense rule (dense_eval.nested_indices midpoints): of the A2 VQA clips only 4/280 d1 and 0/617 d2 are complete from k6; new decodes needed.

## Running
- Orchard login-node extraction (nice, not a job) pid 1115655 in /project/community/jjyeung/okh7/b6d1 (ledger L/work/ORCHARD_LEDGER.jsonl): routing r16, pointing, pool eb3429c5, pose a2v3 full, a3v2 sample. Output o/{rows,clips}.jsonl.gz, summary.json; log.txt.
- Nothing. The Claude cache subagent died with the lane; its tree is L/cache/tree_cache (gf1_cache.py, tests/test_gf1_cache.py; run via L/cache/run/run_tests.py with env L/cache/run/env.sh). Last run L/cache/out/tests_new_try.json: parity fails on one bf16 router gradient (projections.0.bias rel 0.0167 vs tol 0.015625).
- Orchard extraction pid 1115655 finished (o3 pool rows pulled to L/work/inputs/rows_s3.jsonl.gz).

## Code (L/dense)
- sqlro.py: read-only SQLite scanner over split parts / tar members (tests/test_sqlro.py; equal to sqlite3 on the 152,123-row A2 store).
- extract_meta.py: metadata-only clip extraction (no RGB).
- dense_manifest.py: plan (metadata only) / seal (after fetch) / attach (row -> dense_source for r2_dense.build_training). tests/test_dense_manifest.py.
- wa_dense.py: ARKit range fetch wrapping the pinned k6 wa.py (copy at L/work/k1src/p2_build/c5d3/k6bin/bin/wa.py), traj-row timestamps, version pin, parity ordinals.

## Done (outputs)
- Metadata pre-pass + plan: L/out/plan_v4/ (summary L/out/plan_v4.summary.json): 6,195 clip signatures, 2,741 planned clips (d1 556, d2 683, d3 1,502), 0 refusals; new decodes 11,410 frames/1,225 scenes; ARKit range 46,424 frames/1,500 captures. Per-stream demand L/out/DEMAND_BY_STREAM.json. A0 v4 families: every scene planned, 0 off-map (L/out/A0_FAMILY_SCENE_COVERAGE.json).
- Pose count: L/work/inputs/pose_counts.txt: 27,604 dense pose rows, all with a nested 64 inside posed ordinals (no new decode).
- Cache tests (12:35Z): tests.test_gf1_cache 10/11 pass (L/cache/out/tests_full_1235Z.json, PARITY_full.json). The one failure is the BF16-cache case (router grad projections.0.bias rel 0.0167 > pre-registered 2**-6); every FP32-cache case passes, the BF16-tower+FP32-cache case exactly (rel 0.0). Rule left unchanged; production default cache dtype float32. Regression (gf1, gf1_contracts, gf1_review, gf1_trainer, gx_dense_binding): 30 pass + the same 2 pre-existing errors as base (lost 2-18 path; torchvision tvF) (L/cache/out/tests_regress_1240Z.json).
- Cache patch on build 5 (seal ba346bd9, = L/cache/work/tree_r1): L/out/packets/gf1_cache/gf1_cache_on_b5_ba346bd9.patch (5 files); dry-run applies to build 5 and to the build-6 working tree's gf1.py/dense_eval.py/carrier_c1_data.py.
- Cache size, real grid (all dense frames 640x480 -> 130 cells): L/out/CACHE_SIZE.json: 102 MB/clip FP32 at 32 anchors; 280 GB for 2,741 clips (245 GB four streams without pool); 64 anchors double it.
- Frame fetch/decode packet: L/out/packets/frame_fetch/ (+ tgz frame_fetch_db3954b2.tgz sha 525991fd), staged on Orchard /project/community/jjyeung/okh7/db3954b2. Login-node self-test: v path OK, one ARKit capture 64/64 frames; parity 3/32 byte-equal, 32/32 pixel-equal (max|d|=1) -> dparity.py pixel rule (max|d|<=1, frac<=1e-3) and dense_manifest.parity(pixel=) (dense tests 18/18). SUBMIT.md holds 3 job lines (egress, fetch array, parity), names in the ledger; NOT submitted (needs ORCH GO).

- Cost packet L/out/packets/cost_step/ (README protocol + analyze.py, synthetic-tested). Card draft L/out/A2_CARD_DRAFT.md. Ready file L/out/A2_DENSE_READY.md.
- Mirror: L/work/b06_mirror_1310Z.tar = trinity-1-18:/scratch/jjyeung/n30_mirror/b06_a2dense/b06_mirror_1310Z.tar (sha256 15cd0804...7dbb, equal).

## In flight
- (done 13:08Z) Codex refute review (gpt-6-astra high, read-only), tmux b06_review1; prompt L/work/review/prompt_refute1.md; receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T130347Z_b06_refute1 (final_message.md at the end). Check: `tmux has-session -t b06_review1`.
- Orchard root okh7/db3954b2 holds the staged packet and selftest/ (login-node test only).

## Next steps (waiting on ORCH; poll events folder and L/inbox every 10 min)
1. ORCH 1300Z: GO for the frame jobs only after the D0 m200 read leaves general (~19:30Z; watch EV/cont_ops events); array runs %1 (serial); all off general before ~01:40Z 11-17. Then: submit SUBMIT.md job 1 (egress), then job 2 (array 0-5), then job 3 (dparity) after all parts DONE; one ossh call each; TZ=UTC squeue at most every 10 min.
2. Pull parts/*/out.jsonl (wa_out a*, wd_out v*) and parity.jsonl (small files, one at a time); run dense_manifest.py seal out/plan_v4 ... SEALED.json parity.jsonl; record counts in A2_DENSE_READY.md; mirror.
3. When tree build 7 carries the cache patch: rerun tests.test_gf1_cache on the integrated tree; run the cost packet when ORCH hands an H100 node.
4. Review 1 folded in (A2_DENSE_READY.md section 'Refute review 1'). Open: real-row parity in the frame-host job; one-point power from D0's item-level m200 read before registration.

## Defaults in force
- ReVSI first, frame count a parameter (32/64), SFT first (ORCH NOTE 11:55Z). ReVSI decides nothing in the card's stop rule (benchmark).
- Cache dtype float32 (BF16 cache failed the pre-registered rule by a hair; rule left unchanged).
- Pixel parity rule max|d|<=1, frac<=1e-3 (fixed before the full run).
- 12:59Z card updated for ORCH 1227Z room note (room direct, EAT-1 reader).
- after_fetch.sh ready: L/work/after_fetch.sh (pull + seal, run after Orchard parts and parity are done).
- 13:10Z: ORCH 1300Z answered: ASK2 routed to tree_rebuild4 (build 7); ASK3 = I order one Codex review (gpt-6-astra high). Cache-location answer written in A2_DENSE_READY.md (derived, node-local, rebuilt per allocation; frames to GCS after seal). egress.sh now also records compute-node disk (Orchard copy equal). Packet tgz now 5a9eea9d.
- 13:40Z: review 1 fixes landed (dense 19/19; test_gf1_cache 11/12, only BF16-cache fails; regression 30+2 pre-existing). New patch sha 3610e972 (supersedes 8294f618). Card rule 3 one-sided + claim rule + zero-bank print. R0 overlap 0 (L/out/R0_OVERLAP.json). Mirror b06_mirror_1340Z.tar c31aca69 equal on trinity-1-18.
