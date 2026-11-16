# Lane amend3_reg (Claude Fable subagent on trinity-3-30): rule on and register the three amend3 drafts as the orchestrator's delegate
Read B/tools/CLAUDE_LANE_RULES.md first (B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30). Events folder: B/events/amend3/. Local folder /scratch/jjyeung/orch_n30/amend3 (exists).

## Why
Three drafts wait for registration: re-freeze amendment 3, the next-leg init rule, and the trace ruling 2.2 evidence line. A pre-registration only counts if it lands before the outputs it governs: the K1 own phase is being rerun today (its outputs may exist from ~13:00Z) and the D0 step-200 verdict arrives ~18:00-19:30Z; the init rule must be registered before that verdict is used for anything but the stop rule.

## Read
B/events/amend3/20261116T0643Z_RESULT_amend3_drafts.md, STATUS.md and the three DRAFT_*.md there; the review verdict B/events/review_a0d/REVIEW_VERDICT_A0_DESIGN.md; in /data2/jjyeung/agent_project_data/distill_design/: A0_AFTER_NATIVE_READ_DESIGN_20261116.md, REFREEZE_PREREGISTRATION_20261115.md, REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md, REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md, D0_STOP_RULE_20261116.md, TRACE_RULING_20261115.md, NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md, POLICY_AUDIT_20261115.md. Read files whole only when short; search with bounded commands on named files.

## Do
1. First check whether any K1 own-phase output or table exists yet (B/events/k1_ops3/ newest RESULT; do not ssh). Write that fact into amendment 3.
2. Source the numbers the drafter could not (metre items among the 790 dev-S1 distance items and the resulting half-width; step 544's dev-S1 direct-type mean; whether the 80 rooms belong to step 544's pool; GPU-hours for D1'); where a number cannot be sourced from files you can read, say so and choose a rule that does not depend on it.
3. Decide each open choice (D1' or no decision; the metre item set; the floor value and whether appearance order counts; the cutoff option; whether m600 and m800 become candidates) with a one-paragraph reason each, preferring rules that cannot be tuned on benchmark items and that keep held-out claims clean.
4. Register: write the final texts as records in distill_design (REFREEZE_AMENDMENT_3_<topic>_20261116.md, NEXT_LEG_INIT_RULE_20261116.md), each with its sha256 and UTC registration time inside, plus one INDEX.md line each; apply the 2.2 evidence-line change to TRACE_RULING_20261115.md in place (current state only, no history narration) and note it in its INDEX line. Register amendment 3 first, and as early as possible.
5. Return at most 15 lines: each choice and its reason in one line, paths and sha256s, anything only the user can decide.
