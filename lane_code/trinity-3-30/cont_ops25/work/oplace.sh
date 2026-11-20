#!/bin/bash
# Governed head-node push of the K3c placement stream (o_place_head.sh + place.tar) to Orchard through tools/ossh.sh.
set -euo pipefail
W=/scratch/jjyeung/orch_n30/cont_ops25/work; LOG=$W/oplace.log; K=/dev/shm/c25/k3
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
[[ "$(hostname -s)" == trinity-3-30 ]]
cd $W
setsid nohup bash -c "bash -c 'kill -STOP \$\$; cat $K/o_place_head.sh $K/place.tar; exit \$?' | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | timeout 600 bash $O 'bash -s'; echo PIPE_RC \${PIPESTATUS[*]}" > $LOG 2>&1 < /dev/null &
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
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane cont_ops25_oplace --pid $ROOT --member-pid $RL --rl-pid $RL \
  --expected-bytes 44688451 --tier 3 --kind push --nominal-mbps 8 --io-weight 1 --allow-resume --priority 3
