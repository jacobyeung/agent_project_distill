# Lane k1_ops5 (runs on trinity-1-18): successor of lane k1_ops4, operator of the K1 grounding kill test

Lane folder: the predecessors', /scratch/jjyeung/orch_n30/k1_ops3 on trinity-1-18. Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/ (write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are an operator: code changes go to Codex as the rules describe.

## Why
K1 is the grounding kill test of the re-freeze: it decides whether routed programs keep the frozen SAM 3 tower for grounding or the student's own grounding. Phase tower_sam is complete (300 of 300 captures, verified, mirrored). What remains: the own phase (the student's own grounding on the same 300 captures, on Orchard), convert, tables on the frozen 296-capture set, the refit, the report.

## Start
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/STATUS.md (section "Now" numbers your steps) and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/20261116T0542Z_RESULT_rotate.md. Then my rulings in that folder, newest first: *_ORCH_RULING_part_b_four_points.md (manifest v2, config and receipt, naming exemption, rehearsal on trinity-1-3, one review, submission only on my GO), *_ORCH_ORDER_part_b_package.md, *_ORCH_RULING_refit_inputs_recovered.md, *_ORCH_GO_gtset_after_fixes.md; amendments 1 and 2 under /data2/jjyeung/agent_project_data/distill_design/ (REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md, REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md); decode rates in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r2/20261116T0515Z_RESULT_decode_times.md.
In flight from your predecessor, to wait for and never duplicate: Codex build k1_partb2 (workspace k1_ops3/work/partb/build, receipt codex_runs/20261116T054104Z_k1_partb2) and the governed pull k1_ops4_meta (tmux k1meta; rename its record when it ends, as STATUS.md says).

## Do
1. Finish the Part B package on my four rulings: v2's sha256 into amendment 2 before any own output exists; the namespace rehearsal on trinity-1-3; the bundle upload; one RESULT event with the v2 script, the diff against the native read's wrapper, the rehearsal output and the lines no rehearsal executes. I order one reader on that event.
2. Tables on v2: k1_downstream.sh pins the manifest to 91a2dbf9. Change that one line to v2's path and sha256, keep the assertion that the 300 capture entries equal v1's, and include the change in the same RESULT for the reader.
3. Submit nothing to Orchard without my GO naming the job. Orchard general runs one job per user; D0's CPU proof (job 170109) holds it until between 06:00 and 09:30Z.
4. Card 4 of this node is released by K1. Lane trin_read2 will use it for a reader proof from about 06:40Z; touch no GPU.

## Limits
No Git, no deletion, no paid key. Checks at most every 5 minutes while something runs. Your session ends after 5 hours: write a RESULT event named rotate, with STATUS.md exact, before then or at 60% of your context.
