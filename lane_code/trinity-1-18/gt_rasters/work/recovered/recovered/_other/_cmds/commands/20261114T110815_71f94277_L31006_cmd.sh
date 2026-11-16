<!-- recovered by seal_plan: transcript=71f94277 line=31006 utc=2026-11-14T11:08:15.605Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/orchard_cp2/inbox/${N}_ORCH_ANSWER_terminal_slot_read_approved.md <<'EOF'
# ORCH answer: yes, one terminal slot and accounting read, as you bounded it

Approved exactly as in your 110743Z question: one read-only, no-retry login-host call through the existing shared master and `work/oc.sh`, only after the watcher shows a terminal job state; the four slot records and three disposition files at the sizes you state, `lstat` of the four archive names, one `sacct` query with the eight fields, 64 KiB of file reads in total, a minimal environment, a 60-second outer bound, raw returns kept before decoding.

- Build and test it locally now (mocked transport), without touching the watcher or the audit sources. It needs no further review: the job is over when it runs and it writes nothing remotely.
- If the call fails or the connection drops, that is the one attempt: report it in the end RESULT and stop.
- Put its findings in the end RESULT; a separate event only if the slot records are missing or inconsistent with the wrapper log.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) orchard_cp2(13) QUESTION 110743Z: approved one bounded read-only terminal slot-metadata + sacct call after the job's terminal state (no retry)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md