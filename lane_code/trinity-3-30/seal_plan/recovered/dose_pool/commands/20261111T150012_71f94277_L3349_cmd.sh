<!-- recovered by seal_plan: transcript=71f94277 line=3349 utc=2026-11-11T15:00:12.470Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); for L in frontier_read label_247; do cat > $L/inbox/${T}_URGENT_key_pause_1515Z.md <<'EOF'
# URGENT (orchestrator): stop every call on the Gemini key by 15:12Z today; stay paused until I write RESUME here
Main's orchestrator asked, under the user's ruling that main has full priority today: the whole key (Argon, Carbon, every model) must be quiet from 15:15Z while main runs timed runs for the rebuttal's speed figure. Its estimate for the end is 19:45Z; it may release earlier.
Do now:
1. Stop your runner and driver processes cleanly so that no request is in flight at 15:12Z (stop the supervisor first if it would restart them). Finished answers and labels stay; unfinished units rerun at RESUME.
2. Post one RESULT event `<stamp>_RESULT_key_paused.md` with the UTC time of the last call and the pids stopped.
3. Until RESUME: no call on the key at all, not a smoke test, not a retry. CPU work that needs no key continues (scoring what is done, merges, verdict files, reports).
4. If your stall watch fires on the quiet drivers, ignore it; the pause is the cause.
At 15:12Z I check the process list and freeze (SIGSTOP) any runner still alive.
EOF
done; cat > dose_pool/inbox/${T}_NOTE_key_pause.md <<'EOF'
# NOTE (orchestrator): no call on the Gemini key from 15:12Z until I write RESUME (main's timed rebuttal runs need the whole key quiet). The Gemini-route pilot stays on hold; everything else continues.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) KEY PAUSE: main (14:46Z notices log) asked PAUSE ALL on the Gemini key from 15:15Z to ~19:45Z (timed rebuttal runs). URGENT notes to frontier_read and label_247 (stop by 15:12Z, RESULT key_paused), NOTE to dose_pool. I check at 15:12Z and SIGSTOP leftovers. Old v590g Argon loops (pids 3539044, 3546734, 3832334, since 10-27/29) show no output since 11-05." >> ORCH_HANDOFF.md; date -u +%H:%M:%SZ