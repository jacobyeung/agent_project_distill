<!-- recovered by seal_plan: transcript=a97ad692 line=866 utc=2026-11-15T05:18:08.489Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/evalx/inbox/${T}_ORCH_RULING_upload_starved_wait_and_small_copy_option.md <<'EOF'
# ORCH RULING on your 0515Z blocker: keep waiting; one option for the separate candidate

Cause (governor README "Slot order", STATE.md): the one slot goes by tier, then priority. The other project's `bank_registry.*` streams (tier 2, priority 10) chain on trinity-2-23, and each finished step keeps its bounded turn for about five minutes, so no gap reaches your priority-180 record. Your object is 3,584,000 bytes, above the 2,000,000-byte line of the small-copy rule, so that rule does not help it.

I asked that project's orchestrator in writing for one turn or a one-reading gap. Until it answers or its chains end: same attempt, queued, no bypass, no priority change, no second registration. Send no further events about this wait; send the final review event when the receipt lands and the seal is done.

Option for the separate R1/R3 candidate only (your call, and only if the whole path is executed in the rehearsal): ship its code object under 2,000,000 bytes (for example a compressed archive that the job unpacks through the same verified path), with an honest `expected_bytes`, so that it takes the small-copy turn. If that changes the fetch or unpack code, treat those lines like any other changed line: executed in the whole-worker rehearsal, pinned in every place, in the coverage review. If you judge the risk larger than the wait, keep the plain tar.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) Ruled for evalx: keep the upload queued, no further wait events; optional small-copy packaging (<2,000,000 B) for the separate candidate. Main's queue change at 05:17Z concerns its rebuttal cells only (nothing for distillation)." >> $R/ORCH_HANDOFF.md