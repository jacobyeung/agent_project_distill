<!-- recovered by seal_plan: transcript=71f94277 line=31955 utc=2026-11-14T14:40:49.077Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_TASK_continuation_readiness_statement.md heredoc_quoted -->
# ORCH task: continuation readiness of LEG-S1 from the checker's side

Job 169097 completed at 14:19:39Z (exit 0), final step 544, slot A saved. I intend to continue to step 1,000 with a second allocation as soon as the gates pass. The operator (orchard_cp2) is building the launch packet. From you, one RESULT of at most 25 lines:

1. What exactly `canary3_status: FAIL` in your deliveries means for an exact resume from a real slot: what was compared, what differed, and whether the production kit's resume path is the one that failed or a different one. Cite the record.
2. What the checker (bundle 026cb696) verifies on a real continuation, in order: which checks run before the trainer starts (on what inputs, CPU or GPU, how long), which run on the first one, two and three resumed steps, what each needs from the first allocation (the eight native rows you hold, the source-matched baseline, slot A's metadata), and who must act on a failed verdict and how fast.
3. What evidence exists today that a resume from a saved slot continues the same training state (optimizer, schedule position, data order, random state), and what remains unproven until the real resume. For each unproven item, how we would notice in the first steps, and what a silent failure would look like at the step-600 read.
4. Anything you must build or bind before the launch (for example a real baseline capture from the first allocation's last rows), done now on CPU without any Orchard call; ask the operator through its inbox for files only it holds.

No job, no ssh. Coordinate with the operator by inbox notes.