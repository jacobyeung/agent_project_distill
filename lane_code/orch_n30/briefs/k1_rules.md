# Lane k1_rules (runs ON trinity-1-18): re-register the K1 decision rules that were lost with trinity-2-18

Lane folder: `/scratch/jjyeung/orch_n30/k1_rules` on trinity-1-18. Events folder: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_rules/`. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md` and obey it. You use no GPU, start no copy and need no ssh. You change nothing outside your lane folder and your events folder: not the kit, not a record, not INDEX.md.

## Why
K1 is step P1 of the pre-registered re-freeze of the routed reading path (a grounding kill test on 300 eligible captures plus a selector refit). Its decision rules were the file `b6_build/out/K1_RULES.json` (sha256 cb0aadee89c86e3db41c33d450eee6d7f58558d63f56d3d189e744277ad23269), written before any K1 output and referenced by the pre-registration. That file, `RUNCARD_K1.md` and `PROOFS.md` existed only on trinity-2-18, which is down; lane recover_map2 searched every surviving store and found no copy (`.../orch_n30/events/recover_map2/20261115T1714Z_RESULT_k1_inputs.md`). No K1 GPU phase has run (lane k1_ops3 on this node: `.../orch_n30/events/k1_ops3/STATUS.md`).

The orchestrator's ruling: re-register the rules from the registered text, with every field traced to a surviving source, under a dated amendment adopted before any K1 GPU output exists. If trinity-2-18 returns before K1's GPU phase starts, the original file is used and the amendment is void. The point of the registration is that the marks are fixed before the data is seen; your job is to keep that true and to make every choice visible.

## Sources (read in bounded parts)
- `/data2/jjyeung/agent_project_data/distill_design/REFREEZE_PREREGISTRATION_20261115.md` and `.json` (look at `/k1_rules_relation` and `/inputs`).
- `/data2/jjyeung/agent_project_data/distill_design/B6_GROUNDING_DESIGN_20261115.md` (K1's definition; the kill rules are near lines 184 to 200; brief B6-A).
- `/data2/jjyeung/agent_project_data/distill_design/POLICY_AUDIT_20261115.md` where a rule cites it.
- On this node's local disk, read-only: the kit `/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a` (every file that reads K1_RULES.json, RUNCARD_K1.md or PROOFS.md, every pin of them, the tests) and `/scratch/jjyeung/orch_cd/k1_ops`. You may `grep -r` inside those two folders only.

## Tasks
1. From the kit's code, write down the schema the consumer expects: keys, types, how each value is used, and what the code does when a key is missing.
2. Write the candidate `work/K1_RULES.json` in that schema, and `work/K1_RULES_PROVENANCE.md` with one row per field: value; source (record path and line, or kit file and line); status `registered` (the value is stated in a record or kit text written before 2026-11-15T10:00Z), `derived` (follows from registered text by arithmetic you show), or `new` (no surviving source: give the value you chose, why, and the alternatives). Tune nothing on data and look at no model output.
3. For RUNCARD_K1.md and PROOFS.md, say whether code pins or reads them. If it does, write replacements that contain only what the records state and what was verified today, and that say in their first line that they replace lost originals.
4. List every place that pins the lost files' hashes (kit code, manifests, bootstrap pins, the pre-registration JSON) and the step that regenerates each.
5. Order the independent review yourself, as the orchestrator's order, with a Codex dispatch of preset `review` (`--model gpt-6-astra --effort high`, read-only). Its brief must say, in this order: derive the K1 pass and kill marks on your own from the two design records before opening the candidate; then compare with the candidate field by field; attack every row of the provenance table, above all `derived` and `new` rows; load the candidate with the kit's own loader on CPU if one exists; verdict ADOPT, ADOPT AFTER FIXES or REJECT with reasons, written to a file in your lane folder. Apply fixes it demands and have the same reviewer confirm once.
6. Draft `work/REFREEZE_AMENDMENT_1_20261115.md`: what was lost and how the loss was established; what replaces it; the sha256 of the new K1_RULES.json; every `new` or `derived` field; the evidence that no K1 GPU output existed when the amendment was written; the void clause; the pin changes from task 4. The orchestrator adopts it and edits the records; you do not.
7. Write one RESULT event: the candidate's sha256, the counts of registered, derived and new fields, the reviewer's verdict, and the pin locations. Copy the candidate, the provenance table, the review verdict, the amendment draft and any replacement documents into your events folder. Then stop.

If the kit code shows that a rule needs a value that no record states and that could change K1's verdict, say so in a QUESTION event with your proposed value as the default, and continue.
