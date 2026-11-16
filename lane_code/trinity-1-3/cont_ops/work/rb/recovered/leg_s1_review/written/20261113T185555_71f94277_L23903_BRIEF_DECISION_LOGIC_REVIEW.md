<!-- recovered by seal_plan: transcript=71f94277 line=23903 utc=2026-11-13T18:55:55.913Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_DECISION_LOGIC_REVIEW.md  -->
# Independent review: the comparison and decision code for a stop-or-continue ruling on a training run

You are an independent reviewer from a different model family than the author. This code turns item-level model answers into the comparisons that decide whether a training run (about 96 GPU-hours per day) continues at step 100. A wrong pairing, a wrong interval or a rule implemented differently from its registered text would produce a wrong decision with no crash.

## Material

- Code: `/scratch/jjyeung/orch_cd/legs1_reads/out/decision.py` (308 lines; its sha256 begins 2874d0a7 and must be unchanged; verify) and the files it imports from the same folder; `DEPENDENCIES.sha256`, `CELLS.json`, `DESIGN_RECORD.md`, `RUNCARD_M100_M200.md`, `REVIEWED_INTEGRATION.log` (test evidence by the author, not a review).
- The registered rules, which the code must implement and may not reinterpret: `/scratch/jjyeung/orch_cd/leg_s1_tree/out/PRELAUNCH_CARD.md`, section "Step-100 decision read" (lines 92 to 110); `/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md` (search it for "m100", "R1", "R3" and "ledger"; read only those passages); and the inbox note named in the card, `20261112T1035Z_ORCH_ANSWER_readout_rule_and_counts.md` (look for it in `/scratch/jjyeung/orch_cd/legs1_reads/inbox/` and `/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/`).
- Reference reads the code has already been run on, for a numerical cross-check: the parent's per-type results `/scratch/jjyeung/orch_cd/devs1_direct/out/r5/MERGE_RESULTS.md` (71.6436% on 1,375 primary items) and the parent stand-in reports in `legs1_reads/out/` (`PARENT_REPORT.log`, `PARENT_STANDIN.md`).

## Check, with file and line for every finding

1. **Loading and admission** (`load_merge`, lines 52 to 91): the item sets of the two arms must be identical and in the registered set; a missing, duplicated or extra item refuses rather than shrinking the comparison; refusals, cap hits and call errors stay in the denominator as wrong.
2. **Scoring.** The per-type metric (accuracy for choice types, the benchmark's mean relative accuracy for numeric types) is the registered one, applied identically to both arms; the aggregate is the registered aggregate over types, not a pooled item mean, unless the rules say otherwise. Say exactly what it is.
3. **Pairing and intervals** (`paired`, `comparison`, `aggregate`): the difference is computed per item on the same items; the bootstrap resamples the registered cluster unit (rooms or captures, not items), with the stated number of draws and a fixed seed; the interval is the percentile interval the rules name; a type with few clusters is handled as the rules say.
4. **The rules** (`direct_rules`, lines 125 to 154): "stop if route planning or another direct task trails f17 with the paired 95% interval wholly below zero" and R3 ("no direct-task deficit with an interval below zero on dev-S1 or dev 858, and at most one cap hit per 100 answers"): which types count as direct tasks, which comparator each rule uses (f17 or the parent), whether "wholly below zero" is implemented as the upper bound below zero, how untrained types are excluded and labelled. Any place where the code is stricter or laxer than the text is a finding.
5. **The report** (`write_report`, lines 216 to 300): every number in it traceable to the computation; the comparator, GPU type and token policy named; nothing presented as a decision that the rules call diagnostic.
6. **Reproduce.** From a private copy, run the code on the existing parent merge and confirm 71.6436% on 1,375 items and the per-type values in `MERGE_RESULTS.md`; recompute one paired comparison by an independent implementation of your own (a few dozen lines) and compare the point estimate exactly and the interval to within bootstrap noise.
7. **What is missing for the step-100 read.** The cut by the 47 development scenes that f17 saw is not implemented anywhere. State what a correct implementation must do (same paired machinery on the two strata, the registered aggregate kept whole), and what the list of 47 scenes must be bound to (`/scratch/jjyeung/orch_cd/init_audit/F17_EXPOSURE.md`).

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_DECISION_LOGIC.md`, at most 45 lines: first line **ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**; one line per item with evidence; findings by severity with the smallest fix; what you ran; what you did not check. If and only if the verdict is ACCEPT, also write `/scratch/jjyeung/orch_cd/leg_s1_review/DECISION_LOGIC_RECEIPT.json` with the verdict, your reviewer identifier and the sha256 of `decision.py`. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_decision_logic/` (private copies, at most 300 MB). No Git commands, no ssh, no network, no GPU, no agents, no deletion commands, and no names of deletion operations in any shell command text. Stay on `/scratch`; never read, search or list `/home` or `/data*`; no recursive search outside the folders named here. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
