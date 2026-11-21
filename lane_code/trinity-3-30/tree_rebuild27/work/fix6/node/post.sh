#!/bin/bash
# The kit's receipt steps on a scratch result, in the job shell's order, every output in scratch.
# usage: post.sh <run folder name> <layout folder name> [force]
set -uo pipefail
D=/tmp/a15_dbg_174134; SRC=${1:-n1}; DST=${2:-n1k}; FORCE=${3:-}
KIT=/project/community/jjyeung/okh7/x_22c714e1/n
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
cd "$D"
say() { echo "$(date -u +%FT%TZ) $*"; }
say "layout and census publish"
bash L.sh post.py "$D/$SRC" "$D/$DST" $FORCE > "log/post_$DST.log" 2>&1; say "layout and census publish rc=$?"
say "h.py"
bash L.sh "$KIT/b/h.py" "$D/$DST/p" "$D/$DST/v.json" > "log/h_$DST.log" 2>&1; rc=$?; say "h.py rc=$rc"
if [[ $rc == 0 ]]; then
    say "rv.py, stopped once it waits for a review file"
    A15_THREADS=8 bash L.sh --sh nice -n 10 "$PY" -B -s "$KIT/b/rv.py" "$D/$DST" "$D/$DST/v.json" 174134 > "log/rv_$DST.log" 2>&1 &
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
