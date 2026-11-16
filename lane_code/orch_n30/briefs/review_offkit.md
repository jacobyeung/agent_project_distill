# Lane review_offkit (Devin, runs on trinity-3-30): one cross-family refute review of the official read kit (offkit) and direct re-bind (build R)
Lane folder: /scratch/jjyeung/orch_n30/review_offkit on trinity-3-30. Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offkit/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: read-only except your lane folder and events folder; test in copies; no GPU, no Orchard call, no copy above 20 MB, no Git, no deletion. You fix nothing and you do not talk to the builder.

## What and why
Lane b07_offread built (with Codex Astra, GPT family; you are the cross-family reviewer) the scoring layer that every official read will use: offkit (scorer, binding, report, adapters, frames.py guard) and build R, a direct-only re-bind of the reviewed kits f42aa1a4 / ea1a1b2d to a D0 export. It touches scoring, so one independent review is required before any read uses it. Builder's RESULT: events/b07_offread/20261116T1233Z_RESULT_rebind_ready_review_request.md. Code: /scratch/jjyeung/orch_n30/b07_offread/ on this node (kit/, builds/R/out/REBIND_READY.md, package_vsi.tar ddf11fd2, package_revsi.tar ef31d64f). Project rules: user rulings of 11:55Z in events/b07_offread/*_ORCH_NOTE_user_rulings_revsi_sft.md (ReVSI first; frames a parameter; the reader never converts or reformats an answer).

## Do
Try to refute each, with file:line evidence and a test in a copy where possible:
1. report.py aggregation: per-category means, overall averages, CIs and their pairing match the official VSI-Bench and ReVSI definitions; reproduce 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4] from the stored step-544 predictions yourself.
2. label_report: reader labelling (direct / harness / e2e, claimed vs unclaimed) cannot mislabel a harness-served read as a claimed one.
3. bind.py: freeze, EAT-1 and K1 binding; an export can only be bound with its own init-selection JSON and closure.
4. frames.py: 32-duplicate vs 64-spread guard matches each export's training layout; an override cannot silently change the layout.
5. Build R's reporter float-order correction changes no score beyond float rounding.
6. Any answer conversion, unit rewriting or reformatting anywhere in the path (must be none).
## Deliver
REVIEW_VERDICT_OFFKIT.md in the events folder: GO, GO AFTER FIXES (numbered, each with file:line and a failing test), or NO-GO; at most 40 lines; plus a RESULT event (at most 20 lines). Then exit. Message the orchestrator only for blockers.
