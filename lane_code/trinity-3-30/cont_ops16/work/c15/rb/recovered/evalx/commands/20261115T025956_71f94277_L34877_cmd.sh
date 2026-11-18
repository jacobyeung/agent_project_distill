<!-- recovered by seal_plan: transcript=71f94277 line=34877 utc=2026-11-15T02:59:56.672Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_YES_rehearse_all_636_items.md <<'EOF'
# ORCH: yes, rehearse the full read over all 636 items

Keep the worker's cohort and admission guards exactly as they are and run the full-read rehearsal over the whole 636-item cohort with the CPU model and decode stand-in. That is better than my reduced list: it executes the real membership and family-count checks. Keep it within the node's limits: at most 8 threads, small writes only, and stop and tell me if the rehearsal would write more than 300 MiB or run longer than 40 minutes.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 0258Z: the full-read rehearsal cannot use a reduced item list without touching guards; it proposes all 636 items with the CPU stand-in. Answered yes (<=8 threads, <=300 MiB writes, <=40 min)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md