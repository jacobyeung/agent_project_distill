#!/bin/bash
# Polls one run folder on the held node every 2.5 minutes and exits as soon as its event file shows a
# new DONE, ERROR, WARNING or END line beyond the first $1 lines, or its process is gone.
# usage: watch.sh <lines already seen> <run folder> <log name> <process pattern>
F=/scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6
SEEN=${1:-0}; NODE=${2:-n1}; LOGN=${3:-c1}; PAT=${4:-c.py}; EVN=${5:-ev}; K="${NODE}_$EVN"
for i in $(seq 1 40); do
    {
        echo 'export TZ=UTC; date -u +%TZ'
        echo "timeout 60 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; echo ==EV; cat $NODE/$EVN.jsonl 2>/dev/null; echo ==LOG; tail -c 1200 log/$LOGN.log 2>/dev/null | grep -v \"^EV \" | tail -6; echo ==PROC; pgrep -u \$(id -un) -af \"$PAT\" | grep -v pgrep | cut -c1-120; echo ==GPU; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr \"\\n\" \";\"; echo'"
        echo 'squeue -j 174134 -h -o "%i %T %M %N"'
    } | bash "$F/s/oq.sh" > "$F/rd/w_$K.out" 2> "$F/rd/w_$K.err"
    awk '/^==EV/{f=1;next} /^==LOG/{f=0} f' "$F/rd/w_$K.out" > "$F/rd/ev_$K.jsonl"
    total=$(grep -c . "$F/rd/ev_$K.jsonl")
    new=$(tail -n +$((SEEN + 1)) "$F/rd/ev_$K.jsonl" | grep -E '"kind": "(DONE|ERROR|WARNING|END)"' | cut -c1-900)
    proc=$(awk '/^==PROC/{f=1;next} /^==GPU/{f=0} f' "$F/rd/w_$K.out" | grep -c .)
    if [[ -n "$new" ]]; then echo "$(date -u +%TZ) events=$total"; echo "$new"; exit 0; fi
    if [[ "$proc" == 0 ]]; then echo "$(date -u +%TZ) events=$total process gone"; tail -5 "$F/rd/w_$K.out"; exit 0; fi
    sleep 150
done
echo "$(date -u +%TZ) events=$total no new event in the watch window"
