# Removal candidates (tree_rebuild15, 2026-11-19T21:40Z; none removed; per ORCH 2046Z item 5, move to trinity-2-28 by IB after N launches, then remove these from trinity-1-18)
trinity-1-18 W=/scratch/jjyeung/orch_n30/tree_rebuild10_w (43 GB of 40 GB cap; node 97 GB free at 21:39Z):
- W/w16b 1.4 GB, W/w17b 1.3 GB, W/w20 1.6 GB, W/w21 5.2 GB, W/w22 3.4 GB, W/w23 3.2 GB: superseded build workspaces (packages b16-b23; cores mirrored in events/tree_rebuild/ops_mirror).
- W/w24/attic 1.3 GB (superseded kit files of 24d-24k).
- W/work/conf24c, conf24e, conf24f (untar confirmations of superseded packages).
- W/w24/out/tree_rebuild_b24_90637cdf.tar 145 MB and b24b_7d7a8858.tar 149 MB (superseded by the 24c-24k overlays; keep until N launches).
- (tree_rebuild17, 02:58Z) trinity-1-18 W/work/up24m3, up24m3c, up24m4e (upload staging copies, after launch); W/work/conf24m3, conf24m4, conf24m4c, conf24m4d, conf24m4e (confirmation untars); W/w24/work/build24k/rehearsal_k2, rehearsal_k4, rehearsal_k5, rehearsal_k5b, rehearsal_k6 (fixture rehearsal roots, ~200-360 MB each); W/w24c (24m4c/24m4d workspace, superseded by w24e after launch). Orchard x_22c714e1/a24m3, a24m4e (replaced kit files), s24m3/s24m4e (empty after overlay). Keep W/w24 (tree R kit line, first-boundary tree).

