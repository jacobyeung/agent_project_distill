# Cross-family refute review of EAT-1 (end-to-end acceptance test): clause definitions and allowlist

You are the independent reviewer (GPT family). EAT-1 was built by Claude-family lanes. You try to REFUTE it. You fix nothing in the builder's tree.

## Rules
- Work only inside your current directory R = /scratch/jjyeung/orch_n30/b03_e2etest/work/review_eat1 (writable; it holds a byte-identical copy of the kit in R/eat1, hashes in R/COPY_FILES.sha256). Everything else is read-only to you.
- No Git, no deletion, no GPU, no network, no ssh, no copies above 20 MB. Never run a recursive grep/find/du/ls -R outside R or outside /scratch/jjyeung/orch_n30/b03_e2etest. Read named files only; read files under /data2 in bounded parts.
- Python: /scratch/jjyeung/envs/p1cpu/bin/python (torch cpu). Tests in your copy: `cd R && EAT1_TMP=R/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1` (expected `Ran 16 ... OK`). Write any new test or probe under R/probes/ only. Keep R under 200 MB.
- The user's wording decides any dispute: quote it.

## Read first
1. The brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/qs/03_e2e_acceptance_test.md (sections "Why" and "The test" are the clause definitions A1-A6).
2. User rulings: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b03_e2etest/20261116T1155Z_ORCH_NOTE_user_rulings_revsi_sft.md (ruling 4 and 5: fixed math covers unprojection and printing head outputs as text only; any unit conversion or answer reformatting outside the model fails; constants are fine).
3. USER 2026-11-16 (lane brief): "the goal is one end-to-end model whose CoT uses its own heads (no agent loop, no external tools; frozen towers inside the checkpoint are allowed; no fitted selector, rule table, guard or fallback outside the weights for anything we claim as the model)".
4. R/EAT1_READY.md (what was built, plus the 10 interpretation points under "For the refute review"), then the kit R/eat1/: run.py, hook.py, scan.py, allowlist.json, closure.py, artifact.py, toy/, tests/test_eat1.py, adapters/. Baseline reports R/BASELINE_C8R.md, R/BASELINE_A2_TREE.md, R/EAT1_ON_B04_TINY.md for context only.
5. Optional context: /data2/jjyeung/agent_project_data/distill_design/ARCHITECTURE_CURRENT.md (bounded reads).

## Do
A. Rule on each of the 10 interpretation points in EAT1_READY.md: AGREE or REFUTE against the quoted user wording, with the reason.
B. Try to refute each clause's implementation (A1-A6): find a reader that violates the user's wording yet PASSES, or a compliant reader that FAILS. Give file:line evidence, and where possible a planted toy variant under R/probes/ that demonstrates the hole by running EAT-1 on it (state the command and output). Priorities: A2 token provenance (can a Python-side rewrite of the sequence or a prompt rebuild slip through?), A3 scanner holes (tables loaded by a non-obvious API, constants hidden in defaults/kwargs/config objects, thresholds via comparisons not caught, unit conversion via an allowed op), A4 guard/fallback detection, A1 file-open coverage (mmap, subprocess, os.open, C extensions), A5 (i)/(ii) eligibility logic.
C. Check the allowlist (eat1/allowlist.json) against ruling 5: anything allowed that performs unit conversion or answer reformatting is a defect.

## Deliver
Write R/REVIEW_VERDICT_EAT1.md, at most 40 lines: first line `VERDICT: GO`, `VERDICT: GO AFTER FIXES` or `VERDICT: NO-GO`; then the 10 point rulings (one line each); then numbered defects, each with file:line, the user wording it violates, and the probe/test that fails or passes wrongly. Only verified problems; no style comments, no fix designs beyond one clause. Then end with the same text as your final message.
