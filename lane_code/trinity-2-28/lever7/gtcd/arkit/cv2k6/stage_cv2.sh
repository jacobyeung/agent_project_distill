#!/bin/bash
# Governed pull of one wheel (pattern: gtcd/arkit/stage_arkit_apple.sh).
# root = bash started stopped (never execs) -> curl (stdout) | ratelimit.py > wheel.part; renamed on PIPE_RC=0 0.
# Rehearsal: CV2_TEST_URL=<url> CV2_TEST_DIR=<dir> runs the same pipeline against a local server, skips register.py and
# stands in for the node agent (rate file + SIGCONT); nothing touches PyPI or the governor.
set -u
K=/scratch/jjyeung/orch_n30/lever7/gtcd/arkit/cv2k6; cd "$K"
LANE=lever7_gtcd_cv2; BYTES=61960165
NAME=opencv_python_headless-4.14.0.94-cp37-abi3-manylinux_2_28_x86_64.whl
URL=https://files.pythonhosted.org/packages/ae/ce/7f538891722a4f06921419d55bac6f41729258d54442861edb2de0dbdf5e/$NAME
REC=/data3/jjyeung/orch_n13_20261026/io_governor/streams/$LANE.json
T=${CV2_TEST_DIR:-}
if [ -n "$T" ]; then W=$T; URL=$CV2_TEST_URL; else W=$K; fi
OUT="$W/wheels/$NAME"; L="$W/logs"; RC="$L/rc_stage.txt"; ERR="$L/stage.err"
log(){ echo "$(date -u +%FT%TZ) $*"; }
[ "$(hostname -s)" = trinity ] && { log "refused: head node"; exit 2; }
[ -e "$OUT" ] && { log "refused: $OUT exists"; exit 2; }
if [ -z "$T" ] && [ -e "$REC" ]; then log "refused: record $REC exists"; exit 2; fi
mkdir -p "$W/wheels" "$L"; : > "$RC"
if [ -n "$T" ]; then export RATELIMIT_DIR="$T/rl"; mkdir -p "$RATELIMIT_DIR"; fi
(
  bash -c 'kill -STOP $$; curl -sS -f -L --limit-rate 8M -A "Mozilla/5.0" "$0"; rc=$?; echo "SRC_RC=$rc" >&2; exit $rc' \
       "$URL" 2>>"$ERR" \
  | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 > "$OUT.part"
  echo "PIPE_RC=${PIPESTATUS[*]}" > "$RC"
) &
SUB=$!
sleep 3
ROOT=$(pgrep -P "$SUB" -x bash | head -1)
RL=$(pgrep -P "$SUB" -f 'ratelimit.py -q -L 1000' | head -1)
log "sub=$SUB root=$ROOT rl=$RL root_state=$(awk '{print $3}' /proc/$ROOT/stat 2>/dev/null) rl_comm=$(cat /proc/$RL/comm 2>/dev/null)"
if [ -z "$ROOT" ] || [ -z "$RL" ]; then log "PID discovery failed"; exit 2; fi
for i in $(seq 20); do [ "$(cat /proc/$RL/comm 2>/dev/null)" = ratelimit ] && break; sleep 1; done
if [ -z "$T" ]; then
  /usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane "$LANE" --pid "$ROOT" --member-pid "$RL" --rl-pid "$RL" \
    --expected-bytes "$BYTES" --tier 3 --kind pull --nominal-mbps 8 --io-weight 1 --allow-resume --priority 950
  log "register rc=$?"
else
  ST=$(awk '{print $22}' /proc/$RL/stat)
  echo '{"rate": 8388608, "seq": 1}' > "$RATELIMIT_DIR/$RL.$ST.rate.next" && mv "$RATELIMIT_DIR/$RL.$ST.rate.next" "$RATELIMIT_DIR/$RL.$ST.rate"
  kill -USR1 "$RL"; kill -CONT "$ROOT"; log "test: rate 8 MiB/s set, root continued"
fi
wait "$SUB"
log "$(cat "$RC" 2>/dev/null)"
if grep -q 'PIPE_RC=0 0' "$RC" 2>/dev/null; then
  mv "$OUT.part" "$OUT"; log "size $(stat -c %s "$OUT") sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
  if [ -z "$T" ] && [ -e "$REC" ]; then mv "$REC" "${REC%.json}.done.$(date +%s)"; log "record renamed done"; fi
else
  log "FAILED; stderr tail: $(tail -3 "$ERR" 2>/dev/null | tr '\n' ' ')"
fi
log "end"