## Added by tree_rebuild18 (2026-11-20)
- trinity-1-18 W/w24/work/build21/inputs/config.json, W/w24/work/build21/inputs/kit_config.json, W/w24/work/build21/kits/q/k/s.json: rewritten by an inherited 24m4h test (W/w24h/work/build24m4h/WRITE_BOUNDARY_INCIDENT.json); superseded build21 workspace; keep out of test paths (ORCH 0511Z item 6).
- trinity-1-18 W/w24g (24m4g stop-branch workspace, 45 MB) after 24m4h launches; W/work/au24 (unused audit script, ORCH 0418Z item 6).
- Orchard x_22c714e1/a24m4h/ (files replaced by the 24m4h overlay), x_22c714e1/s24m4h.tar (1.1 MB) after launch.
## tree_rebuild19 (2026-11-20)
- Orchard orchard-community-2 node dirs /tmp/q_22c714e1_173655, /tmp/q_22c714e1_173657, /tmp/q_22c714e1_173660 (rcj job staging; 173660 holds the 837 MB rebuilt DB r/rows.sqlite, keep until N launches).
- Orchard x_22c714e1/s24m4j/ (empty dirs after overlay), s24m4j.tar 348 KB; a24m4j/ (superseded kit files, rcj_x_24m4j.py, rcj_x_cbc240f8.py, rcj_x_a5e54c7d.py).
- trinity-3-30 tree_rebuild19/work/s24m4j.tar 348 KB and x24m4j/ (extracted copy) after N launches.
- trinity-1-18 W/work/rcj24m4j, rcj24m4j3 (superseded helper copies; rcj24m4j4 is current), W/work/up24m4j + s24m4j.tar after N launches.
- trinity-1-18 W/w24n (partial untar, broken), W/work/up24m4m (empty), 2-28 n30_mirror/tree_rebuild19/tree_rebuild_b24m4m_598cadf7.tar (partial, invalid).
- trinity-1-18 W/w24o (untar of 24m4n + 8 min of Codex 24m4o edits, killed 10:56Z; superseded by W/w24o2). Added by tree_rebuild20 10:57Z.
- trinity-1-18 W/w24q (untar 24m4p + 11 min of killed Codex 24m4q; superseded by W/w24q2). Orchard x_22c714e1/s24m4n/ + s24m4n.tar (superseded by s24m4o3). Added by tree_rebuild20 12:37Z.
- Orchard login /tmp/bwp.b1YfdV (bwrap probe dir, 1 empty file). Orchard x_22c714e1/s24m4r/ (empty after overlay) + s24m4r.tar. Added by tree_rebuild21 14:02Z.
- Orchard x_22c714e1/s24m4s/ + s24m4s.tar (24m4s upload; q/n deltas not overlaid), x_22c714e1/c_8de0c8b3/ (candidate kit copy) after review/overlay. Added by tree_rebuild21 14:43Z.
- Orchard x_22c714e1/s24m4t/ + s24m4t.tar, c_291c6f58/ (candidate); 1-18 W/w24s (superseded by w24t after review). Added by tree_rebuild21 15:10Z.
- Orchard x_22c714e1/s24m4u/ + s24m4u.tar, c_291c6f58u/ (candidate). Added by tree_rebuild21 16:26Z.
- W/w24x (killed 24m4x after 2 min, superseded by w24x2), W/w24w after 24m4x2 merges
- W/w24y (killed 24m4y after 9 min, superseded by w24y2)
- trinity-1-18 W/w24z3 (killed build 24m4z3 21:34Z, superseded by w24z4 per ORCH ANSWER 2132Z; 1.6 GB copy of w24z2)
- trinity-1-18 W/w24z5 (killed build 24m4z5 22:36Z, superseded by w24z7; 2.0 GB copy of w24z4)
- 2026-11-21 00:31Z tree_rebuild24: trinity-1-18 W/w24z8 (pinned kit qp_ee8c749b with escaped .py literals; superseded by W/w24z8b; package mirrored 2-28 n30_mirror/tree_rebuild23/tree_rebuild_b24m4z8_1075c5ab.tar). After the launch: W/w24z7 (superseded by w24z10; package mirrored), W/w24z9 (e3 harness superseded by w24z10 out/e3; package mirrored). Orchard X/s24m4z8b/ (1 file left after install), X/s24m4z8b.tar, X/s24m4z10e3/, X/s24m4z10e3.tar.
## tree_rebuild26 (2026-11-21T07:05Z; user runs deletions; nothing here is used by the launch 174085)
- trinity-1-18 W=/scratch/jjyeung/orch_n30/tree_rebuild10_w: w24z16 (copy of w24z13b; Codex z16 died on auth before writing), w24z16b (copy of w24z13b; dispatch failed on auth), w26jn6, w26jn6b, w26jn6c, w26jn6d, w26jn6e (superseded jn6 test dirs; final is w26jn6f), w26t, w26t2, w26t3, w26t4 (superseded jn5->jn6 harness runs, ~164 MB each; final is w26t5), work/s24m4z12a and work/s24m4z12a.tar (17.7 MB staging of the armed kits, now on Orchard).
- Orchard X=/project/community/jjyeung/okh7/x_22c714e1: s24m4z12a.tar (17.7 MB) and s24m4z12a/ (MANIFEST.sha + u/ left after the moves), a24m4z12/jn6_1076bfe9.sh and a24m4z12/jn6_4ed2704d.sh (superseded jn6 bytes), o/174081*, o/174082*, o/174083* (forced-refusal outputs; keep 174083 until the card is final).
- (08:20Z) trinity-1-18 W: w26trace (CPU trace workspace), w26fix (kit b44a4915, superseded by w26fix2 06d9a1b5; keep until 174101 passes its gate). Orchard X: t_7ec7c28925b4, t_34c11e8cc527, t_b47e5e2141d3 and the two later t_* test dirs (GPU settling tests; results copied to events/tree_rebuild/fix_rlimit and fix_spawn), s26fix_n_go.tar, s26fix2_n_go.tar, s26fix/ and s26fix2/ (empty after the moves), a24m4z12/n_3f55530c and a24m4z12/n_b44a4915 (superseded launch kits; keep until the run is judged), n_s/sess_174085.json (unused sessions of the cancelled job; n_ops10 decides).
- 2026-11-21T10:03:46Z fix3 subagent: trinity-3-30 /scratch/jjyeung/orch_n30/tree_rebuild27/work/fix3/{rd,ship1,ship2,pkt} and fix3/ship*.tar (about 45 MB, reading copies of the kit, tree and job records; everything needed is in events/tree_rebuild/fix_proc and on 1-18). trinity-1-18 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix/{t1,t3b,t3c,vt,ovl,ovl2} (test replicas, about 70 MB); keep w27fix/n_go, s27fix_n_go.tar, work/, packet/, src/, gpu_test/.
