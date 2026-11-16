# Lane vsti_diag (Devin, runs on trinity-1-3): why step 544 trails f17 by 2-46 points on VSTI's relative types
Lane folder /scratch/jjyeung/orch_n30/vsti_diag. Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/vsti_diag/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. CPU only: no GPU, no Orchard submission, no Git, no deletion, no recursive search on /home or /data*.
## Question
Step 544's native VSTI-450 read (job 170294; events/native_r4/20261116T1610Z_RESULT_full_read.md; return in trinity-1-3 /scratch/jjyeung/orch_n30/native_r4/work/ret4/, report work/ret4/report_v1d/) answers camera_obj_rel_dist v1/v2/v3 at 42/54/70 and obj_obj_relative_pos lr/nf/ud at 94/62/76, against f17 80/88/84 and 94/96/96 and P1 m200 on the SAME items and frames. D0 trains from step 544, so a lost skill propagates. Find the cause from evidence.
## Do
1. Per item, pair native vs f17 vs P1 m200 (their per-item outputs are named in the read's comparator files, work/ret4/extra.py). Tabulate per type: answer distribution (option bias, e.g. always "near"), confusion against GT, CoT length and content class (states a measurement, cites frames, empty, refuses), and whether failures cluster by scene, frame count or question phrasing (VSTI's wording vs the training templates).
2. Read 15 failing items per worst type in full (CoT and answer). Name each failure's class.
3. Check training exposure: how many LEG-S1 / D0 rows of each matching type (dev records: D0_ROWS_ADMISSION_20261115.md, TRACE_RULING_20261115.md section 1a), and whether the trace ruling's direct-row grammar for these types differs from what f17 learned.
4. Price it: VSTI primary points lost per type; whether D0 or A2 rows already address it.
## Deliver
distill_design/VSTI_RELATIVE_TYPES_DIAGNOSIS_20261116.md (+ INDEX line; design-record format: question, answer, evidence, options rejected, what would settle it) and one RESULT (<= 20 lines) with the cause, its evidence and the cheapest fix; then exit. Questions or blockers only as events.
