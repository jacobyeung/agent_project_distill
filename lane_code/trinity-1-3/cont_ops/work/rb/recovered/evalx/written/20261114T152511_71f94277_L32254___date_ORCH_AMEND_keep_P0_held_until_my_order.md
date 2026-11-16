<!-- recovered by seal_plan: transcript=71f94277 line=32254 utc=2026-11-14T15:25:11.982Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_AMEND_keep_P0_held_until_my_order.md heredoc_quoted -->
# ORCH amendment: keep 169530 held; do not release it when the pilot runs

Since `advanced` carries main's pending jobs (167859 to 167861), the full routed read will also need our `general` slot, and it outranks the IF-P0 run. So:

- Do not release 169530 when pilot 169537 starts or finishes. It stays held until I order its release.
- If the pilot passes, build the full-read packet for `general` first and report its token with the pilot's RESULT; I then order the full read, and P0 is released behind it.
- If the pilot fails, I will most likely release P0 at once so the card is not idle while the failure is fixed; wait for that order.