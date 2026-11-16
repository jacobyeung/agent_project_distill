<!-- recovered by seal_plan: transcript=71f94277 line=23509 utc=2026-11-13T18:25:10.272Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_MILESTONE_DIRECT_REVIEW.md  -->
# Independent review, direct scope: the reader that decides whether a training leg continues

You are an independent reviewer from a different model family than the author. The code under review produces the numbers of a stop-or-continue decision on a training run that costs about 96 GPU-hours per day, so a wrong denominator, a wrong frame layout or a silently dropped failure matters more than style.

## Context

A 9B vision-language model is being trained (run 469ddece). At step 100 its weight export is read on held-out development questions and compared with two baselines (the leg's parent checkpoint "CP1 m200" and another student "f17"). The registered comparisons are: leg minus f17, leg minus parent, and a cut by the 47 development scenes f17 saw; plus three camera-motion question types on a 450-question cohort, each against shortcut baselines. A rehearsal on the step-1 export runs first; its numbers are diagnostic only and must be labelled so.

The author (lane "evalx") packaged the direct readers into a command chain with authorization gates and a bounded save routine. Scope "direct" of the review packet:

- Packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST.json` (entry `direct`: five code pins and `code_pins_sha256` b1be1d58...).
- Files: `camera_leg.py`, `chain.py`, `chain_save.py`, `execute_chain.py`, `report_camera_leg.py` in `/scratch/jjyeung/orch_cd/evalx/work/milestone/`, and their tests in the same folder.
- Background you may read: the earlier verdict on the camera reader `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_CAMERA_DIRECT.md`; the launch card's step-100 section `/scratch/jjyeung/orch_cd/leg_s1_tree/out/PRELAUNCH_CARD.md` (search it for "step-100" and "comparisons"); the camera cohort `/scratch/jjyeung/orch_cd/legs1_routed/out2/CAMERA_COHORT.json` and `CAMERA_TASKS.jsonl`; the decision rule `/scratch/jjyeung/orch_cd/legs1_reads/out/decision.py` (sha256 begins 2874d0a7); the lane's own notes at the top of `/scratch/jjyeung/orch_cd/evalx/STATUS.md` (top block only).

## Check, with file and line for every finding

1. **Pins.** Hash the five files; do they equal the packet, and does the canonical digest equal `code_pins_sha256`? State how you computed the digest.
2. **Admission.** Exactly the pinned question sets are read (identifiers, hashes, counts); nothing can be added, dropped or reordered silently; the export under read is bound by identity to the producer's done record and artifact, and a mismatched or incomplete export refuses.
3. **Authorization.** No GPU command can run without the recorded authorization for that exact export and cell; the step-1 rehearsal cannot be mistaken for a decision read (labels, file names, report text); a repeated or resumed chain cannot double-count or skip a cell.
4. **Frame binding.** Each student is read with the frame layout it was trained with (this project lost 3 to 13 points to a layout mismatch before); the layout is taken from an authenticated source, not a default; frame identity and timing are bound per item.
5. **Scoring and denominators.** Every admitted item stays in the denominator: parse failures, cap hits, generation errors and missing outputs count as wrong and are reported per type; the comparisons are paired on identical items; intervals use the stated clustered bootstrap; the decision rule file's hash is asserted before use.
6. **Failure preservation.** A failed command leaves its evidence and stops the chain in a state that a later run reports honestly; nothing is retried silently; partial outputs cannot be read as complete.
7. **Bounded save.** Two alternating fixed names with atomic rename of a completed file, a free-space floor checked before the job and at each save, a clean stop below it, and no path that removes or overwrites evidence. The target filesystem is shared and nearly full today, so check the behaviour when a write fails for lack of space.
8. **Tests.** Run the scope's CPU tests from a private copy and report the count. Add a test only if it demonstrates a finding.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_DIRECT.md`, at most 45 lines: first line **ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**; one line per item with evidence; findings by severity with the smallest fix; what you ran; what you did not check. If and only if the verdict is ACCEPT, also write `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_DIRECT_RECEIPT.json` with `{"verdict": "ACCEPT", "reviewer": "<your model family and role>", "scope": "direct", "code_pins_sha256": "<the digest you verified>"}`. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_direct/` (private copies and tiny fixtures, at most 300 MB). No Git commands, no ssh, no network, no GPU, no agents, no deletion commands. Stay on `/scratch`; never read, search or list `/home` or `/data*`; no recursive search outside the folders named here. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
