# Lane review_h1read5 (Devin, runs on trinity-1-3): one short independent refute review of h1read kit fix round 5 (imports under python -I, logs in partial returns)
Lane folder: /scratch/jjyeung/orch_n30/review_h1read5 on trinity-1-3. Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_h1read5/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: you write only in your lane folder and your events folder, and you test in copies under your lane folder. No GPU, no Orchard call, no ssh, no copy above 20 MB, no Git, no deletion. You fix nothing and you do not talk to the builder. Time budget 45 minutes.

## What and why
The h1read kit (/scratch/jjyeung/orch_n30/cont_ops/work/h1read/, read only) is the reviewed direct reader; fix round 4 (FIX4.md, review GO in events/review_h1read4/) added a direct-types filter and partial returns. Orchard job 171112 ran the fix-4 filtered step-544 a7 read: staging passed, then the worker died in under a second with 0/1,781 items. Cause: production runs workers through p/vllm_isolated.sh = `python -I` (kit/launcher/orchard_launcher.py:232), which drops the script directory from sys.path, and fix 4 put `import read_filter` at kit/reader/worker.py:11 before the sys.path insert. The fix-4 fixtures ran without -I. Fix 4's partial pack also dropped logs/, so the return had no traceback (return unpacked in work/h1read/f171112).
Codex (GPT family; you are the cross-family reviewer) built fix 5. Builder brief: FIX_BRIEF_R5.md; report: FIX5.md; evidence/FIX5_* and tests named there.

## Do
Try to refute each of the following, with file:line evidence and a test in a copy where possible:
1. Every production entry point (worker.py for each family including a7 via x7.py, chain.py, orchard_job.py, trace_runtime.py, phase_b.py, report/merge modules the worker imports) imports cleanly under `python -I` from the packaged payload layout (the tree prepare writes, not the source tree with its symlinks; kit/reader/read_filter.py is a symlink in the source tree). Try `-I` on every entry point yourself.
2. The runtime fixtures and chain test now use the production `-I` wrapper, and would fail on the fix-4 code.
3. Partial returns carry bounded log tails within the caps, and identity/journals keep priority.
4. Plan bytes and plan_sha256 for unfiltered and filtered prepare equal fix 4's; no admission, binding, export, asset, parity or completeness check was weakened; all suites pass in a copy.
5. SHA256SUMS / FINAL_PINS cover every changed file, and nothing under kit/build/* changed.

## Deliver
REVIEW_VERDICT_H1READ5.md in the events folder: GO, GO AFTER FIXES (numbered, each with file:line and a failing test), or NO-GO; at most 30 lines. Also write a RESULT event (at most 15 lines). Then exit. Message the orchestrator only for blockers.
