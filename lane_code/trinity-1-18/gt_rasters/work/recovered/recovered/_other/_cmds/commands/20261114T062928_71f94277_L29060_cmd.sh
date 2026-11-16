<!-- recovered by seal_plan: transcript=71f94277 line=29060 utc=2026-11-14T06:29:28.052Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ANSWER_use_your_reader_for_all_four.md <<'EOF'
# ORCH answer to QUESTION 062826Z: use your seek-only reader for all four archives; go

My concern was the volume read from the shared filesystem, not whether a few payload bytes are touched. Either method satisfies it. Use the tested seek-only reader for all four archives, for uniformity. Bounds per archive: 60,000 headers, 64 MB read, 300 seconds. If an archive exceeds a bound, deliver what was read with the member count so far and say so; names and sizes are what lane if_p0 needs.

Run the batch now and deliver. For anything else of this size in this task, decide yourself and note the choice in the covering note.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: orchard_cp2 QUESTION 062826Z (GNU tar touches partial payload blocks while listing) ANSWERED ($N): the concern is IO volume only; use the tested seek-only reader for all four archives (60,000 headers, 64 MB, 300 s each); go; decide small details itself. Re-armed evwait (bvryq67k4)." >> $C/ORCH_HANDOFF.md