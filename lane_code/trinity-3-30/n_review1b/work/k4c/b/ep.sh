export PYTHONDONTWRITEBYTECODE=1
tk_evidence_finish() {
    local status="$1" signal_mode="${2:-}"
    trap - EXIT TERM USR1
    if [[ -n "$signal_mode" && -n "${TK_WORK_PID:-}" ]]; then
        kill -TERM -- "-$TK_WORK_PID" 2>/dev/null || true
        wait "$TK_WORK_PID" 2>/dev/null || true
    fi
    if [[ -n "${TK_EVIDENCE_PID:-}" ]]; then
        kill -TERM "$TK_EVIDENCE_PID" 2>/dev/null || true
        wait "$TK_EVIDENCE_PID" 2>/dev/null || true
    fi
    python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" "$status" || true
    exit "$status"
}
trap 'tk_evidence_finish $?' EXIT
trap 'tk_evidence_finish 143 signal' TERM
trap 'tk_evidence_finish 138 signal' USR1
setsid python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" -1 --loop &
TK_EVIDENCE_PID=$!
