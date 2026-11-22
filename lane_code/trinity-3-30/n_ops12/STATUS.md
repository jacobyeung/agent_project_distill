# n_ops12 STATUS (successor resumes from this file alone)
Updated 2026-11-22T05:09Z n_ops12 (headless Claude Opus, trinity-3-30, brief B/briefs/n_ops12_c.md), started 02:46Z 2026-11-22. Start RESULT 0247Z posted. Rotate due ~10:46Z (write _RESULT_rotate by 10:46Z; killed ~12:46Z).
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. X=/project/community/jjyeung/okh7/x_22c714e1. MON=/scratch/jjyeung/orch_n30/n_ops1/work/mon. AUTO=/scratch/jjyeung/orch_n30/n_ops9/work/auto. Predecessor status: n_ops12/STATUS_n_ops11.md.
## Job 174246 (a15_cot_apb2edfac4, orchard-community-3, kit 7e23bbdd, jn7.sh 98edfd9e, sessions X/n_s/sess_174246.json 5570aa81)
- ENDED: FAILED 03:44:23Z (1:0) at the step-1 checkpoint: check_space needs 6,027,674,886,604 B disk plan vs 5,717,540,712,448 free on node /tmp. BLOCKER 0347Z. Evidence n_ops12/work/fail_174246/ (o.tar f459fc83, x/, extra.out.034658). Record distill_design/N_174246_CKPT_DISK_PLAN_20261122.md. Main notice 034918Z sent (job ended).
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
- 03:44:13Z 174246 FAILED at first checkpoint disk check (see top). 03:47Z BLOCKER posted (copies tree_rebuild29, n_review1k inboxes). 03:49Z main notice. Routing loss vs P closed: P 172660 node_hist (r1_ops6/work/mon) 2.9e-5..7e-5 near steps 380-420, same order as rehearsal.
## Owed now
- Wait for ORCH answer; sessions for any new job (SESS_JOB in n_ops12/inbox; procedure in STATUS_n_ops11.md "Sessions for a resubmission"; tools n_ops10/work/sess2.sh + ycheck). Watch: nauto/nops_mon keep running; MON/job still 174246 until nauto switches to a new advanced job.
- 03:48Z ORCH ORDER: tree_rebuild29 takes the disk plan apart + builds one kit (H links in kit, preflight disk check, jn8.sh holds pre-first-checkpoint exits, rehearsal does a save). Reviewer now n_review1l (inbox /scratch/jjyeung/orch_n30/n_review1l/inbox). 03:5xZ my item-2 RESULT posted; main follow-up note (new job in some hours). Next: sessions for the new job when SESS_JOB arrives; then 1-min watch through the first save.
- 04:09Z ORCH RULING: kit option (a) exports only at milestones 100 and 200, full-state interval stays 7,200 s. Watch note: n_ops1/work/parse.py flags NO_EXPORT_m<t> for t in (100,200,400,600,800,1000) 45 min after step t+1, so for the new job it raises a false NO_EXPORT_m400 ~45 min after step 401. Adjust the list (with tests/run_tests.py + replay) before step 400, or ignore the flag.
- 04:59Z RESULT /project free falling (0.25-0.6 GiB/min); 05:07Z ORCH ORDER: not ours (tree_rebuild29 ~20 MiB); 05:10Z RESULT items 2-3: no new writer of ours visible; old removal list marked SUPERSEDED (user list = USER_free_orchard_space_20261121.sh). Default: post again if free <60 GiB or >0.5 GiB/min for an hour.
