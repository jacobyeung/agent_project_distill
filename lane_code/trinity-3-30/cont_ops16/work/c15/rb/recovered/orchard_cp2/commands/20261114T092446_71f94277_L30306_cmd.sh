<!-- recovered by seal_plan: transcript=71f94277 line=30306 utc=2026-11-14T09:24:46.977Z kind=commands original_path=(bash command)  -->
fold -w 1100 -s /scratch/jjyeung/orch_cd/orchard_cp2/events/20261114T092334Z_QUESTION_end_baseline_source_match_scope.md | tail -n +14 | head -n 12; N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ANSWER_end_audit_step_approved.md <<'EOF'
# ORCH answer to QUESTION 092334Z: the end-of-run source and mirror audit is approved, once

Approved as you scoped it: one read-only overlap step in job 169097 (one CPU, 1 GiB, at most 60 seconds of work, immediate admission, no retry), after the trainer and all four ranks have exited and a final complete save is identified. It reads the complete marker and the attempt and binding metadata (at most 2 MB), may list at most 64 checkpoint names in the run root if the exact path is not in held evidence, and hashes the two metrics files' prefixes through the final saved step (at most 128 MB each); it returns identities, hashes, byte ranges, row counts and four-rank coverage. No state tensors, no credentials, no writes, no signals.

Three conditions:
1. It must never delay or touch the wrapper's own end sequence (final save, stop export, slot copy): it runs beside it as an overlap step and reads only. "Before the slot copy" is a preference, not a gate: if the wrapper has already begun the slot copy, run the audit anyway while the copy proceeds, and say which it was.
2. If the allocation's remaining time is under five minutes when you could start it, skip it and record that.
3. The absolute-path form and the minimal explicit environment that today's in-job steps used; raw output saved before decoding.

Report it inside your end-of-allocation RESULT, not as a separate event, unless source and mirror disagree; then mark it URGENT.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: orchard_cp2 QUESTION 092334Z (one bounded end-of-run in-job audit of node metrics vs the project mirror through the final saved step; mirror held through step 415, 66.0 MB) ANSWERED ($N): approved once, read-only overlap step after trainer exit, never delaying the wrapper's end sequence, skipped under five minutes of remaining allocation; reported in the end RESULT. Production is past step 415. Re-armed evwait (bb1w9vbzm)." >> $C/ORCH_HANDOFF.md