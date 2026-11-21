#!/bin/bash
# Second scratch run of the kit's review script, to see what its evidence step says once pose rows
# pass its room classifier: own live folder, census diagnose switch on, unresolved pose rooms accepted.
set -uo pipefail
D=/tmp/a15_dbg_174134; DST=${1:-n2k}
KIT=/project/community/jjyeung/okh7/x_22c714e1/n
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
cd "$D"
say() { echo "$(date -u +%FT%TZ) $*"; }
mkdir -p live2
for f in c0.json c1.json c2.json c3.json c4.json h0.json; do [[ -e live2/$f ]] || cp -p live/$f live2/$f; done
say "rv.py second run"
A15_DIAG=2 A15_LIVE="$D/live2" A15_THREADS=8 bash L2.sh --sh nice -n 10 "$PY" -B -s "$D/kw.py" "$KIT/b/rv.py" "$D/$DST" "$D/$DST/v.json" 174134 > log/rv2.log 2>&1 &
bg=$!
for i in $(seq 1 280); do
    if [[ -e live2/WAITING_REVIEW.json || -e live2/REVIEW_REFUSED.json ]]; then break; fi
    kill -0 "$bg" 2>/dev/null || break
    sleep 10
done
say "rv.py second run, live folder: $(ls live2 | tr '\n' ' ')"
pkill -TERM -u "$(id -u)" -f "rv.py $D/$DST " || true
wait "$bg"; say "rv.py second run ended rc=$?"
ls -la live2
say "end"
