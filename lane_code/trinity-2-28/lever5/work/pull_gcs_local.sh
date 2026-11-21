#!/bin/bash
# lever5: governed GCS pull on trinity-2-28. Args: URI GEN SHA BYTES DESTDIR LANE. Root = stopped bash producer.
set -u
URI=$1; GEN=$2; SHA=$3; BYTES=$4; DEST=$5; LANE=$6
log(){ echo "$(date -u +%FT%TZ) $*"; }
cd "$DEST"
(
  bash -c 'kill -STOP $$; /home/jjyeung/google-cloud-sdk/bin/gcloud storage cat "$0"; rc=$?; echo "SRC_RC=$rc" >&2; exit $rc' "$URI#$GEN" 2>>"$DEST/src.err" \
  | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 \
  | bash -c 'set -C; cat > 0.gz'
  echo "PIPE_RC=${PIPESTATUS[*]}" > "$DEST/rc.txt"
) &
SUB=$!
sleep 3
ROOT=$(pgrep -P "$SUB" -x bash | head -1)
RL=$(pgrep -P "$SUB" -f 'ratelimit.py -q -L 1000' | head -1)
log "sub=$SUB root=$ROOT rl=$RL root_state=$(awk '{print $3}' /proc/$ROOT/stat 2>/dev/null) rl_comm=$(cat /proc/$RL/comm 2>/dev/null)"
if [ -z "$ROOT" ] || [ -z "$RL" ]; then log "PID discovery failed"; exit 2; fi
for i in $(seq 20); do [ "$(cat /proc/$RL/comm 2>/dev/null)" = ratelimit ] && break; sleep 1; done
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane "$LANE" --pid "$ROOT" --member-pid "$RL" --rl-pid "$RL" \
  --expected-bytes "$BYTES" --tier 3 --kind pull --nominal-mbps 8 --io-weight 1 --allow-resume --priority 950
log "register rc=$?"
wait "$SUB"
log "$(cat "$DEST/rc.txt")"
test "$(stat -c %s 0.gz)" = "$BYTES" && echo "$SHA  0.gz" | sha256sum -c - && log SHA_OK
REC=/data3/jjyeung/orch_n13_20261026/io_governor/streams/$LANE.json
if grep -q 'PIPE_RC=0 0 0' "$DEST/rc.txt" && [ -e "$REC" ]; then mv "$REC" "${REC%.json}.done.$(date +%s)"; log "record renamed done"; fi
log end
