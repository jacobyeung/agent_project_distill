<!-- recovered by seal_plan: transcript=71f94277 line=24053 utc=2026-11-13T19:08:29.946Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/$(date_ORCH_ORDER_warm_start_review2_fixes_and_trial_fingerprint.md heredoc_quoted -->
# ORCH order: second warm-start review is SEALABLE AFTER FIXES; one required fix, and a trial fingerprint now

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_WARM_START_2.md` (42 lines; read it in full). Confirmed: F1 to F4 fixed (each test fails on 3d2e5fa8 and passes on the candidate e0770534); the allowlist matches its published file and refuses unlisted fields at any depth, type-strictly; scanner and consumer hash the donor identically; the byte gate is still the default; the real mirrored production schema binds after a simulated fresh admission; seven targeted mutations refuse. The reviewer's 17 tests are in `/scratch/jjyeung/orch_cd/leg_s1_review/work_warm_start_2/` (adopt `test_reviewer_round2.py` and `sim_production_check.py`).

## Fixes, as a new patch file on top of e0770534, each with a test

1. **G1 (medium, required before any seal):** the attestation is bound to the donor's configuration and preparation pins but not to the scanner's source hash. `accept_scan.py` drops `scanner.source_sha256` and `s1_row_order.py:86-93` cannot tell who produced the rows; the reviewer's test binds an envelope computed from a new admission with a changed target. Keep `source_sha256` (5c1f4408...) in the envelope, have `verify` require it, and record it in the lineage.
2. **G3 (low, fails closed):** `s1_row_order.py:89` compares pins including their paths; the scanner records the donor's logical `/inputs/` path, so a mirrored `donor_config` path would refuse at launch. Compare content pins, and treat the path as one of the named aliases.
3. **G2 (low):** your earlier suites are stale against the candidate (fixtures that `prepared()` refuses first, refusals that now fire earlier with another message). Bring them up to date so one command runs every suite green.
4. **G4 (low):** row JSON key order is not bound because `canonical()` sorts keys. State in the design note why that is acceptable (the trainer reads rows by key), or bind it.

## The check the reviewer says matters most, to start now

Whether a fresh admission reproduces the donor's ordered row content is unproven. If it does not, both gates refuse and the contingency is unusable. We can learn most of the answer today on this node:

- Run the frozen scanner (bundle 1a565f85, unchanged) over the prepared databases of the local admission (`/scratch/jjyeung/orch_cd/leg_s1_local_admission/`, the successful preparation with stand-ins and without the large pose source) and keep its per-stream ordered-row digests. Local, read-only, same bounds as your benchmark; no question needed.
- When the operator returns the production scan (I have given a conditional go for one execution inside the job), compare stream by stream. Routing (57,136 rows) and VQA (114,904 admitted) are comparable between the two; say exactly which streams are not (pointing ran on stand-ins locally; pose lacks one source) and why.
- Report: for each comparable stream, identical or not; if not, the first differing position and what differs (order, a field, a target). That tells us whether a fresh admission on Orchard would reproduce the donor, before the donor is gone.

Post one RESULT for the fixes and one for the local digests. This goes before the frame-pin cache.