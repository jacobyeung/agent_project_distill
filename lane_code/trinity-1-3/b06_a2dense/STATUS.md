# b06_a2dense STATUS (a successor resumes from this file alone)
Updated: 2026-11-16T22:20Z. Lane: Devin successor #2 on trinity-1-3 (17:47Z-22:20Z) rotated at the brief's 22:30Z limit; the next successor resumes here. No ORCH word since ANSWER 1913Z (waited to 22:19Z). Brief: orch_n30/briefs/b06_a2dense.md -> queue brief orch_n30/briefs/qs/06_a2_dense_frames_tower_cache.md. Lane folder L=/scratch/jjyeung/orch_n30/b06_a2dense. Events: orch_n30/events/b06_a2dense/. Finish or rotate by 22:30Z.

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

## Binding ORCH constraints (newest first)
- ORCH ANSWER 1913Z: 170379 cancelled (done 19:22:58Z, RESULT 1923Z). Submit nothing to Orchard until ORCH says GPUs are back. Parity on the login node only if < 30 min CPU (it is not: needs all parts + every k6 tar) -> wait.
- ORCH ORDER 1844Z (USER): no GPU anywhere; submit NOTHING to Orchard (general included) until ORCH says GPUs are back; CPU work continues. 170379 was submitted 18:52Z before I read it; QUESTION event 1912Z asks; default: let it finish, run parity (job 3) on the login node at nice 19, submit nothing.
- ORCH 1746Z: submit the three CPU jobs only after job 170320 has left general AND the newest INBOX_TO_DISTILL_ORCH_* (in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/) and squeue show no pending main job on general. All must leave general before the D0 m400 read (~01:00Z 11-17, earlier than the 01:40Z in older notes). One job at a time on general. Cancel pending array tasks at 00:00Z if job 2 is not done.
- ORCH RULING 1638Z (USER): main has GPU/partition priority; before any Orchard submission check squeue for main's pending jobs (jjy_* and main's a15_cot_ap jobs listed in its inbox); if main pends on general, do not submit, write a RESULT, submit when main's job started or main says go.

- 18:20Z power kit: L/power/power.py (imports cont_ops readk f1f2.bootstrap; 450 main items of size/rel-distance/counting, 69 rooms). Proxy from A544 alone: single-read half-width 4.11 pp (L/power/proxy_a544.json); synthetic paired test OK. Owed: when cont_ops posts the m200 ITEMS.jsonl (readk/kit/build/a4cadd8934b/...), run `power.py A544.jsonl ITEMS.jsonl L/power/m200_power.json` and write the half-width into A2_CARD_DRAFT.md Power line and A2_DENSE_READY.md.

- 18:37Z job 170320 COMPLETED (cont_ops RESULT 1837Z: D0 m200 verdict STOP on F1 object size). General free, no main pending (inbox 183801Z = trinity-1-13 GPUs only).
- 18:39Z power on real m200: paired m200-A544 on the 450-item mean = -2.24 pp, CI [-6.62, +1.64], half-width 4.13 pp > 1.0 (L/power/m200_power.json b8ee62f0; ITEMS c1c99e4d). Rule 3 cannot be a CI rule at 1 pp; it stays a point rule. Card/READY to be updated.
- 18:39Z SUBMITTED job 1 egress: Orchard job 170374 (a15_cot_apc9f6b9ac93a6), PENDING Priority. Next: when gone from squeue, read logs/egress.170374.json + logs/disk.170374.txt under okh7/db3954b2, then submit job 2.

- 18:45Z 170374 FAILED 1:0 in 2 s, no logs: egress.sh found its root via $0 (= slurmd spool copy under sbatch). Fixed: F=${EGRESS_ROOT:-/project/community/jjyeung/okh7/db3954b2} (local L/out/packets/frame_fetch/bin/egress.sh = Orchard copy, sha checked; old copy bin/egress.sh.v1). Login-node run OK (206, 65536 B, zip magic). djob.sh uses $0 too but is called by absolute path in --wrap (safe). Resubmitted as 170377 at 18:46Z.

