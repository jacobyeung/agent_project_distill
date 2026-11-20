from common import *
source=L.parent/'work/dbb2.py'
assert J.sha(source)=='a7cbfb9f3093ee50bf373838cd952405de190cb8b5dbcc29a0ab0aa1a48d06e5'
replace(L/'out/dbb2.py',source.read_bytes())
loop='''tk_db_loop() {
    local node="$1" output="$2" helper="$3" attempt
    for ((attempt=1; attempt<=180; attempt++)); do
        if [[ -f "$output/routing_selection.json" ]]; then
            if python3 -B -I -s "$helper" "$node" "$output"; then return 0; fi
        fi
        if (( attempt < 180 )); then sleep 60; fi
    done
    return 1
}
'''
(D/'db_loop.sh').write_text(loop)
s=(L/'out/jd.sh').read_text()
needle='source "$ROOT/b/ep.sh"\n'
s=s.replace(needle,needle+loop+'''
export -f tk_db_loop
setsid bash -c 'tk_db_loop "$1" "$2" "$3"' bash "$N" "/project/community/jjyeung/okh7/x_22c714e1/o/$SLURM_JOB_ID" "/project/community/jjyeung/okh7/x_22c714e1/dbb2.py" &
TK_DB_PID=$!
tk_discovery_finish() {
    local status="$1" signal_mode="${2:-}"
    if [[ -n "${TK_DB_PID:-}" ]]; then
        kill -TERM -- "-$TK_DB_PID" 2>/dev/null || true
        wait "$TK_DB_PID" 2>/dev/null || true
    fi
    tk_evidence_finish "$status" "$signal_mode"
}
trap 'tk_discovery_finish $?' EXIT
trap 'tk_discovery_finish 143 signal' TERM
trap 'tk_discovery_finish 138 signal' USR1
''')
replace(L/'out/jd.sh',s,0o755)
