# Lane review_h1read4 (Devin, runs on trinity-1-3): one short independent refute review of h1read kit fix round 4 (direct-types filter and partial returns)
Lane folder: /scratch/jjyeung/orch_n30/review_h1read4 on trinity-1-3. Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_h1read4/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: you write only in your lane folder and your events folder, and you test in copies under your lane folder. No GPU, no Orchard call, no ssh, no copy above 20 MB, no Git, no deletion. You fix nothing and you do not talk to the builder. Time budget 45 minutes; the verdict is wanted by 00:15Z.

## What and why
The h1read kit (/scratch/jjyeung/orch_n30/cont_ops/work/h1read/, read only) is the reviewed direct reader. It produced the D0 m200/m100 and H1-1 m100 R0-dev (family a7) reads (jobs 170757/170786/170808). Its fix round 3 (reviewed GO in events/review_h1read3/) admitted the step-544 export (run 469ddece, mstop, 544).
- Job 170928 read step 544 on a7. Step 544 takes about 150 s per item on object_abs_distance and room_size_estimation (about 1 s elsewhere). The job was cancelled at 1,958/2,169 items and returned no journal.
- ORCH ORDER (events/cont_ops/20261117T2149Z_ORCH_ORDER_direct_types_only_filter.md) asks for two changes. (1) A type filter so that a read takes the direct types only (everything except those two routed types), recorded in the read identity, with unchanged denominators for the kept types. (2) A cancelled or timed-out read returns the journal of what it finished.
- Codex (GPT family; you are the cross-family reviewer) built the changes. Builder brief: FIX_BRIEF_R4.md; builder report: FIX4.md (diff summary, tests, operator commands); evidence/FIX4_* and tests named in FIX4.md.

## Do
Try to refute each of the following, with file:line evidence and a test in a copy where possible:
1. Without the filter, preparation (CONFIG, plan, payload bytes) and reader behaviour are byte-identical to fix 3. The existing suites pass in a copy.
2. With the filter, the excluded types are not generated. Every kept type has its full item set: a7 counting 385, size 293, direction 192/194/192, appearance 246, rel_distance 279 = 1,781. The filter is in CONFIG, plan_sha256 and the returned SPEC/SUMMARY, and excluded types never score as 0.
3. No admission, binding, export, asset, parity or completeness check was weakened. Completeness is relative to the kept set only.
4. The partial return path packs the finished journal on SIGTERM/SIGUSR1/failure within the archive cap and Slurm's kill-wait. It is marked incomplete, and unpack/fetch never present it as a final score.
5. SHA256SUMS / FINAL_PINS cover every changed file, and nothing under kit/build/* changed.

## Deliver
REVIEW_VERDICT_H1READ4.md in the events folder: GO, GO AFTER FIXES (numbered, each with file:line and a failing test), or NO-GO; at most 30 lines. Also write a RESULT event (at most 15 lines). Then exit. Message the orchestrator only for blockers.
