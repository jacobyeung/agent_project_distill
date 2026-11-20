export PYTHONDONTWRITEBYTECODE=1
# Bulk publication ends 780 s before allocation end; evidence ends before TERM@600.
tk_live_finish() {
    local status="$1" signal_mode="${2:-}" waited=0 copy_pid seconds
    trap '' TERM USR1
    trap - EXIT
    if [[ -n "$signal_mode" && -n "${TK_WORK_PID:-}" ]]; then
        python3 -B -I -s "$ROOT/b/sr.py" "$TK_WORK_PID" 420 signal || waited=$?
        if [[ "$waited" == 0 ]]; then
            status=0
            wait "$TK_WORK_PID" || status=$?
        else
            status="$waited"
        fi
    fi
    for copy_pid in "${TK_LOG_PID:-}" "${TK_COPY_PID:-}"; do
        if [[ -n "$copy_pid" ]]; then
            kill -TERM -- "-$copy_pid" 2>/dev/null || true
            python3 -B -I -s "$ROOT/b/sr.py" "$copy_pid" 5 || kill -KILL -- "-$copy_pid" 2>/dev/null || true
            wait "$copy_pid" 2>/dev/null || true
        fi
    done
    # Close the last launch-evidence log writer before freezing the archive.
    python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" "$status" || true
    if [[ "$waited" == 0 ]]; then
        seconds=$(python3 -B -I -s "$ROOT/b/pc.py" --seconds)
        timeout --signal=TERM --kill-after=5 "$seconds" python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --final --status "$status" || true
    else
# Do not archive files while an unfinished trainer can still modify them.
        timeout --signal=TERM --kill-after=5 150 python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --small || true
    fi
    exit "$status"
}
python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --prepare
trap 'tk_live_finish $?' EXIT
trap 'tk_live_finish 143 signal' TERM
trap 'tk_live_finish 138 signal' USR1
setsid python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --loop &
TK_COPY_PID=$!
setsid python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --loop-small &
TK_LOG_PID=$!
