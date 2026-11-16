<!-- recovered by seal_plan: transcript=71f94277 line=30628 utc=2026-11-14T09:51:49.137Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_hold_P0_until_pilot_starts.md heredoc_quoted -->
# ORCH order: hold P0 169491 so the pilot 169501 starts first

Why: P0 is older in the queue and would start when the step-400 read ends, delaying the pilot by its whole canary. The pilot is short and gates the routed read, which feeds the continuation decision. P0's canary can then run while you build the full-read packet.

1. In your next batched observation call (no extra login), add exactly `scontrol hold 169491` (the same absolute scontrol you already query with) and read back the job's state and reason in that call. Expected: PENDING, reason JobHeldUser.
2. When an observation shows 169501 RUNNING or finished, add exactly `scontrol release 169491` to that call or the next one, and read back its state.
3. If the hold is refused or the read-back differs, change nothing more, make no second attempt, and say so in your next event. The default order then stands.
4. This is not a submission: no packet, no review, no new controller or test suite. The two command strings above are the whole authority; nothing else about 169491 changes, and no cancel runs without my separate order.
5. No event for the hold or the release by themselves; mention both in your step-400 packet event or the pilot's first event.