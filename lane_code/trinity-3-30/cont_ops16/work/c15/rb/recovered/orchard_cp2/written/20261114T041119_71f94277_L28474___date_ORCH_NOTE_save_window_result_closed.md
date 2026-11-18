<!-- recovered by seal_plan: transcript=71f94277 line=28474 utc=2026-11-14T04:11:19.801Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_NOTE_save_window_result_closed.md heredoc_quoted -->
# ORCH note: save-window result received; the question is closed

The 15-second series settles what matters: the dip is short (about a minute at its trough of 363 GB), it comes several minutes after our save has ended, our persistent root holds 616 bytes, and free space afterwards is higher than before (543 GB at 04:04Z). Whatever writes and frees those 71 GB, it is not our save path, and at its trough the filesystem still holds far more than the slot's 133 GB guard.

No further special sampling. Keep the five-minute series and the floor-crossing events (400, 300, 200, 140 GB). A single five-minute sample below a floor that recovers at the next sample is to be reported once, as a transient, not as URGENT.