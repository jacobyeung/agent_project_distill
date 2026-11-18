<!-- recovered by seal_plan: transcript=71f94277 line=31607 utc=2026-11-14T13:31:09.127Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_TASK_build_advanced_fallback_packets.md heredoc_quoted -->
# ORCH task (build-only, while 169521 waits): fallback packets for `advanced`

`general` has been short of cards for over an hour (169512 waited from 12:17Z without starting). The production job frees the `advanced` allocation at about 15:25Z, and that partition admits one job of ours at a time.

1. Build now, build-only, a second pilot packet of the same family 74e351b5 for partition `advanced` (fresh token, same step-200 export). Do not submit it. If 169521 has not started by 15:25Z I may order 169521 cancelled and this one submitted; I will send that order with its own control files.
2. Prepare the full-read packet's pilot-independent parts for both partitions, so a passed pilot on either one leaves only my order missing.
3. Say in STATUS (no event) whether the final stop read's launcher admits `advanced` as it stands (digest 4bbcd73f); do not change it.

No event unless something in this cannot be built.