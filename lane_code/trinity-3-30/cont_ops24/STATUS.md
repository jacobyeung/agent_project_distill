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
## 05:32Z
- T2 173625 RUNNING on orchard-community-2: 97 main items at 05:28Z (~8/min, ~200 KB/item); ETA end ~06:05-06:20Z. Progress monitor tmux c24_monP (work/monP_173625.log, srun --overlap reads job-local metadata/4.json every 5 min).
- Review c24_rev2: GO-WITH-FIXES (scorer only: also report the <3-frames cohort of 100 items; fallback receipt handling) -> folded into round 3 (tmux c24_r3 on 2-28, BRIEF_R3.md = scorer fixes + 64-frame arm).
- T1 fixed package a52c1dcfae7bb placed (+10.8 MB); its CPU check waits until T2 leaves general (one job at a time).
- After T2: o_fetch (g3/orchard_points/o_fetch.sh) -> work/gpull.sh URI GEN SHA BYTES t2.gz PRIO (governed pull to 2-28 cont_ops24_c/cap) -> score_ceiling.py on 2-28.
## 06:21Z
- T2 DONE: 173625 COMPLETED 65 min; RESULT 0619Z (points +4.9 [-3.9,+14.2] on 150; sparse<3 +7.9; restricted selector -6.1). Files events/cont_ops/files_t2/ (T2_TABLE.md, SCORE_T2.json sha 7d6c336b…, CAPTURE.json). Capture on 2-28 cont_ops24_c/cap/t2.gz (sha 2406c812…) + GCS gen 1795155052831221. Governed pull record renamed .done.
- Corpus: add_read.sh refuses the ground-capture format ("Cannot identify one format"); no read id. Not a reasoning-trace read.
- Mirror: 2-28 gbuild (deliveries, code, reports, out2/GT.json, cap/) -> trinity-1-18:/scratch/jjyeung/n30_mirror/cont_ops24/gbuild_cap_20261120T0625Z.tar (132 MB, sha 66231724… matches both ends).
- 64-frame arm: review c24_rev3 NO-GO (memory basis gate) -> fixed by me (basis kept fixed_g3t_shapes; 37 gpkg tests OK) -> token ac85ad201020f (delivery 1025c1c3…), placed, CPU 173644 passed, GPU job 173646 submitted 06:16Z, PENDING (Resources). Monitors c24_monD, c24_monPD.
- T1 a52c1dcfae7bb placed; CPU check after the dense job leaves general.
## 06:43Z
- RESULT 0619Z (T2 ceiling), RESULT 0642Z (T2 stage join: gain on no-GT items; S2 main on GT items; camera alignment passes 6/38 -> S4/S5 censored). Record D/GROUNDING_CEILING_T2_20261120.md + INDEX line.
- ORDER 0604Z done: K1 inputs 684 files 2.62 GB 1-18 -> 2-28 anchor_kill1/k1_inputs, 10 sha match; RESULT events/anchor/20261120T0621Z_*.
- Codex round 4 DONE (STAGES_T2); round 5 RUNNING (tmux c24_r5 on 2-28; BRIEF_R5.md: camera convention / frame binding vs GT NPZ).
- 64-frame arm 173646 RUNNING orchard-community-1, 33/160 at 06:40Z, ETA ~07:40Z. After it: fetch (g5/orchard_dense/o_fetch.sh), gpull (work/gpull.sh ... dense.gz), score_ceiling --dense-capture (REPORT3 command) on 2-28; then T1: CPU check (g3/orchard_t1/o_cpu.sh, general) + hand submit (o_sub_hand.sh with __T__=a52c1dcfae7bb).
## 08:01Z (exact)
- Dense arm DONE: 173646 COMPLETED 64 min; RESULT 0731Z (-2.0 [-7.2,+3.0]; primary -2.9). Files events/cont_ops/files_dense/. Capture 2-28 cap/dense.gz (sha 665b2ebb…), GCS gen 1795159385742121. Stream record renamed .done.
- ORCH NOTE 0735Z: no more dense arms; camera check (round 6) is the priority; BLOCKER if the reader's cameras are wrong on a class of captures. ORCH ORDER 0729Z (to n_ops5, copy): /project free space falling ~100 MB/s from other causes; ours adds ~38 MB installed in 7 package dirs, returns < 1 MB.
- Round 5 DONE (no axis/inversion convention repairs alignment; frame_indices match; report copied to files_t2/CAMERA_CONVENTIONS_REPORT5.md). Round 6 RUNNING (tmux c24_r6 on 2-28; NPZ self-consistency + S2 split), not finished at 08:00Z.
- T1: CPU 173659 passed; GPU job 173662 RUNNING orchard-community-1 since ~07:37Z; 59/160 records at 07:59Z; ETA ~08:30Z. Monitors c24_monT1, c24_monPT1.
- Successor brief written: B/briefs/cont_ops25_d.md (fetch/pull/score steps for T1; camera BLOCKER criteria).
