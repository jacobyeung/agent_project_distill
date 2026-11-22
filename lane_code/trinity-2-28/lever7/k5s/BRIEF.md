# Brief: K5-S analysis (CPU only), lane lever7 on trinity-2-28
Rules: read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md; obey both. No Git, no SSH, no GPU, no copy to/from /home or /data* (reading named files there is fine; no recursive find/grep/du/ls -R on /home or /data*). Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first (you need none). A child process that dies must leave its cause in a log. Work only in /scratch/jjyeung/orch_n30/lever7/k5s. Python: /scratch/jjyeung/envs/p1cpu/bin/python -I -B (numpy, scipy available? check; else /usr/bin/python3).

## Task
Implement exactly the registered analysis in /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md section "Tower instability as a sign of tower error (K5-S)" (read only that section, lines ~278-287). Do not change its definitions; if one cannot be implemented as written, say so in the report and use the nearest faithful choice, named.

Inputs:
- K5 returns: /scratch/jjyeung/orch_n30/lever6/k5b/ret/g0, g1 (arms A1, D1 in job 0; A2, D2 in job 1). Parse them with the scorer's own loaders and compare() in /scratch/jjyeung/orch_n30/lever6/k5b/kit/score_k5.py (import or copy those functions; cite lines). Kit docs: kit/REPORT_K5.md.
- Audit classes and fits: /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json (38 captures, 'rigid_fit', 'alignment_pass'); the audit's fit code and GT pose source are in /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild (REPORT*.md name the scripts) and the record /data2/jjyeung/agent_project_data/distill_design/TOWER_CAMERA_FAILURES_20261120.md. Gross = rigid rotation max > 60 deg; pass = the audit's pass rule (translation RMS <= 0.10 m and every anchor rotation <= 5 deg); moderate = the rest.
- Error of A1 against GT: reuse the audit's own rigid-fit function on A1's metric cameras ('cm') against the GT anchor poses the audit used (same anchors, same convention). Before using it, check the function reproduces the audit's recorded rigid_fit numbers when fed the cameras the audit used (if those are available); report that check.
- Map K5 captures to the 38 by capture id (K5's record ids; see REPORT_K5.md and kit/3.json or 1.json).

Outputs in /scratch/jjyeung/orch_n30/lever7/k5s/:
- k5s.py (the analysis), K5S.json (all numbers), K5S.md (<= 60 lines: per-capture table: dataset, id, audit class, A1-class, A1 translation RMS and rotation max vs GT, disagreement rot deg and trans m; Spearman with each error; AUCs gross vs pass, moderate vs pass, gross+moderate vs pass, pooled and per dataset where both classes exist, each with a 10,000-draw capture bootstrap 95% interval, seed 0; A2-vs-D2 replicate agreement; the registered reading applied as written to the primary AUC). AUC convention: probability a random gross capture has a larger disagreement than a random pass capture, ties counted half.
- Also add one row: the same AUCs with the disagreement measured by the secondary metric.
- Also a short line: the share of the K5 tail (captures with primary disagreement > 3.9 deg, the p90) by dataset over all 84 K5 captures.
- tests: a tiny synthetic test of the AUC and bootstrap (perfect separation -> 1.0; reversed -> 0.0); log to tests.log.
Final reply: under 15 lines: the primary AUC with interval, the verdict as registered, n per class, and any deviation from the registration.
