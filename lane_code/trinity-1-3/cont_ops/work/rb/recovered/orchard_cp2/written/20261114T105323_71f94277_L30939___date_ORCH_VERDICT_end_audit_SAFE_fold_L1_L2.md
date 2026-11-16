<!-- recovered by seal_plan: transcript=71f94277 line=30939 utc=2026-11-14T10:53:23.343Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_VERDICT_end_audit_SAFE_fold_L1_L2.md heredoc_quoted -->
# ORCH: independent verdict on the end audit step = SAFE TO RUN AT END

Verdict file: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_END_AUDIT_STEP.md` (20 lines; read it). It reviewed node 6c15e418, gate da7d61af, login 929471de, driver 5ea55546 (binding 2f4faddc) and ran the 60 tests from private copies. Nothing touches the end slot. Low findings to fold into your candidate together with your own two fixes:

- L1: driver line 232, the except clause misses AttributeError (a non-dict JSON body would crash the driver after the call). Catch it; the outcome is RETURN_UNVERIFIED_NO_RETRY with RESULT.json written.
- L2: pass an outer timeout of 150 s to the runner call (driver line 209); TimeoutExpired and OSError become TRANSPORT_FAILED with `transport.json` and `RESULT.json` retained, and no second call. This is your gap 2.
- Your gap 1 (the review record's content): keep your fix.
- No code change for L3 to L6; put them in the end RESULT's wording: `nice` is the effective control; a nonzero trainer or wrapper rc makes the gate refuse the audit, which is the expected outcome and not a fault; a step exit of 3 shows as DerivedExitCode 3 and is reported apart from the job state and the slot state; record slot_before and slot_after.

Change only the driver unless a test proves another file needs it. Then one event with: the diff against binding 2f4faddc (path and sha256), the new four source hashes, the test counts, and the exact review-record form the driver now requires (file name, schema, fields). I confirm the diff, write the record in that form, and you install and seal. Cut-off 13:45Z.