<!-- recovered by seal_plan: transcript=71f94277 line=29879 utc=2026-11-14T08:15:41.762Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_native_pilot_launch.md heredoc_unquoted(vars_unexpanded) -->
# ORCH: the fixes are confirmed ACCEPT; launch the native PILOT now

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md` (ACCEPT; the pilot may be submitted; four low findings, none blocking; the reviewer recomputed the 84 captures with the reader's own code and compared the new geometry kernels statement for statement).

The two gate records for token e2c87e426 are written:
- `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426/REVIEW.json`
- `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426/ORDER.md` (it contains exactly one line `LAUNCH EVALX NATIVE pilot 200 general e2c87e426 <family> <artifact>`)

Do, in order:
1. Prepare the real packet with these two files (partition `general`, step 200, the attested step-200 transport). Run the launcher's own admission and batch validation on CPU. If either file's format is not what the gate reads, tell me the exact difference; do not edit them.
2. Queue and main-notice check; `/usr/local/bin/sbatch --test-only`, then one real submission. No retry.
3. RESULT with the job id. Then observe: staging and inventories, the overlay and `ptxas` assertions, model load, P1 to P3, the geometry captures, the items, and the bounded return. Fetch and authenticate the return, and post the pilot's numbers: load time, parity verdicts, peak memory, geometry seconds per capture, seconds per item, compressed return size, the bootstrap's FLA and Triton lines, and the full read's projections (GPU time for 84 captures and 636 items; return size against the limit).
4. If the pilot fails, post the failure record at once; no second pilot without my word.

Step 400: when its export arrives, submit its read with the bounded controller. For that submission only: `ALLOW <the job id of this pilot>` (the one job you submit under this order). If the pilot has already ended, the ordinary launcher applies.