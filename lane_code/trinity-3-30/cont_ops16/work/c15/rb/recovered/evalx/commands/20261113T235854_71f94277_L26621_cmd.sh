<!-- recovered by seal_plan: transcript=71f94277 line=26621 utc=2026-11-13T23:58:54.358Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_NOTE_pending_169328_wait_policy.md <<'EOF'
# ORCH note: job 169328 pending; wait policy

Right not to resubmit. In your next routine observation (no extra session for this alone), record Slurm's start estimate for 169328 and the pending reason code, and whether any other job of this user is in the queue.

If the job is still pending at 00:45Z, post one QUESTION with: the start estimate; what a direct read of the step-100 export on a Trinity card would need (the export on Trinity or not, download size and time at 8 MB/s, which allowed card, how its numbers would compare with the Orchard comparators measured on H100); and your recommendation. Do not start a Trinity read on your own; the comparators were measured on Orchard hardware and a hardware change touches the decision.

The reader change for ruling 4 proceeds meanwhile.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx RESULT 2358Z: step-100 direct read submitted once at 23:55:27Z as job 169328 (package b719d20dd, plan sha 8505d816); PENDING at 23:57:55Z (nodes down, drained or reserved for higher-priority partitions); not resubmitted. NOTE to evalx ($N): record the start estimate; if still pending at 00:45Z, one QUESTION with the estimate and what a Trinity read would need; no Trinity read without my word. Re-armed evwait (bhkelcfbr)." >> $C/ORCH_HANDOFF.md; echo $N