export PYTHONDONTWRITEBYTECODE=1
tk_live_finish() {
    local status="$1"
    trap - EXIT TERM USR1
    python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --small || true
    if [[ -n "${TK_COPY_PID:-}" ]]; then
        kill -TERM "$TK_COPY_PID" 2>/dev/null || true
        wait "$TK_COPY_PID" 2>/dev/null || true
    fi
    python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --final || true
    exit "$status"
}
trap 'tk_live_finish $?' EXIT
trap 'tk_live_finish 143' TERM
trap 'tk_live_finish 138' USR1
python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --loop &
TK_COPY_PID=$!