- 18:50Z egress 170377 COMPLETED: compute node orchard-community-0 egress OK (206, 65536 B, zip magic). Compute /tmp = /dev/md127 5.9T (4.8T free), /dev/shm 922G, 1.8 TB RAM (logs/disk.170377.txt; L/work/oq21.out). The 280 GB cache fits node-local /tmp.
- 18:50Z array submit REFUSED by Slurm: general_qos MaxSubmitPU=5, MaxJobsPU=1 (L/work/oq23.out), so a 6-task array cannot be submitted (and pending tasks would block other lanes' general submits). Replaced by ONE job running the six parts serially: bin/dserial.sh (local L/out/packets/frame_fetch/bin/dserial.sh = Orchard copy, sha checked), per-part tag ${SLURM_JOB_ID}t<i>.
- 18:52Z RUNNING job 2 = Orchard 170379 (a15_cot_ap7128842a8567) on orchard-community-2, --time 05:00 (hard end 23:52Z, before the 01:00Z m400 window). Logs: okh7/db3954b2/logs/dserial.170379.log and logs/<a0n3|..>.170379t<i>_0.log; parts/<tag>/DONE. Poll via ossh every 10 min max.

- 19:04Z 170379: a0 DONE 18:56Z (495/500 ok, 5 err, 17,097 frames, 0 misses, tar 5.0 GB), a1 DONE 19:01Z (493 ok, 7 err, 17,028 frames), a2 running. Errors are the wa_dense clock guard ("known ordinals differ from traj rows", n_bad 19-30): those captures are refused, not misaligned; the seal must list them as deferred with that reason.

- 19:12Z a2 DONE 19:05Z (495 ok, 5 err, 16,947 frames); a total 1,483/1,500 captures, 51,072 frames, 17 clock refusals. v0 running (scannet 179 members extracted in 383 s).

- 19:23Z 170379 CANCELLED 19:22:58Z. DONE parts kept: a0n3 a1n3 a2n3 v0n3 (v0 ended 19:20:43Z). Owed when ORCH says general is back: resubmit the same job-2 command (SUBMIT.md step 2; dserial.sh skips DONE parts -> v1, v2, ~15 min each), then parity (job 3 or login node), then after_fetch.sh.

- 19:35Z partial seal dry-run (no pixel file): L/work/fetch_partial/ (wa_out 1,500 lines cdf7400c = cat of a0-a2 out.jsonl; wd_out = v0 out.jsonl bfbfb621; SEALED_partial.json): 2,741 = 1,902 clips + 839 refusals (822 d1/d2 parity_missing = scenes of v1/v2 not yet run; 17 d3 = the clock-guard captures). Parity 6,510 checked, all byte-equal, 0 differ. Seal pipeline works end to end.
- Orchard parts (16 GB, okh7/db3954b2/parts; sha256 in L/work/parts_sha_1930Z.txt): a0n3_000.tar 71e920bc, a1n3_000.tar aff4914f, a2n3_000.tar 01654203, v0n3_000.tar 628e058a. Orchard-resident: no mirror needed (path + sha recorded).

## Resume point for the next successor (exact)
- Nothing of this lane runs on Orchard (170379 cancelled 19:22:58Z; general empty of ours). Wait helper: L/work/wait_orch.sh (<=9.5 min, returns on a new ORCH file or inbox file).
- Gate: ORCH must say GPUs/general are back (ORDER 1844Z, ANSWER 1913Z). Then, after checking `TZ=UTC squeue -u jjyeung -p general` is empty and the newest INBOX_TO_DISTILL_ORCH_* shows no main job pending on general: submit SUBMIT.md step 2 (one job, bin/dserial.sh; runs v1, v2 only, ~15 min each; --time may drop to 01:30:00), poll every 10 min (logs/dserial.<id>.log). Then parity: job 3 command from SUBMIT.md (or login node nice 19 if ORCH allows). Then `bash L/work/after_fetch.sh` (pull + seal), counts into A2_DENSE_READY.md, mirror small outputs (SEALED.json etc.) to trinity-1-18 n30_mirror/b06_a2dense, one RESULT event.
- Then: GCS copy of parts tars (governed stream; ask ORCH which bucket) per the cache-location answer.
- When tree build 7 carries the cache patch (events/tree_rebuild/STATUS.md): rerun tests.test_gf1_cache on the integrated tree; cost packet when ORCH hands an H100 node.
