# Fresh review of the GTC registration and kit (lane lever6, trinity-2-28). Read-only; write one report file.

Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU (CUDA_VISIBLE_DEVICES=''), no deletion, no edit of kit files.
- No recursive grep/find/du/ls -R on /home or /data*. Write only /scratch/jjyeung/orch_n30/lever6/gtcrev2/REVIEW_GTC2.md (and scratch copies under lever6/gtcrev2/tmp if a test writes files). Python: the kit's interpreters, nice -n 10, threads <= 8.
- Do not compute, print or look at any cell value, score or difference (a, e, t, s). Tests that assert equality without printing values are allowed.

## Files (nothing else is needed)
- The ruling: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever/20261121T1939Z_ORCH_RULING_mask_source_run_the_dev_side_gt_seeded_carry_as_a_new_registered_experiment_k1_resume_waits_for_the_user_r0_pair_2.md (item A only).
- The registration: section "Rank 1 follow-up (GTC)" of /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md (lines 219-231; also read the rank 1 entry lines 201-218 and the plan's rank 1 reading at line 50 for conventions).
- The kit: /scratch/jjyeung/orch_n30/lever6/gtc/kit (REPORT_GTC.md, gtc_common.py, frames.py, seeds.py, track.py, relift_t.py, launch_gpu.sh, tests/), its outputs lever6/gtc/out (FRAMES_GTC.json, SEEDS_GTC.json), SHA256SUMS_GTC in lever6/gtc.
- The reviewed relift code it wraps: /scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py and its review lever5/r1x/REVIEW_X.md.
- K1's carry kit for the s seed rule and the carry rule: /scratch/jjyeung/orch_n30/sb_cachk/kit_v2 (mc_seeds.py, mc_tracker.py, mc_track_pass.py).

## Criteria (verdict GO or NO-GO, file:line for every defect)
1. The arms match the ruling: t seeded with the GT mask on the first visible served frame and carried over the served frames; s with the best served mask by K1's S_A0 rule; a and e recomputed exactly as the banked read; all relifted by relift.py's unchanged path inside dump 174135, paired on the same 117 items.
2. Nothing selects items, captures, seeds or frames after seeing results; the bars, the seed-size guard and what each outcome builds are fixed in the registration and are consistent with the plan's conventions (bootstrap: 10,000 draws, seed 20261120, physical room, item weighting).
3. The statistics are computed as registered: t - a and s - a with the room bootstrap, the share of e - a, per-frame precision and recall against the bound GT instance per dataset, the >= 200-pixel seed subset.
4. Masks reach relift on the same (32,240,320) grid and anchor order as cells a and e; the resize round trip is right; the carry rule matches K1's.
5. Frame inputs are the served anchors (binding hash reproduced); no stream is needed; the GPU launch follows the rules (two nvidia-smi readings 5+ min apart, vnice off trinity-0-13, timeout, no rerun after a kill, results to /scratch).
6. Tests exercise t == e and t == a and s == a/e on the real dump without printing values; run them if they take under 15 min; check SHA256SUMS_GTC.

## Output
REVIEW_GTC.md (<= 50 lines): first line `VERDICT: GO` or `VERDICT: NO-GO`; a line per criterion; blocking defects with the smallest fix; non-blocking notes. If a hook blocks writing the file, give the content in your final message. Final message: verdict and blocking defects only.

## This is the second review, after a fix
A first review (lever6/gtcrev/REVIEW_GTC.md) found one blocking defect, B1: relift_t.py did not compute the registered seed-size subset. The fix: lever6/gtcfix/BRIEF_FIX.md, FIX_NOTES.md, pre-fix copies beside them; the plan section now states the subset's membership rule. Judge all six criteria again on the current kit, and add:
7. The subset membership, its statistics and the verdict field implement the registration exactly (bars, guard, the first bar on all 117 items decides), with tests covering every branch; nothing in the fix touches track.py, seeds.py, gtc_common.py, frames.py or launch_gpu.sh (compare SHA256SUMS_GTC with the pre-fix copy).
The tracker's GPU output may already exist under lever6/gtc/out/track; do not open it.
