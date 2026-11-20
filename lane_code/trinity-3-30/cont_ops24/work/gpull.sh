#!/bin/bash
# Governed GCS -> trinity-2-28 pull of one capture object. Usage: gpull.sh URI GENERATION SHA256 BYTES DEST_NAME PRIORITY
# Starts the pipeline with its reader stopped, registers it with the IO governor (tier 3, io-weight 1), prints the record.
set -euo pipefail
U=$1; G=$2; H=$3; N=$4; NAME=$5; PRIO=${6:-5}
W=/scratch/jjyeung/orch_n30/cont_ops24/work; LOG=$W/gpull_${NAME}.log
D=/scratch/jjyeung/orch_n30/cont_ops24_c/cap
[[ "$(hostname -s)" == trinity-3-30 ]]
cd $W
setsid nohup bash -c "bash -c 'kill -STOP \$\$; gcloud storage cat \"$U#$G\"; rc=\$?; exit \$rc' | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p $D && cd $D && set -C && cat > $NAME && test \$(stat -c %s $NAME) = $N && echo \"$H  $NAME\" | sha256sum -c -'; echo PIPE_RC \${PIPESTATUS[*]}" > $LOG 2>&1 < /dev/null &
OUTER=$!
sleep 3
ROOT=""; RL=""
for p in $(pgrep -g $(ps -o pgid= -p $OUTER | tr -d ' ')); do
  c=$(cat /proc/$p/comm 2>/dev/null || true); s=$(awk '{print $3}' /proc/$p/stat 2>/dev/null || true)
  [[ "$c" == ratelimit ]] && RL=$p
  [[ "$c" == bash && "$s" == T ]] && ROOT=$p
done
echo "outer=$OUTER root=$ROOT rl=$RL"
[[ -n "$ROOT" && -n "$RL" ]]
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane cont_ops24_$NAME --pid $ROOT --member-pid $RL --rl-pid $RL \
  --expected-bytes $N --tier 3 --kind pull --nominal-mbps 8 --io-weight 1 --allow-resume --priority $PRIO
