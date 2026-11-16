# Lane review_c5 (runs on trinity-1-3): confirmation review of contracts packet revision 5

Lane folder: /scratch/jjyeung/orch_n30/review_c5 on trinity-1-3. Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_c5/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: read-only everywhere except your lane folder and your events folder; copy what you need to test into your lane folder. No GPU, no Orchard call, no copy above 20 MB, no Git, no deletion. You fix nothing and you do not talk to the builder.

## What and why
The contracts packet patches the serving contracts (geometry calculator, candidates, 3D box) of the next training leg's tree; a wrong contract trains the student on wrong programs. Revision 4 was reviewed: ACCEPT AFTER FIXES (/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_contracts2/REVIEW_VERDICT_CONTRACTS_R4.md: H-1 box_v313.py:519, H-2 calculator.py:239, M-1, M-2, lows, surviving mutants). The builder (Codex) delivered revision 5: claim in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/contracts_rebuild/20261116T0142Z_RESULT_r5_interdiff_ready_for_check.md; packet on this node under /scratch/jjyeung/orch_n30/contracts_rebuild/out (INTERDIFF_R4_TO_R5.diff, 957 lines, sha256 9eb02819...; INTERDIFF_R4_TO_R5_PATCHES.diff; CONTRACTS_REPORT_R5.md; MUTATION_R5.json; the patches and apply_contract_patches_r5.sh). Your scope is the interdiff: whether revision 5 fixes what revision 4's review found and adds no defect. Do not re-review what revision 4's review accepted.

## Do, forming your own view from the interdiff before reading the builder's report
1. For each finding of the r4 verdict: fixed, not fixed, or fixed with a new defect, with file and line.
2. H-1: is there any path on which a stored trace of the sealed epoch replays under the new contracts, or a new-epoch trace under the old ones?
3. H-2: after the change, does any printed output or decoded value still depend on a reference-camera heading when a heading is unavailable? Is the private camera basis deterministic, and does it read nothing the student could not have at serving time?
4. M-1 and M-2: one resolver on all three call sites with the stated precedence; rerender and the strict comparison.
5. The four mutants claimed equivalent (R4, N7, N3, R5): for each, try to construct a reachable input that tells mutant from original; R5 above all.
6. L-2c removes the bare-gap parser, which defers the legacy_surface absolute-distance family when the contracts are on. Check with your own query over the builder's real-row audit that no real row needs it and that the runtime cannot emit a bare gap.
7. If the builder's test environment on this node is usable read-only: apply the packet to a fresh copy of the sealed tree in your lane folder, run the suite, and confirm a second application is refused.
8. Legality: no patch reads ground truth, an answer bank or a benchmark item at serving time.

## Verdict
Write REVIEW_VERDICT_CONTRACTS_R5.md in your events folder: CONFIRMED, CONFIRMED AFTER FIXES (each fix with file, line and why it matters) or NOT CONFIRMED; what you read and what you did not; each builder claim you could not confirm. Then one RESULT event of at most 20 lines. Then stop.
