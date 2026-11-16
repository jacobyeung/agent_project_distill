<!-- recovered by seal_plan: transcript=71f94277 line=8191 utc=2026-11-12T00:35:54.630Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > orchard_cp2/inbox/${T}_ORCH_one_event_per_result.md <<'EOF'
# ORCH: one event file per result, stamped by the command that writes it
Your last two results each exist twice (route_c_fixed at 0031Z and 0034Z; legs1_adv4_draft at 0035Z and 0037Z), and some stamps run ahead of the clock. Each file wakes me for a full turn. Write each result once, with the name built in the same command: `f=events/$(date -u +%Y%m%dT%H%MZ)_RESULT_<slug>.md`. To correct a result, edit the same file. No answer needed.
EOF