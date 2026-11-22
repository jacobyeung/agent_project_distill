#!/bin/bash
# Governed ARKit pull from Apple by HTTPS range (pattern: lever6/r0p2/stage.sh, gtcd/stage_scannet.sh).
# root = bash started stopped (never execs) -> fetch_arkit.py (tar to stdout) | ratelimit.py | tar xf - -C raw/.
# The lane starts it in tmux on trinity-2-28; do not start it without an orchestrator order.
# Rehearsal: ARKIT_TEST_DIR=<dir with plan/PLAN_ARKIT.json> runs the same pipeline against that plan (a local HTTP server),
# skips register.py and stands in for the node agent (rate file + SIGCONT); nothing touches Apple or the governor.
set -u
A=/scratch/jjyeung/orch_n30/lever7/gtcd/arkit; cd "$A"
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
LANE=lever7_gtcd_arkit; BYTES=955000000
REC=/data3/jjyeung/orch_n13_20261026/io_governor/streams/$LANE.json
T=${ARKIT_TEST_DIR:-}
if [ -n "$T" ]; then W=$T; else W=$A; fi
PLAN="$W/plan/PLAN_ARKIT.json"; OUT="$W/raw"; L="$W/logs"; RC="$L/rc_fetch.txt"; ERR="$L/fetch.err"; CAUSE="$L/fetch_cause.jsonl"
log(){ echo "$(date -u +%FT%TZ) $*"; }
[ "$(hostname -s)" = trinity ] && { log "refused: head node"; exit 2; }
[ -s "$PLAN" ] || { log "refused: no plan $PLAN"; exit 2; }
[ -e "$OUT/_FETCH_DONE.json" ] && { log "refused: $OUT already holds a finished fetch"; exit 2; }
if [ -z "$T" ] && [ -e "$REC" ]; then log "refused: record $REC exists"; exit 2; fi
mkdir -p "$OUT" "$L"; : > "$RC"
if [ -n "$T" ]; then export RATELIMIT_DIR="$T/rl"; mkdir -p "$RATELIMIT_DIR"; fi
(
  bash -c 'kill -STOP $$; "$0" -I -B "$1" "$2" "$3"; rc=$?; echo "SRC_RC=$rc" >&2; exit $rc' \
       "$PY" "$A/tools/fetch_arkit.py" "$PLAN" "$CAUSE" 2>>"$ERR" \
  | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 \
  | tar xf - -C "$OUT"
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
if [ -z "$T" ] && grep -q 'PIPE_RC=0 0 0' "$RC" 2>/dev/null && [ -e "$REC" ]; then mv "$REC" "${REC%.json}.done.$(date +%s)"; log "record renamed done"; fi
log "end"
