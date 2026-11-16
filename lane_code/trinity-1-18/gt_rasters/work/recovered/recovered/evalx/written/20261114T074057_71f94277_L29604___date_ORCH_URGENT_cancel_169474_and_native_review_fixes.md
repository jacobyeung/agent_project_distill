<!-- recovered by seal_plan: transcript=71f94277 line=29604 utc=2026-11-14T07:40:57.208Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_URGENT_cancel_169474_and_native_review_fixes.md heredoc_quoted -->
# ORCH (URGENT, two parts): cancel pending job 169474; then the native family's review fixes

## 1. Cancel IF-P0 job 169474 now (my written order)

The review of your native family found a defect that the IF-P0 kit shares: its extractor writes the FLA archive's members without their file modes, so the compiler programs the model's kernels need (`triton/backends/nvidia/bin/ptxas`, `cuobjdump`, `nvdisasm`) would not be executable, and the job would die at its first kernel compile, possibly only after staging about 160 GB. Job 169474 (token a1bf5cb5a7bad53bf, seal 0fa68201) is still pending. In one short Orchard session: check its state; if it is PENDING, cancel that one job id (the scheduler's cancel command with that id only) and record the before and after queue lines; if it is already RUNNING, do not cancel, and tell me at once with its current phase. Post one RESULT. This order covers job 169474 only.

## 2. Native family: ACCEPT AFTER FIXES; the pilot is not to be submitted as it is

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md` (28 lines; read it in full). What passed: the pilot kernels are statement for statement the accepted reader's code and the full read imports the original modules; the cohort is 636 items on 152 captures; the 806 FLA names and 13 base-model names match the real listings; every path the job reads is staged under its hash; the reuse digest recomputes; the build-only packet refuses.

Fix, in one diff on the sealed family:
- **H1 (blocks pilot and full).** `native_stage.extract_named` (line 78) drops file modes. Preserve them as the accepted `orchard_stage` does (`mode & 0o755`), assert in `runtime_spec` that `ptxas` is executable, and add a test.
- **H2 (full read).** `geometry.prepare` loops over all 152 captures, but only 142 have a task row and the 636 items use 84; it would raise at `d3/42444810` after about 80 captures. Run full-mode geometry through the pinned `native_geometry` kernel over the 84 captures the items use, and change the 152 check in `native_worker` (line 198) and `native_job` (line 148) accordingly. State the capture count the read binds and why.
- **M1 (silent).** If the NumPy or closure overlay has the wrong layout, `runtime_spec` falls back to the interpreter's own NumPy without a word. Require NumPy and the FLA and Triton modules to resolve from their overlays, and refuse otherwise.
- **M2.** The pilot's 900-second budget may be too short for ten thinking decodes, and a timeout loses the pilot report. Write the pilot report incrementally (after load, after parity, after each geometry capture, after each item) so a timeout still returns what was measured, and raise the budget to what you can defend.
- **M3.** Project the full read's compressed return size from the pilot's per-item size against the 256 MiB limit before the full read is packaged, and refuse a full packet whose projection exceeds it.

Deliver the diff against the sealed family (runtime and tests separately), the new seal and hashes, test counts and the two rehearsals. I confirm by reading that diff on top of the review. Uploaded objects change only if the code archive changes; if it does, upload the new code object the same governed way under a new name and pin, and say so (approved for that one object, under 5 MB).

Order of work now: the cancel; these fixes; the stop-archive-name candidate; step 400 when it arrives (with the bounded controller only if a job of ours is in the queue).