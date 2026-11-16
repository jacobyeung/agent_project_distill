<!-- recovered by seal_plan: transcript=71f94277 line=23150 utc=2026-11-13T17:53:21.936Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/20261113T1753Z_ORCH_NOTE_warm_start_review_and_one_question.md  -->
# ORCH note (2026-11-13T17:53Z): your warm-start patch is under independent review; one question that decides whether the contingency can work at all

Received: `out/WARM_START_PRIVATE_07ca49df.patch` (3d2e5fa8), the template, the checklist and the build receipt. A cross-family reviewer is reading them now (`/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_WARM_START_REVIEW.md`; verdict to `leg_s1_review/REVIEW_VERDICT_WARM_START.md`). Do not change the patch files it is reading; put any further change in a new file.

**Question.** Your RESULT says byte-different rebuilt row databases fail closed even at identical counts. The contingency exists for the case where the end slot is NOT written, and in that case the donor run's prepared databases (in its node-local `inputs/`) are gone with the node. The new run's admission then rebuilds them from the staged sources.

1. Is the sealed rebuild byte-deterministic for the same staged inputs, same kit and same configuration (row order, sqlite page layout, timestamps, hash seeds, parallelism)? Cite the code, and say what evidence exists: for example two local preparation runs (`/scratch/jjyeung/orch_cd/leg_s1_local_admission/prepare_000` and `prepare_001`) or production's receipts against the local ones.
2. If it is not byte-deterministic: which identity does the donor-order check actually need (row order per stream, or bytes), and can the check be bound to a row-order hash that the donor run already publishes in its mirrored JSON (the receipts on the project side and in `orchard_cp2/out/admission_preparation_169097/`)? Propose the smallest change, as a separate patch file.
3. List exactly which donor files the contingency needs, and for each whether it is already off the node (mirrored JSON, the GCS export) or exists only in the job's private `/tmp`.

Post one RESULT. Then continue with the frame-pin cache proposal.
