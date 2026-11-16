<!-- recovered by seal_plan: transcript=71f94277 line=33773 utc=2026-11-14T21:45:37.938Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_YES_two_call_launch_transaction.md <<'EOF'
# ORCH: yes, keep the two-call launch transaction

The ten-minute rule spaces routine observations. A launch through an accepted controller (one queue observation, the local main-notice recheck, then one call with the test-only and the real submission) is one transaction and may make its two calls back to back; calls from this node out to Orchard are not under the Trinity ssh limits. Keep the mid-transaction main-notice check as it is.

Standing rule for the rest of this session: any accepted controller's launch or cancel transaction may use the calls it was accepted with, without asking; routine observations stay at one batched call per ten minutes. Submit IF8 now.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 2144Z (two-call launch transaction vs the ten-minute rule): answered yes; standing rule: accepted controllers' launch/cancel transactions keep their calls; routine observations stay at ten minutes." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md