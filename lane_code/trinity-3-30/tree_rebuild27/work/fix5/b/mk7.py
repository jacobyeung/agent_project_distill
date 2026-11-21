# Builds jn7.sh = jn6.sh + traceback copy (X/o/<job>/tb.txt) + node hold on a failure before training.
# Usage: python3 mk7.py <jn6.sh> <j7.py> <jn7.sh>
import sys
s=open(sys.argv[1]).read();j7=open(sys.argv[2]).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
assert 'PYJ7' not in j7
# 1. Hold constants and the hold, defined before finish() so the EXIT trap can call it.
rep('''# One final attempt: 120 s, then at most 15 s for fixed-text fallback.
''','''# jn7 node hold: a failure before training keeps the job (and its node directory) for at most 180 min.
J7_HOLD_S=10800
J7_POLL_S=15
J7_SIG=''
hold() {
    local status=$1 now deadline reason='' pid rc job=${SLURM_JOB_ID:-0}
    # Never after a TERM/USR1 reached the work (stop path), never on success, never without the helper.
    [[ $status != 0 && -z ${J7_SIG:-} && -f ${N:-/nonexistent}/j7.py ]] || return 0
    # Training has started once rv.py installed the review pin (p/rv.json) or j.sh opened t.log for t.py.
    if [[ -e $N/t.log || -L $N/t.log || -e $N/p/rv.json || -L $N/p/rv.json ]]; then return 0; fi
    now=$(date +%s); deadline=$((now + J7_HOLD_S))
    # Leave Slurm's TERM warning (600 s) and the publication after it untouched.
    if [[ ${SLURM_JOB_END_TIME:-} =~ ^[0-9]+$ ]] && (( SLURM_JOB_END_TIME - 660 < deadline )); then deadline=$((SLURM_JOB_END_TIME - 660)); fi
    (( deadline > now + 60 )) || return 0
    # No published HOLD.txt, no hold: nobody would know the node is held.
    if ! timeout --signal=KILL 30s python3 -B -I -s "$N/j7.py" hold "$N" "$X" "$job" "$status" "${step:-setup}" "$now" "$deadline" </dev/null >/dev/null 2>&1; then
        echo "$(date -u +%FT%TZ) HOLD record not written; no hold"; return 0
    fi
    echo "$(date -u +%FT%TZ) HOLD status=$status until $(date -u -d "@$deadline" +%FT%TZ) or $X/o/$job/RELEASE"
    # TERM/USR1 (scancel, time limit) end the hold at once.
    trap 'reason=signal' TERM USR1
    while [[ -z $reason ]]; do
        if (( $(date +%s) >= deadline )); then reason=timeout; break; fi
        timeout --signal=KILL 10s python3 -B -I -s "$N/j7.py" poll "$X" "$job" </dev/null >/dev/null 2>&1 &
        pid=$!; wait "$pid"; rc=$?
        if [[ -n $reason ]]; then kill -KILL "$pid" 2>/dev/null; break; fi
        if [[ $rc == 0 ]]; then reason=release; break; fi
        sleep "$J7_POLL_S" </dev/null >/dev/null 2>&1 &
        pid=$!; wait "$pid"
        if [[ -n $reason ]]; then kill -KILL "$pid" 2>/dev/null; fi
    done
    trap '' TERM USR1
    echo "$(date -u +%FT%TZ) HOLD end reason=$reason status=$status"
    timeout --signal=KILL 15s python3 -B -I -s "$N/j7.py" end "$X" "$job" "$status" "$reason" "$now" </dev/null >/dev/null 2>&1 || true
}
# One final attempt: 120 s, then at most 15 s for fixed-text fallback.
''')
# 2. Traceback copy right after the failure text, before the live snapshot (priority order).
rep('''        ' bash "$X" "${SLURM_JOB_ID:-0}" "$message" "$status" || true
    fi
''','''        ' bash "$X" "${SLURM_JOB_ID:-0}" "$message" "$status" || true
    fi
    # The kit's raw traceback file, at most 200 KB, on every failure (jn7).
    if [[ $status != 0 && -f ${N:-/nonexistent}/j7.py ]]; then
        timeout --signal=KILL 30s python3 -B -I -s "$N/j7.py" tb "$N" "$X" "${SLURM_JOB_ID:-0}" "$status" </dev/null >/dev/null 2>&1 || true
    fi
''')
# 3. The hold, after every publication, before the exit with the original status.
rep('''        timeout --signal=KILL 30s python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "${SLURM_JOB_ID:-0}" "$$" 120 once final </dev/null >/dev/null 2>&1 || true
    fi
    exit "$status"
}
''','''        timeout --signal=KILL 30s python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "${SLURM_JOB_ID:-0}" "$$" 120 once final </dev/null >/dev/null 2>&1 || true
    fi
    hold "$status"
    exit "$status"
}
''')
# 4. Write the helper after the live mirror; never fatal (no helper means no tb.txt and no hold).
rep('''step=setup
printf''','''step=holdkit
if cat > "$N/j7.part" <<'PYJ7'
'''+j7+'''PYJ7
then
    mv -f -- "$N/j7.part" "$N/j7.py" || echo "$(date -u +%FT%TZ) hold helper not installed"
else
    echo "$(date -u +%FT%TZ) hold helper not written"
fi
step=setup
printf''')
# 5. Record a TERM/USR1 forwarded to the work: that is the stop path, never held.
rep('''trap 'forward TERM' TERM
trap 'forward USR1' USR1
''','''trap 'J7_SIG=TERM; forward TERM' TERM
trap 'J7_SIG=USR1; forward USR1' USR1
''')
open(sys.argv[3],'w').write(s)
print('built')
