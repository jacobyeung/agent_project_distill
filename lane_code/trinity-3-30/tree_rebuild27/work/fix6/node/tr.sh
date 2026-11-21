#!/bin/bash
# Scratch training start on the held node: the kit's launch line of t.py (torch.distributed.run,
# four ranks) with the scratch per-rank entry, two optimizer steps in the tree's smoke length.
# No publisher of the job is started; every output is under /tmp/a15_dbg_174134.
set -uo pipefail
D=/tmp/a15_dbg_174134; DST=${1:-n2k}
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
cd "$D"
say() { echo "$(date -u +%FT%TZ) $*"; }
say "acceptance stand-in"
bash L.sh accept.py "$D/$DST" > log/accept.log 2>&1; rc=$?; say "acceptance stand-in rc=$rc"
[[ $rc == 0 ]] || { tail -c 1500 log/accept.log; say "end"; exit 1; }
left=$(( $(date -u -d "17:56:30" +%s) - $(date +%s) ))
(( left > 120 )) || { say "too late to start"; exit 2; }
nvidia-smi --query-gpu=timestamp,index,memory.used,utilization.gpu --format=csv,noheader -l 10 > log/smi_train.log 2>&1 &
smi=$!
say "training start, hard stop after $left s"
A15_THREADS=8 A15_STEPS=2 timeout -s TERM -k 20 "$left" bash L.sh -m torch.distributed.run --standalone --nnodes=1 --nproc_per_node=4 --no-python /bin/bash "$D/e2.sh" "$PY" "$D/$DST/p" "$D/$DST/v2.json" > log/train.log 2>&1
say "training ended rc=$?"
pkill -TERM -u "$(id -u)" -f "torch.distributed.run" 2>/dev/null; pkill -TERM -u "$(id -u)" -f "a15_dbg_174134/u2.py" 2>/dev/null; sleep 3
kill "$smi" 2>/dev/null
ls -la rp rp/* 2>&1 | head -40
say "end"
