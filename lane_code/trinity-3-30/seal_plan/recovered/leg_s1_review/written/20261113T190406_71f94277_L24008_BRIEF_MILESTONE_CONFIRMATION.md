<!-- recovered by seal_plan: transcript=71f94277 line=24008 utc=2026-11-13T19:04:06.921Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_MILESTONE_CONFIRMATION.md  -->
# Confirmation pass: two reviewed evaluation readers after their fixes

You are an independent reviewer from a different model family than the author. Two scopes of an evaluation chain were reviewed an hour ago and returned ACCEPT AFTER FIXES. The author has repaired them. Your job is a confirmation pass, not a new full review: verify that each named finding is fixed, that nothing else changed in a way that affects admission, scoring, pairing, denominators or safety, and issue the receipts if so. The numbers these readers produce decide whether a training run of about 96 GPU-hours per day continues.

## Material

- First-round verdicts (read both in full first): `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_DIRECT.md` (findings F1 to F8) and `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_ROUTED.md` (findings F1, F2, three minor items, disclosure D1). Their briefs are beside them (`BRIEF_MILESTONE_DIRECT_REVIEW.md`, `BRIEF_MILESTONE_ROUTED_REVIEW.md`) and give the context.
- First-round packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST.json` (direct: 5 pins, digest b1be1d58...; routed: 13 pins, digest 548cbefe...).
- Repaired packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST_REPAIRED.json` (sha256 cf59e374...): direct 21 pinned files, digest 682aaeaa...; routed 29 pinned files, digest 21dd82dd....
- Author's RESULT: `/scratch/jjyeung/orch_cd/evalx/events/20261113T1901Z_RESULT_scoped_review_fixes_ready.md`; test logs `work/milestone/scoped_review_fix_tests_final.log` and `work/milestone/native_review_fix_tests.log`.
- The first-round reviewers' added tests: `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_direct/milestone/test_review_findings.py`.

## Check, per scope, with file and line

1. **Pins.** Hash every pinned file of the repaired packet; confirm each and the digest; state how the digest is computed and whether it still depends on absolute paths (direct F8).
2. **Each finding.** For every finding of the first round, say FIXED, NOT FIXED or CHANGED DIFFERENTLY, with the line that fixes it and the test that fails on the old code. Direct: F1 leftover partial save blocks later saves; F2 authorization not bound to the export and run and reusable; F3 final save gated on the GPU query and on `record()`; F4 staged code list omitted five files the chain runs; and F5 to F8 if done. Routed: F1 archive output folder not refused on `/home` or `/data*`; F2 unpinned imports and the pin check's own hash function; the three minor items (final save order, the step-1 `R1.json` diagnostic label, the data-receipt flags); and whether the reports carry the D1 disclosure (camera tools answered from the frozen tower's pose and depth, with scale and gravity from the checkpoint).
3. **The diff.** For the files that were in the first packet, list every change that is not one of those fixes and say whether it can affect which items are read, how they are scored or paired, any denominator, the frame layout, the tool-call loop or the saves. For the files newly added to the pins (16 in each scope), say what each is and whether it was already executed by the chain before (now merely pinned) or is new code; new code that affects scores needs the same scrutiny as the first round gave.
4. **Tests.** Run both suites from a private copy (CPU only): the author reports 69 milestone tests and 74 native-reader tests. Re-run the first round's three added tests against the repaired code: F1 to F3 must now pass as fixed behaviour.
5. **One new consideration.** The output of these reads must stay off a shared filesystem that is nearly full today. Confirm that, with the fixes, a failed write for lack of space cannot corrupt a result, lose failure evidence, or abort a healthy GPU read for a reason other than the stated free-space floor.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_MILESTONE.md`, at most 50 lines: one verdict line per scope (**ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**), then the table of findings with their status, then anything new, what you ran and what you did not check. For each scope whose verdict is ACCEPT, write the receipt: `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_DIRECT_RECEIPT.json` and `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_ROUTED_RECEIPT.json`, each `{"verdict": "ACCEPT", "reviewer": "<your model family and role>", "scope": "direct" or "routed", "code_pins_sha256": "<the digest you verified>", "packet_sha256": "<sha256 of the repaired packet>"}`. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_confirm/` (private copies and tiny fixtures, at most 500 MB). No Git commands, no ssh, no network, no GPU, no agents, no deletion commands, and no names of deletion operations in any shell command text. Stay on `/scratch`; never read, search or list `/home` or `/data*`; no recursive search outside the folders named here. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
