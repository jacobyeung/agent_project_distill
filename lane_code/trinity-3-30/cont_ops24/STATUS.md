# cont_ops24 STATUS (trinity-3-30; started 03:12Z 11-20; rotate by 08:40Z; successor cont_ops25)
## 03:25Z
- Read rules, brief, grd_funnel BLOCKER, record. Kit unpacked at work/kit2 (sha 17a910f1 verified).
- T1 in progress: (a) parity rule, (b) Orchard integration — inspecting package b9ef552934627 on Orchard.
- Nothing of mine on Orchard. No Codex round running.
## 03:36Z
- (a) Parity rule registered in D/GROUNDING_FUNNEL_20261120.md section "Parity rule for the ground-call rerun" (brief's rule; no better evidence). Baseline payload stage1.py/grounding.py == kit fixtures.
- (b) Design: derive a new orchard_h10 package from b9ef552934627 (one read = read-1 settings; ground worker; capture written job-local and uploaded to GCS by job.py before publish; only CAPTURE.json/PARITY.json return via pool). Codex Astra implement RUNNING on trinity-2-28: tmux c24_gbuild, dir /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild (BRIEF_GBUILD.md: Part A package+Orchard scripts, B GT adapter, C point-prompt mode for T2), log ../gbuild_dispatch.log. Inputs copy also in /dev/shm/c24/in1 on 3-30.
- (d) GT: 38 of 60 staged 1-18 -> 2-28 by one IB tar pipe into /scratch/jjyeung/orch_n30/cont_ops24_c/gt (sha lists match, md5 8e9e5d5e). 22 missing on 1-18 (no alternates): ARKit 41126645 41159771 41159772 41254810 42446097 42899829 47331002; ScanNet scene0261_02 0320_01 0380_01 0515_00 0515_01 0642_01 0666_01; ScanNet++ 246fe09e98 37c9538a2b 38fcf02d0b 3ce6d36ab5 ca3b651c23 d6bb698875 e35232b92f e667e09fe6.
- T2: note with points schema sent to nvkey1 inbox (0405Z). Orchard: nothing of mine. Next: poll Codex every 10 min; then (c) Astra review, place/CPU/submit.
## 03:58Z
- Codex build c24_gbuild DONE (REPORT.md on 2-28 gbuild/; copy /dev/shm/c24/g1). Package token a1abb3a204ff8 (delivery d0dac81b…, payload d7e65fb6…, plan 87449d1f…), 33 CPU tests pass. GT adapter refused (NPZ rasters 240x320 only, conventions undeclared; 142/300 occurrences bind by exact label; 76/150 items have GT). Point mode = refusing stub (SAM3 geometric-prompt source not in payload).
- Astra review c24_rev RUNNING on 2-28 (tmux c24_rev; /scratch/jjyeung/orch_n30/cont_ops24_c/rev/).
- Orchard: placed /project/community/jjyeung/a1abb3a204ff8 (+10.8 MB; free 238 GiB). CPU entry-sequence job 173603 on general (CPU only; o_cpu_general.sh) RUNNING orchard-community-2 since ~03:57Z. GPU submit (o_check_sub.sh) waits for CPU.json pass AND review GO.
## 04:05Z
- CPU job 173603 COMPLETED 6:02; a/c/CPU.json passed (bundle guard, entry sequence, memory fits). GPU submit waits for review c24_rev verdict.
## 04:22Z
- Review c24_rev (Astra, 4 min): GO-WITH-FIXES, one MAJOR (trailer-less gzip after forced kill unreadable) -> reader-side salvage, in round 2; no job-side change needed.
- First submit of a1abb3a204ff8 rejected by sbatch (gres gpu:h100:1 invalid on general). Rebuilt with parent resources (gpu:1, 16 CPU): token a5d6f41359166 (delivery f4509a4a…, plan d55222ad…), 13 tests pass. Placed (+10.8 MB), CPU job 173613 COMPLETED/passed, GPU job 173616 submitted 04:20Z on general, PENDING (Resources). Monitor tmux c24_monG (work/monG_173616.log).
- Removal candidate: /project/community/jjyeung/a1abb3a204ff8 (10.8 MB, unused).
- Codex round 2 RUNNING on 2-28 (tmux c24_r2, gbuild/BRIEF_R2.md): T2 point-prompt package (Astra points from nvkey1), GT adapter v2 (rulings: downsample predictions to 240x320, ScanNet++ half extents doubled, rigid SE3 no scale), reader salvage.
## 04:44Z
- ORCH ORDER 0350Z: T2 first, then the 64-frame ground-call arm (replaces optional arms), then T1 funnel. NOTE 0356Z: T2 splits sparse items by GT visibility (1-2 vs >=3 frames).
- 173616 FAILED 1:0 in 3 s on orchard-community-4 (no trace; output /dev/null). Hand resubmission 173618 of the same sealed BATCH.sh (logs a/d.log) ran 5 min on community-2: staging OK, GCS capture upload OK (20-byte capture verified), worker died: ImportError e2e_reader.parity resolves to h1eval/reader_core copy (h1eval/__init__ inserts reader_core at sys.path[0]). Return a5d6f413591660002a632 in pool ae71c903 (move to _fetched later).
- Codex round 2 DONE (45 tests; salvage, scorer, GT adapter v2; C2 blocked on SAM source access). Round 2c RUNNING (tmux c24_r2c on 2-28; BRIEF_R2B.md): import fix + real-payload CPU import smoke test, rebuild T1, point-prompt package with selector-restricted control arm + text repeat; SAM3 API copies in gbuild/sam3_ref.
- Next brief ready: /dev/shm/c24/BRIEF_R3.md (64-frame arm).
## 05:07Z
- Round 2c DONE (52 tests): T1 fixed a52c1dcfae7bb (delivery ef9575f1…; not placed yet); T2 package ab704caf7807e (delivery 0d547179…; Astra points sha fb6246cf…; 150 point + 150 restricted-selector + 10 text replays; forecast 167 GPU-min, 84-250). Real-payload import smoke test reproduces the old failure, passes fixed ones.
- T2: placed (+11.0 MB, free 232.8 GiB), CPU job 173624 passed, GPU job 173625 submitted ~05:06Z by hand sbatch (logs a/d.log, --exclude=orchard-community-4; script /dev/shm/c24/o_sub_hand.sh). Monitor tmux c24_monT2 (work/monG_173625.log).
- Astra review c24_rev2 of T2 point runtime + scorer RUNNING on 2-28 (rev2/); if BLOCKER in runtime -> scancel 173625 and rebuild.
- Next Codex: BRIEF_R3 (64-frame arm) after rev2.
