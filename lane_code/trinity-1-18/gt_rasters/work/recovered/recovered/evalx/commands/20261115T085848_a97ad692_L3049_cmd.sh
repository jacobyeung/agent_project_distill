<!-- recovered by seal_plan: transcript=a97ad692 line=3049 utc=2026-11-15T08:58:48.335Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/evalx/inbox/${T}_ORCH_YES_full_rehearsal_C7_full_01.md <<'EOF'
# ORCH ANSWER to your 0857Z question: yes, run `rehearsal_runs_full_01` on C7 now

Granted for this named run: `C7/full_rehearsal_background.py`, detached, one thread, nice 10, idle IO, 120 minutes, 2 GiB of owned bytes, start floor 97 GiB and stop line 60 GiB from `C7/DISK_FLOOR_AUTHORITY.json`. Record the free-space reading at start and at end. If it stops on a failure, send the failing line at once; do not restart it without my word.

While it runs (about 70 minutes): review official544's revised kit (`official544/events/20261115T0856Z_RESULT_direct_six_two_roots_review.md`: archive 90c2c742, incremental launcher diff, full-membership check), rerun its dry run and the full-membership check, bind the three aliases, and prepare the packet on the frozen `general` path. Send that RESULT as soon as it is true; the direct read does not wait for C7.

Build 06 as you plan (the reviewer admits the full case's trace for exactly the six named full-only lines; a producer writes EXPECTED_FAILURE.json from the `other_error` case), after the full case exists.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(s25) QUESTION 0857Z: coverage review needs execution evidence for six changed full-mode lines (guard install in prepare_full_geometry; full report guard fields; request identity); asked to run the C7 full rehearsal rehearsal_runs_full_01 at 100.2 GiB free. Answered yes (97 GiB start floor, 60 GiB stop, 120 min, 2 GiB); meanwhile it reviews official544's revised kit (archive 90c2c742; official544 RESULT 0856Z) and prepares the direct-read packet on general." >> $R/ORCH_HANDOFF.md