# Lane review_k1fin (runs ON trinity-1-18): second reader for the K1 finalize step, before the first K1 GPU phase

Lane folder: /scratch/jjyeung/orch_n30/review_k1fin on trinity-1-18. Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_k1fin/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: read-only everywhere except your lane folder and events folder; no GPU; you fix nothing and do not talk to the builder. This is a short review: aim for 40 minutes.

## What you review
The K1 grounding test's kit refuses every GPU phase until its manifest carries two flags (production_ready, frame_staging_authorized), and no kit script sets them. Lane k1_ops3 had Codex write a finalize step, finalize_k1.py, that sets both flags only when six staging receipts pass, and fills frame timing for the ScanNet and ScanNet++ captures. If it sets the flags too easily, K1 runs on frames that are not the pinned ones.
- Builder's claim: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/20261115T2050Z_RESULT_finalize_v2.md and the folder finalize_v2/ beside it (CODE_DIFF.patch with finalize_k1.py and its tests, REPORT.txt, TEST_OUTPUT.txt, SHA256SUMS). Earlier context: 20261115T2009Z_RESULT_frames_staged.md, 20261115T2029Z_RESULT_codex_finalize_stopped.md and my rulings (*_ORCH_*.md) in the same folder.
- Working files, same node, read-only: /scratch/jjyeung/orch_n30/k1_ops3/ (work/codex_finalize_v2/, the kit copy, the staged manifest ada4797e..., the finalized manifest c3bbc378..., PARITY_FINAL.json, ACCEPT_MANIFEST.json, SUBSTITUTIONS_k6_replica.jsonl, WD_OUT, WA_OUT) and the kit /scratch/jjyeung/orch_cd/k1_build/work/kit_k1a (k1_pipeline.py check_manifest, k1_phases.py, INPUT_CONTRACT.md).

## Do this
1. From the kit's code alone, write down what check_manifest requires for phase tower_sam and for phase own, and what the two flags are meant to attest.
2. Diff the finalized manifest against the staged one yourself: the only differences may be the two flags, the receipts block and the timing fields of the 138 ScanNet and ScanNet++ captures. Anything else is a finding.
3. For each of the six gates, break its input in a copy (a wrong hash, a missing row, n_failures 1, a substitution row whose file does not hash to its pin) and run finalize_k1.py: both flags must come out false. Report the gate that fails to refuse.
4. Timing: for ten ScanNet or ScanNet++ captures recompute fps, timestamps and total frame count with the student reader's own function and compare; confirm the 162 ARKitScenes captures carry null timing and that the unchanged check_manifest then admits tower_sam and refuses own.
5. Confirm that no file of the kit under /scratch/jjyeung/orch_cd was changed by the finalize step (compare with the kit's own source pins).
Verdict in REVIEW_VERDICT_K1_FINALIZE.md in your events folder: GO for tower_sam, GO AFTER FIXES (file, line, failing input) or NO-GO; what you did not check. One RESULT event of at most 15 lines. Then stop.
