# Cross-family re-review of EAT-1 after fixes (round 3)

You are the independent reviewer (GPT family); Claude-family lanes built and fixed EAT-1. Rounds 1 and 2 (GPT reviewers) returned NO-GO: R/REVIEW_VERDICT_EAT1.md (defects 1-16) and R/REVIEW_VERDICT_EAT1_R2.md (open defects plus N1-N10; round-2 probes copied to R/probes_r2/, written against the previous toy, so adapt them). The builder claims all are fixed; the rules now in force are in R/EAT1_READY.md section "Rules after two cross-family refute reviews". The main change is response value provenance (rule 1). You try to REFUTE the fixed kit. You fix nothing in the builder's tree.

## Rules
- Work only inside R = /scratch/jjyeung/orch_n30/b03_e2etest/work/review_eat1_r3 (writable; R/eat1 is a byte-identical copy of the kit, hashes in R/COPY_FILES.sha256). Everything else is read-only to you.
- No Git, no deletion, no GPU, no network, no ssh, no copies above 20 MB. No recursive grep/find/du/ls -R outside R. Read files under /data2 in bounded parts. Keep R under 200 MB.
- Python: /scratch/jjyeung/envs/p1cpu/bin/python. Tests: `cd R && PYTHONPATH=R EAT1_TMP=R/tmp /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest eat1.tests.test_eat1` (expected `Ran 25 ... OK`; the strace test needs ptrace, which your sandbox may forbid: report, do not retry). The round-1 planted variants are ported into R/eat1/toy/adversarial.py; new probes go under R/probes_r3/ only.
- The user's wording decides any dispute: quote it.

## User wording
- Brief /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/qs/03_e2e_acceptance_test.md, sections "Why" and "The test" (clauses A1-A6).
- User rulings /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b03_e2etest/20261116T1155Z_ORCH_NOTE_user_rulings_revsi_sft.md (4: "Unit conversion and number formatting are done by the MODEL in its CoT; constants are fine, but no reader, wrapper or post-processor converts or reformats answers for it"; 5: fixed math covers unprojection and printing head outputs as text only).
- USER 2026-11-16: "one end-to-end model whose CoT uses its own heads (no agent loop, no external tools; frozen towers inside the checkpoint are allowed; no fitted selector, rule table, guard or fallback outside the weights for anything we claim as the model)".

## Do
A. For each round-1 defect 1-16 and round-2 defect N1-N10: CLOSED or OPEN, with the evidence (the adversarial variant's report or your own probe, command and output).
B. Rule AGREE or REFUTE on each of the 10 numbered rules in EAT1_READY.md, against the quoted wording.
C. New holes: a reader that violates the wording yet PASSES, or a compliant end-to-end reader that FAILS (false failures matter: a rule no honest reader can meet is a defect). Give file:line and a probe under R/probes_r3/ with command and output. Keep to plausible readers our lanes would write, not obfuscation contests; state when a hole needs deliberate evasion, and whether claim_grade (strace) would catch it.

## Deliver
R/REVIEW_VERDICT_EAT1_R3.md, at most 40 lines: first line `VERDICT: GO`, `VERDICT: GO AFTER FIXES` or `VERDICT: NO-GO`; then the 26 defect statuses (compact), the 10 rule rulings (one line each), then numbered new defects with file:line, the wording violated, and the probe result. Only verified problems. End with the same text as your final message.
