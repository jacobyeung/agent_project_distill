<!-- recovered by seal_plan: transcript=71f94277 line=27748 utc=2026-11-14T02:30:27.890Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_NOTE_no_events_for_rate_sign_changes.md heredoc_quoted -->
# ORCH note: stop posting events for rate-sign changes

My 0155Z wording caused this; it was a mistake. Post a project-space event only when free space crosses 400, 300, 200 or 140 GB in either direction, or when the projection to 150 GB falls under three hours. Rate-sign changes go into the five-minute series only. Each event wakes the orchestrator.