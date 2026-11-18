<!-- recovered by seal_plan: transcript=71f94277 line=31386 utc=2026-11-14T12:16:54.547Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_REVIEW_ACCEPT_probe_fix_seal_and_report.md heredoc_quoted -->
# ORCH: independent review of the probe fix = ACCEPT; seal it, then tell me the seal and the token

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_NATIVE_PROBE_FIX.md` (35 lines, sha256 63b20ea9...). It accepts nomdg.py 785e061e and test_nomdg.py 6a8322ec as they are; its two residual risks are low and need no change now. It notes the kernel and adapter pins are still 96e9e7e4 and must be renewed in the seal (a stale pin refuses safely).

1. When the real-id CPU replay passes, bind and seal the family with renewed pins, upload the replacement code object as before, and build the pilot-3 packet (step 200, `general`, parity-only pilot) up to the point where it needs my control files.
2. Then one event with: the new family sha256, the packet token you chose, the replaced object's name and generation, the replay's result in one line, and the state of the P0 job at that moment (its id, how far it got). Nothing else.
3. I answer with `NATIVE_PILOT_CONTROL_<token>/REVIEW.json` and `ORDER.md` in the form of the e495c2771 pair, and with the cancel decision for P0 in the same order. Do not cancel anything before that.

If the replay fails, stop and send me the failing assertion instead.