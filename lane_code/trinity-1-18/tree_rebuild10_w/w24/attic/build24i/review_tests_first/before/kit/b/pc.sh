export PYTHONDONTWRITEBYTECODE=1
# 420 s for the trainer, 10 s for copier shutdown, 155 s for final publication.
# Total <=585 s, leaving >=15 s of B:TERM@600; no KillWait grace is assumed.
tk_live_finish() {
    local status="$1" signal_mode="${2:-}" waited=0 copy_pid
    trap '' TERM USR1
    trap - EXIT
    if [[ -n "$signal_mode" && -n "${TK_WORK_PID:-}" ]]; then
        /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/sr.py" "$TK_WORK_PID" 420 signal || waited=$?
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
            /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/sr.py" "$copy_pid" 5 || kill -KILL -- "-$copy_pid" 2>/dev/null || true
            wait "$copy_pid" 2>/dev/null || true
        fi
    done
    if [[ "$waited" == 0 ]]; then
        timeout --signal=TERM --kill-after=5 150 /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --final || true
    else
# Do not archive files while an unfinished trainer can still modify them.
        timeout --signal=TERM --kill-after=5 150 /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --small || true
    fi
    exit "$status"
}
trap 'tk_live_finish $?' EXIT
trap 'tk_live_finish 143 signal' TERM
trap 'tk_live_finish 138 signal' USR1
setsid /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --loop &
TK_COPY_PID=$!
setsid /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --loop-small &
TK_LOG_PID=$!
