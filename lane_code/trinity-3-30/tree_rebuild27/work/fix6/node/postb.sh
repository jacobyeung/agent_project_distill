#!/bin/bash
# The kit's receipt steps in scratch while the forward of the walk goes on: wait for the census of
# the diagnose-mode publish, lay out a node folder, then h.py, rv.py and the gate copy in the job
# shell's order. Every output is in scratch. usage: postb.sh <run folder> <layout folder> <tag> <census folder>
set -uo pipefail
D=/tmp/a15_dbg_174134; SRC=${1:-n2}; DST=${2:-n2k}; TAG=${3:-b}; EARLY=${4:-n2f}
KIT=/project/community/jjyeung/okh7/x_22c714e1/n
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
cd "$D"
say() { echo "$(date -u +%FT%TZ) $*"; }
say "wait for the census receipt of $EARLY"
for i in $(seq 1 300); do
    [[ -e "$EARLY/c5.json" ]] && break
    pgrep -u "$(id -u)" -f "post2.py" > /dev/null || break
    sleep 10
done
say "census receipt present: $([[ -e $EARLY/c5.json ]] && echo yes || echo no)"
say "layout"
bash L.sh post3.py "$D/$SRC" "$D/$DST" "$TAG" "$D/$EARLY" > "log/post3_$DST.log" 2>&1; say "layout rc=$?"
say "h.py"
A15_DIAG=1 bash L.sh kw.py "$KIT/b/h.py" "$D/$DST/p" "$D/$DST/v.json" > "log/h_$DST.log" 2>&1; rc=$?; say "h.py rc=$rc"
if [[ $rc == 0 ]]; then
    say "rv.py, stopped once it waits for a review file"
    A15_DIAG=1 A15_THREADS=8 bash L.sh --sh nice -n 10 "$PY" -B -s "$D/kw.py" "$KIT/b/rv.py" "$D/$DST" "$D/$DST/v.json" 174134 > "log/rv_$DST.log" 2>&1 &
    bg=$!
    for i in $(seq 1 240); do
        if [[ -e live/WAITING_REVIEW.json || -e live/REVIEW_REFUSED.json ]]; then break; fi
        kill -0 "$bg" 2>/dev/null || break
        sleep 10
    done
    say "rv.py live folder: $(ls live | tr '\n' ' ')"
    pkill -TERM -u "$(id -u)" -f "rv.py $D/$DST " || true
    wait "$bg"; say "rv.py ended rc=$?"
fi
say "gate copy"
mkdir -p xr/o/174134
[[ -e xr/o/174134/live ]] || ln -s "$D/live" xr/o/174134/live
python3 -B -I -s /tmp/q_22c714e1_174134/j6.py "$KIT" "$D/$DST" "$D/xr" 174134 $$ 120 once gate; say "gate copy rc=$?"
ls -la live xr/o/174134_gate 2>&1
say "end"
