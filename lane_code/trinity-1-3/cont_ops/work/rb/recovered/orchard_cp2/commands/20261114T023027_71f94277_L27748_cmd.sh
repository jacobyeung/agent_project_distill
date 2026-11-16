<!-- recovered by seal_plan: transcript=71f94277 line=27748 utc=2026-11-14T02:30:27.890Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_NOTE_no_events_for_rate_sign_changes.md <<'EOF'
# ORCH note: stop posting events for rate-sign changes

My 0155Z wording caused this; it was a mistake. Post a project-space event only when free space crosses 400, 300, 200 or 140 GB in either direction, or when the projection to 150 GB falls under three hours. Rate-sign changes go into the five-minute series only. Each event wakes the orchestrator.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: orchard_cp2 RESULT 022913Z: project space 436.2 GB, 3.8 GB/h (rate-sign event only). Told orchard_cp2 ($N) to stop posting events for rate-sign changes (my 0155Z wording caused them). Re-armed evwait (bq7d68met)." >> $C/ORCH_HANDOFF.md