# cont_ops25 STATUS (trinity-3-30; started 08:34Z 11-20; rotate by 14:00Z; successor cont_ops26)
## 08:40Z
- Codex round 6 (camera self-consistency + S2 split) RUNNING on Astra: tmux c25_r6 on 2-28 (runner /scratch/jjyeung/orch_n30/cont_ops25_c/r6_run.sh, falls back to default implement model on capacity); receipts agent/scratch/codex_runs/20261120T083444Z_c25_r6.
- Next: round 7 = T1 funnel join (brief /scratch/jjyeung/orch_n30/cont_ops25/BRIEF_R7.md, copy to gbuild/BRIEF_R7.md); corpus try once on t1ret; mirror t1.gz to 1-18; T3 waits for N export + orchestrator order.
- Nothing of mine on Orchard or GPUs.
## 08:48Z
- Round 6 DONE (Astra, 8 min): NPZ self-consistent; reader cameras outlier on 20/38. BLOCKER posted (events/cont_ops/*_BLOCKER_reader_tower_cameras_wrong_on_20_of_38_GT_captures.md; detail files_cam/). Score pass vs flagged: no difference (-0.6 [-29,+26]).
- Round 7 RUNNING (tmux c25_r7 on 2-28; gbuild/BRIEF_R7.md = lane BRIEF_R7.md; section 0 camera split, then T1 funnel, score_ceiling --t1-capture, migrations, T1 S2 split). Receipts codex_runs/*_c25_r7.
- Next: corpus try on t1ret (fetch small files to /dev/shm/c25/t1ret), mirror after R7, RESULT.
## 09:05Z
- Round 7 DONE (Astra, 10 min): T1 funnel + camera split + S2 split. RESULT events/cont_ops/20261120T0903Z_RESULT_T1_funnel_*. Record D/GROUNDING_FUNNEL_20261120.md T1 section + INDEX. Correction owed in next RESULT: "27/27 S2 had target in pool" holds by construction (S1 definition), not a finding.
- Corpus add_read refused t1ret (format). Stray files I created by mistake: corpus/stage2/reads/{need.json,reads.sha} (REMOVAL_CANDIDATES). rm_guard queued a stray command line (harmless /tmp-free cleanup) in agent/PENDING_USER_COMMANDS.md.
- Mirror: 1-18 /scratch/jjyeung/n30_mirror/cont_ops25/gbuild_t1_r67_20261120T0905Z.tar sha d5e8773e3e94a834... (source sha equal).
- ORCH ORDER 0848Z (camera items pricing, shared features, conditional GPU job): Round 8 RUNNING (tmux c25_r8 on 2-28; gbuild/BRIEF_R8.md = lane BRIEF_R8.md). Inputs on 2-28 /scratch/jjyeung/orch_n30/cont_ops25_c/cam: reads/ (corpus s544 H482p+H418r, s400 H900; pose9 inside), gt/t1_gt/gt (34/52 camera-capture GT NPZ from 1-18 dose_pool/out/t1_gt, hash-matched). 18 camera captures have no GT copy. dev-S1 camera items: ScanNet 29 + ScanNet++ 23 captures, no ARKit.
## 09:19Z
- Round 8 DONE (Astra 14 min): RESULT events/cont_ops/*_RESULT_camera_items_priced_coverage_not_orientation_separates.md (files_cam/). Correction re S2 tautology posted there.
- ORCH NOTE 0909Z: binding test -> Round 9 RUNNING (tmux c25_r9 on 2-28; gbuild/BRIEF_R9.md; out cap/score_bind). Corpus refusal noted in corpus/LEFTOVER.md item 9.
- Queue (one Codex round at a time): K2 coverage-job kit (lane BRIEF_K2.md; only if R9 says ARKit GT binds), then Astra review of S2 table (lane BRIEF_REV1.md; review preset, read-only).
- Owed: design record D/TOWER_CAMERA_FAILURES_20261120.md + INDEX line after R9.
## 09:30Z
- Round 9 DONE: ARKit GT binds to reader frames (same-frame IoU 0.618 vs 0.083 best alt; 0/38 change). Rotation accurate-pose loss read (small-angle MRA precision; copy 32/32). RESULT events/cont_ops/*_RESULT_ARKit_GT_binds_*; files_cam/{REPORT9,BINDING_R9,ROTATION_ACCURATE_POSE_LOSS}.md. Record D/TOWER_CAMERA_FAILURES_20261120.md + INDEX line.
- K2 kit build RUNNING (tmux c25_k2 on 2-28; gbuild/BRIEF_K2.md; outputs gbuild/orchard_tower2x, cap/score_tower2x, REPORT_K2.md). After it: place/CPU check/submit on general per REPORT_K2 (one job on general at a time; check squeue first), ledger in cont_ops25/work/ORCHARD_LEDGER.jsonl, 1-min monitoring.
- Then: Astra review of S2 table (BRIEF_REV1.md, review preset).
## 09:52Z
- K2 DONE: Orchard holds only 32 anchors for the 10 ARKit captures (kit gbuild/orchard_tower2x usable for arm A only). trinity-2-28's 8 GPUs all held by user yimingg2 (14 h) -> GPU route Orchard. QUESTION event 0948Z states the route (default proceeding).
- Staged: governed stream cont_ops25_arkit_lowres (done; record .done.1795168190): 1,250 lowres_wide PNGs + 10 traj, 88.7 MB, /data3 ARKitScenes 3dod -> 2-28 /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres (stream sha 19bf2d7e… both ends). Selection: lane work/SELECTION.json (+ 2-28 cont_ops25_c/SELECTION.json).
- K3 RUNNING (tmux c25_k3 on 2-28; gbuild/BRIEF_K3.md): recipe verification vs /scratch/jjyeung/devs1_frames, kit gbuild/orchard_tower2x_b (arms A 32, B 63, C 94), scorer cap/score_tower2x_b (similarity scale, gravity transport).
- Then: place/CPU/submit on general (one job), fetch, score, RESULT; then Astra review of S2 table (BRIEF_REV1.md).
- ORCH NOTE 0933Z item 1 (ARKit counted again; funnel pooled and by dataset): pooled = REPORT7, by dataset = REPORT9 tables; state in next RESULT.
## 10:30Z
- ORCH ANSWER 0948Z: route approved. K3: served PNGs not in /scratch/jjyeung/devs1_frames; found in /scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames. K3b: no pixel-exact recipe; near-exact = Up/Down unrotated, Left rotated CW, 2.5x upscale (mean abs err 1.08/255, max 124); Down=180 is wrong. A+A'+B forecast 29.3 min > 25.
- K3c RUNNING (tmux c25_k3c on 2-28; gbuild/BRIEF_K3C.md): arms A' (recipe anchors) + B (63 frames); control A' vs T1 served cameras (<=1.0 deg on >=8/10); verdict B vs A'; one place.tar via a governed byte stream (io-weight 1) through tools/ossh.sh from 3-30 (/dev/shm staging, file >5 MB only in /dev/shm).
## 11:05Z
- K3c built (Astra): recipe OpenCV bicubic, Up/Down unrotated, Left CW, mean err 1.08/255; forecast 24.4 min; placement 44,677,021 B. Placed on Orchard /project/community/jjyeung/ac794e028b16f via governed stream cont_ops25_oplace (done). Lane copies of kit scripts: /dev/shm/c25/k3 (o_cpu2.sh, o_check_sub2.sh = mem 200G; o_dbg.sh).
- CPU check 173681 FAILED 5:09 (20G cap reached), rerun 173683 (200G) FAILED 5:17 (MaxRSS 103 GB): same failure, cause unknown (0.py swallows tracebacks, logs to /dev/null). Diagnostic run 173686 with traceback to $P/c.log RUNNING. Next if unclear: Codex Astra review of the defect.
## 11:17Z
- Diagnostics 173686/173697: cause = 2.py images() E10: recipe-decoded raw RGB hash on Orchard (its OpenCV) != hash computed on 2-28 (memory was not the cause). Ledger work/ORCHARD_LEDGER.jsonl.
- K3d RUNNING (tmux c25_k3d on 2-28; gbuild/BRIEF_K3D.md -> new kit gbuild/orchard_tower2x_c): record instead of E10, mem 200G, error logs in the token dir, new token reusing ac794e028b16f/8.tgz by hard link (< 1 MB new bytes).
