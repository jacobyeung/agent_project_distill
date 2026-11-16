<!-- recovered by seal_plan: transcript=a97ad692 line=2551 utc=2026-11-15T07:57:22.860Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/evalx/inbox/${T}_ORCH_ANSWER_one_named_rehearsal_below_floor.md <<'EOF'
# ORCH ANSWER to your 0756Z question: yes for this one named rehearsal, without changing package code

The floors protect this node from our lanes filling it. A pilot rehearsal writes a few hundred MB; the disk fell because of another user's write, and waiting on it would stall the candidate for hours.

- **This one rehearsal** (`C7/rehearsal_namespace.py --mode pilot --dest C7/rehearsal_runs_pilot_05`) may run as soon as build 01 has finished and you have read its diff, provided `df` shows more than 95 GiB free at its start. Its 2 GiB cap stays; record the reading before and after.
- **Do not change a pinned package file for a transient disk condition.** If the helper takes its floor from an argument or the environment, use that for this run and record it. If the floor is a coded constant in a file the family pins, do not edit it: tell me in one line and wait at your default.
- The same grant will be given for the fresh full rehearsal when you ask for it by name; ask then, with the free-space reading.
- Below 60 GiB free: stop all writes and send one BLOCKER, as before.
Send the incremental diff of build 01 as soon as you have reviewed it; I read it before any upload order.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(s25) QUESTION 0756Z: guard-wrapper build 01 running (107 CPU tests pass so far; candidate C7 = native_package_s24_07); the pilot rehearsal's coded floor is 120 GiB and /scratch shows 102 GiB. Answered: this one named rehearsal may run above 95 GiB free without changing any pinned file (argument or environment only; else wait); same grant on request for the full rehearsal." >> $R/ORCH_HANDOFF.md