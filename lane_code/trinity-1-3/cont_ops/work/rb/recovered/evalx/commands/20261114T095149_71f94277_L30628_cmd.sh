<!-- recovered by seal_plan: transcript=71f94277 line=30628 utc=2026-11-14T09:51:49.137Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_hold_P0_until_pilot_starts.md <<'EOF'
# ORCH order: hold P0 169491 so the pilot 169501 starts first

Why: P0 is older in the queue and would start when the step-400 read ends, delaying the pilot by its whole canary. The pilot is short and gates the routed read, which feeds the continuation decision. P0's canary can then run while you build the full-read packet.

1. In your next batched observation call (no extra login), add exactly `scontrol hold 169491` (the same absolute scontrol you already query with) and read back the job's state and reason in that call. Expected: PENDING, reason JobHeldUser.
2. When an observation shows 169501 RUNNING or finished, add exactly `scontrol release 169491` to that call or the next one, and read back its state.
3. If the hold is refused or the read-back differs, change nothing more, make no second attempt, and say so in your next event. The default order then stands.
4. This is not a submission: no packet, no review, no new controller or test suite. The two command strings above are the whole authority; nothing else about 169491 changes, and no cancel runs without my separate order.
5. No event for the hold or the release by themselves; mention both in your step-400 packet event or the pilot's first event.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 0949Z: native pilot 2 submitted once = job 169501 (token e495c2771, family de98ac22), PENDING behind step-400 read 169493 (running since 09:26:43Z) and P0 169491. I ordered evalx (inbox ${N}_ORCH_ORDER_hold_P0_until_pilot_starts.md) to hold P0 in its next batched observation and release it once the pilot runs, so the pilot starts first; no cancel." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; echo ok $N