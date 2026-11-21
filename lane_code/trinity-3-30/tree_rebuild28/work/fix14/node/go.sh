#!/bin/bash
# fix14: two-step scratch start of the four ranks, then kill; hard kill at 17:53:30Z.
set -uo pipefail
export TZ=UTC
D=/tmp/a15_dbg_174134; T=$D/tr
KIT=/project/community/jjyeung/okh7/x_22c714e1/n
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
cd "$T"; mkdir -p log rp live j
say() { echo "$(date -u +%FT%TZ) $*"; }
say "go start on $(hostname -s); gpus: $(nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';')"
say "prep"
A15_THREADS=8 bash L3.sh "$T/prep.py" "$D/n2k" "$T/nk" > log/prep.log 2>&1; rc=$?
say "prep rc=$rc"
[[ $rc == 0 ]] || { say "STOP: prep failed"; exit 3; }
( while :; do echo "$(date -u +%T) $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | tr '\n' ' ')"; sleep 5; done ) > log/gpu.txt 2>&1 &
samp=$!
say "start of the four ranks"
date +%s > log/t0
A15_THREADS=8 setsid bash -c 'echo $$ > "$1/log/pgid"; bash "$1/L3.sh" --sh "$0" -B -s "$1/t2.py" "$1/nk/p" "$1/nk/v.json" 2>&1 | /usr/bin/python3 -B "$2/b/l.py" "$2" > "$1/log/t.log"; echo "rc=${PIPESTATUS[0]}" > "$1/log/t.rc"' "$PY" "$T" "$KIT" &
end=$(date -u -d 'today 17:53:30' +%s)
while :; do
    sleep 5
    if [[ -e log/t.rc ]]; then say "ended by itself: $(cat log/t.rc)"; break; fi
    n=$(cat log/ev_rank*.jsonl 2>/dev/null | grep -c '"kind": "STEP"')
    m=$(find rp runs -name 'metrics_*.jsonl' 2>/dev/null | xargs -r cat | grep -c .)
    if (( m >= 2 )); then say "two steps recorded (metrics lines $m, step events $n)"; break; fi
    if (( n >= 8 )); then say "8 step events; 25 s for the gather"; sleep 25; break; fi
    if (( $(date +%s) >= end )); then say "deadline 17:53:30Z reached; step events $n, metrics lines $m"; break; fi
done
pg=$(cat log/pgid 2>/dev/null)
if [[ -n "$pg" ]]; then kill -TERM -- "-$pg" 2>/dev/null; sleep 8; kill -KILL -- "-$pg" 2>/dev/null; fi
kill "$samp" 2>/dev/null
sleep 3
say "after kill; gpus: $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ';')"
ps -u "$(id -u)" -o pid,pgid,etime,args --width 160 | grep -E 'tr/(uw|t2|e2|L3|prep)' | grep -v grep
say "end"
