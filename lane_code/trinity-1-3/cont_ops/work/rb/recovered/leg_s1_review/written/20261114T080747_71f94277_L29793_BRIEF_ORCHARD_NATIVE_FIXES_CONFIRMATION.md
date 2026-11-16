<!-- recovered by seal_plan: transcript=71f94277 line=29793 utc=2026-11-14T08:07:47.701Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_ORCHARD_NATIVE_FIXES_CONFIRMATION.md  -->
# Confirmation review: fixes to the Orchard native routed-read family (new family seal 0eb005c2)

You are an independent reviewer from a different model family than the author (a GPT-family lane). An independent review of the family at seal 37d83521 returned ACCEPT AFTER FIXES: read it first, in full: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md` (28 lines; findings H1, H2, M1, M2, M3). The author has fixed them and re-sealed. Confirm the fix diff only; do not redo the first review.

## Material (under `/scratch/jjyeung/orch_cd/evalx/work/milestone/native_fix_s22_01/orchard_native/` unless a full path is given)

- The author's RESULT: `/scratch/jjyeung/orch_cd/evalx/events/20261114T0806Z_RESULT_native_fixes_sealed_0eb005c2.md` (read in full).
- `packages_s22/RUNTIME.patch` (634 lines) and `packages_s22/TESTS.patch` (731 lines), both against the reviewed seal; `seal_s22_01/REVIEW_REQUEST.json`, `seal_s22_01/FAMILY.json`, the pilot candidate packet under `seal_s22_01/`.
- The fixed modules beside them and their tests; the two whole-job rehearsal records the RESULT names.
- The reviewed family for comparison: `/scratch/jjyeung/orch_cd/evalx/work/milestone/orchard_native/` (seal `seal_s21_01/`).
- The routed reader the kernels come from: `/scratch/jjyeung/orch_cd/evalx/work/milestone/native/out2/` and its cohort and frame records (the 636 items, `FRAMES.json`).
- The FLA module manifest with the executables' names: `/scratch/jjyeung/orch_cd/if_p0/inbox/20261114T064704Z_cp2_fla_m.sha`.

## Check, each with file and line

1. **H1.** Extracted members keep a safe mode from the archive header (no set-id or world-writable bits; executables stay executable); the runtime check asserts the staged `ptxas` is a regular executable file before any model work; a test proves a mode survives extraction. Check every other extraction path in the family for the same loss.
2. **H2.** Full-mode geometry runs over exactly the captures the 636 items use. Recompute that set yourself from the cohort files (the first review counted 84 captures used, 142 with a task row, 152 in the frame list) and compare with what the fixed code binds; confirm the pinned geometry kernel is the accepted reader's code, that the old 152 checks are changed consistently in the worker and the job, and that no item loses its capture.
3. **M1.** NumPy, FLA and Triton must resolve from their staged overlays with the production versions; a wrong layout refuses instead of falling back. Say exactly what is asserted and whether a correct production layout could be refused by mistake (name the risk: this check runs for the first time in the pilot).
4. **M2.** The pilot writes its measurements after load, after parity, after each capture and after each item, so a timeout or kill still returns them through the bounded publication; the stated budget (2,400 s of GPU inside a 90-minute allocation) is enforced as the author says. Confirm the parity gate is still mandatory and the pilot still cannot enter the scored read.
5. **M3.** A full-read packet requires an authenticated passed pilot; the return-size projection uses the pilot's measured sizes and refuses above the limit. Check the arithmetic and that a missing or failed pilot cannot be bypassed.
6. **Nothing else changed.** List every file the runtime patch touches and state for each whether it can change a prediction, a score, the item set or the pairing. The scored read must still be the accepted reader's code. The replaced code object (`code_fe1eaafe...`, generation in the RESULT) must be what the family pins, and the other four object pins must be unchanged.
7. **Tests.** From a private copy, run the family's CPU suites the way the first review did (redirect fixture roots into your own work folder; skip any suite whose guard refuses outside the author's lane and read its log). Report counts.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md`, at most 35 lines: first line **ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**, and say plainly whether the **pilot** may now be submitted; one line per item with evidence; findings by severity with the smallest fix; what you ran; what you did not check; what the pilot is the first to execute. Return a summary of at most 8 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_native_fixes/` (private copies and fixtures, at most 1 GB). No Git commands, no ssh, no network, no GPU, no agents. No agent runs a command that removes files, and the names of such operations must not appear in any shell command text (a local guard blocks those commands and they may not be retried); use your file tools for anything of that kind. Stay on `/scratch`; never search or list `/home` or `/data*`; no recursive search outside the folders named here; do not read files larger than 20 MB or unpack the pinned archives. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. At most 8 threads.
