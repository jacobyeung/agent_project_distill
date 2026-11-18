<!-- recovered by seal_plan: transcript=71f94277 line=28639 utc=2026-11-14T04:31:20.274Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_MILESTONE_STEP_SET_CONFIRMATION.md  -->
# Confirmation review: one milestone step set across the evaluation read chain (patch MILESTONE_STEP_SET_20261114T0428Z)

You are an independent reviewer from a different model family than the author (a GPT-family lane). The patch changes code that packages, admits and reports the milestone evaluation reads of a training run, including the decision reader whose output the orchestrator rules on. Earlier reviews accepted the previous versions; this review confirms the patch only. Do not redo the earlier reviews.

## Background (what was accepted before)

- The decision reader `decision_fork.py` at sha256 fb2796c5... (receipts in `/scratch/jjyeung/orch_cd/leg_s1_review/`: `DECISION_RECEIPT.json`, `DECISION_RECEIPT_ADDENDUM_86c91ea8.json`, `DECISION_RECEIPT_RULING4_fb2796c5.json`). A copy of that accepted file is `/scratch/jjyeung/orch_cd/evalx/work/milestone/DECISION_FORK_BASE_fb2796c5.py`.
- The Orchard launcher with seven pinned files at digest b13c6dcc... (receipts `ORCHARD_LAUNCHER_RECEIPT*.json` in the same folder; the last is `_STEP_SET.json`).
- Registered decision rules exist only for steps 100 and 200 (design record `/data2/jjyeung/agent_project_data/distill_design/LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md`; read it, about 60 lines; nothing else under `/data2`).

## What was ordered (the orchestrator's note)

`/scratch/jjyeung/orch_cd/evalx/inbox/20261114T0412Z_ORCH_AUTHORIZED_milestone_step_set_everywhere.md`: (1) one step set, the kit's registered milestones 1, 50, 100, 200, 400, 600, 800, 1000, admitted consistently in the launcher and the chain; (2) the report label for steps other than 50, 100 and 200 becomes "REPORTED MILESTONE; no registered stop rule; decisions remain with ORCH", and nothing else in the reader changes: scoring, membership, bootstrap, the rulings' logic and the printed rules stay identical in behaviour; (3) the final stop export (an unregistered step, about 560) is admitted only through an explicit argument that must equal the authenticated artifact's own step and an attested `stop_export: true` flag; (4) tests.

## Material

- The patch: `/scratch/jjyeung/orch_cd/evalx/work/milestone/MILESTONE_STEP_SET_20261114T0428Z.patch` (570 lines, ten files).
- The author's RESULT: `/scratch/jjyeung/orch_cd/evalx/events/20261114T0429Z_RESULT_milestone_step_set_for_confirmation.md`, and the review bundle `/scratch/jjyeung/orch_cd/evalx/work/milestone/MILESTONE_STEP_SET_REVIEW_20261114T0428Z.json` (pins, line ranges, test logs, submitted-packet hashes, the retained baseline archive).
- The candidate files in `/scratch/jjyeung/orch_cd/evalx/work/milestone/`: `release_check.py`, `chain.py`, `orchard_launcher.py`, `decision_fork.py`, `report_camera_leg.py`, `native/out2/r1.py`, and the tests `test_milestone_steps.py`, `test_chain.py`, `test_orchard_launcher.py`, `native/out2/test_nomdg.py`.

## Check, each with file and line

1. **The decision reader is behaviourally unchanged except for the label and the new admission gate.** Compare `decision_fork.py` (candidate) with `DECISION_FORK_BASE_fb2796c5.py` function by function. Every function that loads, scores, selects members, bootstraps, applies the four rulings, computes the stop-rule line, the cap clause, the producer-error validity and sensitivity, or formats those results must be identical apart from the label text and the step admission. List every function whose body differs and say exactly what differs. Run the accepted and the candidate reader's shared tests and say whether any numeric output can differ for steps 50, 100 and 200.
2. **One step set.** The set is defined once (`release_check.py`) and every place that tests a step uses it: the launcher's `prepare`, `chain.py`'s spec and release validators, the reader. Steps 150 and 300 refuse everywhere. Look for any remaining hard-coded step tuple in the candidate files and in files they import from that folder.
3. **The stop-export admission cannot be abused.** A non-milestone step is admitted only with the explicit argument, the pinned artifact whose own integer `step` equals it, and the pinned producer attestation carrying the literal boolean `stop_export: true`. Try on paper and with a small test: a string "true", a missing flag, a different artifact, an artifact whose step differs, a milestone step passed through the stop-export route, a stop-export step equal to a registered-rule step (100 or 200) and what label and rule text it then prints. A stop export must never print a registered-rule verdict as if it were step 100 or 200.
4. **Labels.** Step 50: rehearsal label. Steps 100 and 200: the registered labels, unchanged. Every other admitted step, including the stop export: "REPORTED MILESTONE; no registered stop rule; decisions remain with ORCH". Check what the report prints on its stop-rule line for those steps: the computed line may still appear, but it must not read as a decision. Say what it prints.
5. **Launcher.** Only the admission and the carriage of the stop-export evidence into the job changed; storage, card, staging, results return and the submitted packets (tokens b719d20dd, bffa0d6ef, and IF-P0's packet) are untouched. Recompute the seven-file digest the author states (555eb739...).
6. **Camera report and the routed merger (`report_camera_leg.py`, `native/out2/r1.py`)**: label changes only.
7. **Tests.** From a private copy, run the author's test files named above with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` and report counts. Add a test only if it demonstrates a finding.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_STEP_SET.md`, at most 40 lines: first line **ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**; one line per item with evidence; findings by severity with the smallest fix; what you ran; what you did not check. Return a summary of at most 8 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_step_set/` (private copies, at most 500 MB). No Git commands, no ssh, no network, no GPU, no agents. No agent runs a command that removes files, and the names of such operations must not appear in any shell command text (a local guard blocks those commands and they may not be retried); use your file tools for anything of that kind. Stay on `/scratch` except for the one design record named above; never search or list `/home` or `/data*`; no recursive search outside the folders named here. If a test suite writes into the author's lane by a hard-coded path, do not run that suite from a private copy; read its log instead and say so. At most 8 threads.
