# Builds jn6.sh = jn5.sh + live mirror (j6.py embedded). Usage: python3 mk.py (in this folder)
s=open('jn5.sh').read(); j6=open('j6.py').read()
a="""    if [[ -n ${J2_PID:-} ]]; then kill -KILL -- "-$J2_PID" 2>/dev/null || true; fi
"""
assert s.count(a)==1
s=s.replace(a,a+"""    # Stop the live mirror, then take one bounded final snapshot before the final publish.
    if [[ -n ${J6_PID:-} ]]; then kill -KILL -- "-$J6_PID" 2>/dev/null || true; fi
    if [[ -f ${N:-/nonexistent}/j6.py ]]; then
        timeout --signal=KILL 40s python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "${SLURM_JOB_ID:-0}" "$$" 120 once final </dev/null >/dev/null 2>&1 || true
    fi
""")
b="""J2_PID=$!
step=setup
"""
assert s.count(b)==1
s=s.replace(b,"""J2_PID=$!
# Live mirror every 120 s into $X/o/<job>_live (memory, disk, screened tails, gate state); never fatal.
step=mirror
if cat > "$N/j6.py" <<'PYJ6'
"""+j6+"""PYJ6
then
    setsid python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" 120 loop </dev/null >>"$N/j6.err" 2>&1 &
    J6_PID=$!
else
    echo "$(date -u +%FT%TZ) live mirror not written"
fi
step=setup
""")
open('jn6.sh','w').write(s)
