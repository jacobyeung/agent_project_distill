# n_ops12 STATUS (successor resumes from this file alone)
Updated 2026-11-22T03:41Z n_ops12 (headless Claude Opus, trinity-3-30, brief B/briefs/n_ops12_c.md), started 02:46Z 2026-11-22. Start RESULT 0247Z posted. Rotate due ~10:46Z (write _RESULT_rotate by 10:46Z; killed ~12:46Z).
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. X=/project/community/jjyeung/okh7/x_22c714e1. MON=/scratch/jjyeung/orch_n30/n_ops1/work/mon. AUTO=/scratch/jjyeung/orch_n30/n_ops9/work/auto. Predecessor status: n_ops12/STATUS_n_ops11.md.
## Job 174246 (a15_cot_apb2edfac4, orchard-community-3, kit 7e23bbdd, jn7.sh 98edfd9e, sessions X/n_s/sess_174246.json 5570aa81)
- WAITING_REVIEW since 02:10:50Z; deadline 04:10:50Z (job exits by itself if no review.json).
- review.json held at n_ops12/inbox/review_174246.json sha256 476d17bdba5b5aebab848ef6537d4323260c0f53b55879b8fbc79ca0bfe1a4c6 (= n_review1k source). NOT installed.
- Install ONLY at the minute an ORCH ANSWER names (RULING 0248Z, ORDER 0226Z): fresh MON/hist.txt line, sleep 62, then
  bash AUTO/install_review.sh /scratch/jjyeung/orch_n30/n_ops12/inbox/review_174246.json  -> X/n_r/review.json
- RULING 0248Z: option H (two symlinks in rp by tree_rebuild29) needs rehearsal PASS + n_review1k GO + ORCH answer; if not both in by 03:45Z nothing is written, job ends 04:10:50Z.
## Owed after install
- 1-min checks through model load (~9 min) and first steps; record step time, first checkpoint/export, upload rate vs 55 MB/s, GCS readback; one RESULT; main notice INBOX_TO_NONTRAINING_ORCHESTRATOR_*.
- Failure after training starts: BLOCKER at once with stage + last lines; fetch publishers' output.
- Sessions for any new job: see STATUS_n_ops11.md "Sessions for a resubmission" (n_ops10/work/sess2.sh).
## Log
- 02:47Z start RESULT; watch healthy (nops_mon, nops_auto), hk.log empty, /project 159 GiB free.
- 02:50Z n_review1k GO on RULING 0248Z item 2. 03:01Z tree_rebuild29: rehearsal H run2 loaded init on ranks 1-3, first step began, budget hit; run3 started 03:00Z.
- 03:19Z tree_rebuild29: rehearsal H PASS (two steps, four ranks, finite; 239 s/140 s; peak 80 GB). Awaiting ORCH answer + links + named minute.
- 03:26Z ORCH ANSWER GO: install review.json the minute tree_rebuild29's RESULT says LINKS OK with hashes = pins 1de983c9/e72208ac; not on FAILED; not after 04:05Z. Then 1-min checks; first-steps RESULT must cover routing loss vs P (job 172660 log near step 400), memory alloc/reserved at steps 1,2,10, step time vs P.
- 03:28:03Z INSTALLED X/n_r/review.json 476d17bd (RESULT 20261122T0330Z). 03:29:21Z training_start: 4 u.py ranks, t.log created. Owed: first-steps RESULT, main notice.
- 03:39Z all 4 ranks logged init_artifact (step 400, 508 head tensors); 03:41Z GPU mem 39-45 GB, no errors.
