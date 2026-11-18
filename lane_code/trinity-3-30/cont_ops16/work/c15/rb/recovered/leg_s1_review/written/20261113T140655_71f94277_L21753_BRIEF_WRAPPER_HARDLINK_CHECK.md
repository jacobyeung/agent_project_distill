<!-- recovered by seal_plan: transcript=71f94277 line=21753 utc=2026-11-13T14:06:55.406Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_WRAPPER_HARDLINK_CHECK.md  -->
# Independent check: a two-line change to the production slot wrapper

You are an independent verifier from a different model family than the author of this change. The file under review guards the only durable copy of a training run's state between 24-hour allocations (about 96 GPU-hours each), so be exact.

## Context

A shell wrapper copies a training job's final checkpoint, its `inputs/` folder and `binding.json` into a persistent slot when the job ends, and restores from it at the start of the next job. Its reviewed version (template `/scratch/jjyeung/orch_cd/orchard_cp2/work/adm/jl10_template.sh`, sha256 eaad51092b8c9dab832133c297695451baeb937dd1af4968e5cbd2c848348d2c) verifies the archive's content against the checkpoint's own manifest and rejects any archive member that is not a regular file. A real run's `inputs/` folder contains a hard-linked pair of files written by the trainer (`inputs/native_admission/request.json` and `request.<id>.json`). The archiver stores the second name as a link entry, the verifier rejects it, and no verified slot is written. Confirmed by test: `/scratch/jjyeung/orch_cd/leg_s1_canary/out/JL10_HARDLINK_REVIEW_TESTS.json`.

The wrapper's earlier reviewer wrote a candidate fix itself: `/scratch/jjyeung/orch_cd/leg_s1_canary/work/review_jl10_hardlink_candidate.sh` (sha256 a3efb28b617722b248807b2f7067c943ebbda4371e764ead64082430db5415f2). It says the candidate changes exactly two things: `tar -cf -` becomes `tar --hard-dereference -cf -`, and `du -sb` becomes `du -sb --count-links`; and that all 21 cases of its harness pass (`/scratch/jjyeung/orch_cd/leg_s1_canary/out/JL10_HARDLINK_CANDIDATE_TESTS.json`; harness under `/scratch/jjyeung/orch_cd/leg_s1_canary/work/`, the newest `review_jl10*.py`). Its RESULT: `/scratch/jjyeung/orch_cd/leg_s1_canary/events/20261113T1405Z_RESULT_wrapper_hardlink_FIX.md`. Because the reviewer authored the fix, a second pair of eyes is owed before it is installed.

## Check

1. Diff the candidate against jl10 yourself. Is the difference exactly those two edits, on which lines? Any other byte that differs is a finding.
2. Read the copy block and the restore block of the candidate with the change in mind. With hard links stored as regular files: is every member still verified against the checkpoint manifest and the source listing (path, type, size, hash where given)? Does the source listing the wrapper compares against count a hard-linked file once or twice, and is that consistent with what the archive now holds? Could the comparison pass when a linked file's content is wrong in one of its two archived copies?
3. Space: does `du -sb --count-links` give at least the bytes the archive will hold, for links inside the copied tree and for links whose other name lies outside it? Is the free-space guard therefore still conservative?
4. Restore: both names come back as separate regular files. Does anything in the wrapper's restore guards, or in the trainer's verification of a restored state as far as the wrapper invokes it, require the link relationship? State what you could not check.
5. Symbolic links must still be rejected, and a file that changes or disappears during the copy must still fail. Confirm from the code and from the harness cases.
6. Run the harness from a private copy against the candidate (CPU only) and report the count. If you can add one case cheaply, add this: a hard-linked pair where one name is inside the copied tree and the other outside it.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/WRAPPER_HARDLINK_CHECK.md`, at most 35 lines: first line **INSTALL** or **FIX**; then one line per item with evidence (file and line); findings with the smallest fix; what you ran; what you did not check. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/` (private copies and fixtures under `leg_s1_review/work_wrapper_hardlink/`, at most 300 MB, tiny fixtures only). No Git commands, no ssh, no network, no GPU, no agents. Do not run the wrapper against any real path: only against fixtures in your private folder, as the harness does. Stay on `/scratch`; never read `/home` or `/data*`. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
