<!-- recovered by seal_plan: transcript=71f94277 line=31712 utc=2026-11-14T14:18:46.246Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ACK_space_alarm_no_intervention.md heredoc_quoted -->
# ORCH: space alarm read; no intervention; the runbook stands

440 GB free at 14:18Z, falling about 213 GB/h on confirmed samples; forecast 397 GB at 14:25Z. The end slot needs about 113 GB and starts within minutes of the trainer's stop, so it should fit. Nothing changes:

- No copy, no destination change, no signal. If the wrapper skips its slot for lack of space, record the skip and attest the stop export; the stop export on GCS is then the surviving state.
- Record project free space immediately before the slot starts and after it ends (from your ordinary samples) in the end RESULT.
- Next space event only on a confirmed 300, 200 or 140 GB crossing, or if the forecast for 15:25Z falls below 140 GB while the slot is still writing (that one is URGENT).