set -e; mkdir -p /scratch/jjyeung/orch_n30/lever5_pull; cat > /scratch/jjyeung/orch_n30/lever5_pull/pull.sh <<'PULLEOF'
#!/bin/bash
# lever5: governed pull of rank 1 repeat depth return (GCS -> trinity-3-30 -> InfiniBand -> trinity-2-28).
# Runs on trinity-3-30 in tmux l5_pull. Root = stopped bash producer (first pipeline stage, never execs).
set -u
D=/scratch/jjyeung/orch_n30/lever5_pull; cd "$D"
URI='gs://cmu-gpucloud-jjyeung/q8/ae71c903/a3b73b53d92a70002a878c/0.gz'
GEN=1795284316374119
SHA=77174f7da3cd4b124be18f0015ff901ed067c2c8a5b834ae2a8ee9c02e654b4e
BYTES=37020428
LANE=lever5_r1rdepth
log(){ echo "$(date -u +%FT%TZ) $*"; }
(
  bash -c 'kill -STOP $$; /home/jjyeung/google-cloud-sdk/bin/gcloud storage cat "$0"; rc=$?; echo "SRC_RC=$rc" >&2; exit $rc' "$URI#$GEN" 2>>"$D/src.err" \
  | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 \
  | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib "set -euo pipefail; umask 077; cd /scratch/jjyeung/orch_n30/lever5/r1r/returned; set -C; cat > 0.gz; test \$(stat -c %s 0.gz) = $BYTES; echo '$SHA  0.gz' | sha256sum -c -"
  echo "PIPE_RC=${PIPESTATUS[*]}" > "$D/rc.txt"
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
log "$(cat "$D/rc.txt" 2>/dev/null)"
REC=/data3/jjyeung/orch_n13_20261026/io_governor/streams/$LANE.json
if grep -q 'PIPE_RC=0 0 0' "$D/rc.txt" 2>/dev/null && [ -e "$REC" ]; then mv "$REC" "${REC%.json}.done.$(date +%s)"; log "record renamed done"; fi
log "end"
PULLEOF
chmod +x /scratch/jjyeung/orch_n30/lever5_pull/pull.sh; tmux has-session -t l5_pull 2>/dev/null && { echo EXISTS; exit 1; }; tmux new-session -d -s l5_pull "bash /scratch/jjyeung/orch_n30/lever5_pull/pull.sh > /scratch/jjyeung/orch_n30/lever5_pull/pull.log 2>&1"; sleep 8; cat /scratch/jjyeung/orch_n30/lever5_pull/pull.log; hostname -s
