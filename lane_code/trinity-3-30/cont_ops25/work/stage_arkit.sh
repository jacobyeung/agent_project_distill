#!/bin/bash
# Governed /data3 -> trinity-2-28 copy of the 10 ARKit captures' selected lowres_wide frames (tar stream, ratelimit in path).
set -euo pipefail
W=/scratch/jjyeung/orch_n30/cont_ops25/work; LOG=$W/stage_arkit.log
D=/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres
SRC=/data3/shared/datasets/arkitscenes/3dod/Training
[[ "$(hostname -s)" == trinity-3-30 ]]
cd $W
setsid nohup bash -c "bash -c 'kill -STOP \$\$; tar cf - -C $SRC -T $W/list.txt; exit \$?' | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | tee >(sha256sum > $W/stage_arkit.src.sha) | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p $D && cd $D && tee >(sha256sum > $D/STREAM.sha) | tar xf - && sleep 2 && cat $D/STREAM.sha && find . -name \"*.png\" | wc -l'; echo PIPE_RC \${PIPESTATUS[*]}" > $LOG 2>&1 < /dev/null &
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
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane cont_ops25_arkit_lowres --pid $ROOT --member-pid $RL --rl-pid $RL \
  --expected-bytes 89600000 --tier 3 --kind copy --nominal-mbps 4 --allow-resume --priority 3
