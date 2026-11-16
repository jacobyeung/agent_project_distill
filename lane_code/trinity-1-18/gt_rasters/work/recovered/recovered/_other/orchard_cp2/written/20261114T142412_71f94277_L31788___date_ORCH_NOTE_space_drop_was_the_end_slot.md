<!-- recovered by seal_plan: transcript=71f94277 line=31788 utc=2026-11-14T14:24:12.526Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_NOTE_space_drop_was_the_end_slot.md heredoc_quoted -->
# ORCH note: the 14:18Z space alarm was our own end slot

Your samples: 545.9 GB at 14:02:59Z, 500.2 GB at 14:07:59Z, 439.8 GB at 14:12:59Z, flat since. The trainer exited at 14:04:31Z, so the 106 GB is the wrapper's slot write, not another tenant. I had told main otherwise and have corrected it.

- In the end RESULT give the slot's free-space before and after from these samples and say whether the slot's records confirm a complete save.
- Clear the forecast alarm: a rate measured across our own slot write says nothing about the next hours. No event for the clearing.
- When the job reaches a terminal state, tell me at once in one line (an event) before the longer end RESULT: I am waiting to use the `advanced` allocation.