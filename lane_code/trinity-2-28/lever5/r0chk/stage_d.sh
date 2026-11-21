#!/bin/bash
set -u
D=/scratch/jjyeung/orch_n30/lever5/r0chk; cd "$D"
LANE=lever5_r0frames; BYTES=4000000
log(){ echo "$(date -u +%FT%TZ) $*"; }
(
  bash -c 'kill -STOP $$; tar cf - -T "$0"; rc=$?; echo "SRC_RC=$rc" >&2; exit $rc' "$D/stage_d/list.txt" 2>>"$D/stage_d/src.err" \
  | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 \
  | tar xf - -C "$D/stage_d/frames"
  echo "PIPE_RC=${PIPESTATUS[*]}" > "$D/stage_d/rc.txt"
) &
SUB=$!
sleep 3
ROOT=$(pgrep -P "$SUB" -x bash | head -1)
RL=$(pgrep -P "$SUB" -f 'ratelimit.py -q -L 1000' | head -1)
log "sub=$SUB root=$ROOT rl=$RL root_state=$(awk '{print $3}' /proc/$ROOT/stat 2>/dev/null) rl_comm=$(cat /proc/$RL/comm 2>/dev/null)"
if [ -z "$ROOT" ] || [ -z "$RL" ]; then log "PID discovery failed"; exit 2; fi
for i in $(seq 20); do [ "$(cat /proc/$RL/comm 2>/dev/null)" = ratelimit ] && break; sleep 1; done
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane "$LANE" --pid "$ROOT" --member-pid "$RL" --rl-pid "$RL" \
  --expected-bytes "$BYTES" --tier 3 --kind pull --nominal-mbps 8 --allow-resume --priority 950
log "register rc=$?"
wait "$SUB"
log "$(cat "$D/stage_d/rc.txt" 2>/dev/null)"
REC=/data3/jjyeung/orch_n13_20261026/io_governor/streams/$LANE.json
if grep -q 'PIPE_RC=0 0 0' "$D/stage_d/rc.txt" 2>/dev/null && [ -e "$REC" ]; then mv "$REC" "${REC%.json}.done.$(date +%s)"; log "record renamed done"; fi
log "end"
