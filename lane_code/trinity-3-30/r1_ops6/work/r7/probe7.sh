#!/bin/bash
# r1_ops7: read-only: the trainer namespace's bind sources (mountinfo) and process tree, for the stop-step plan
export TZ=UTC; date -u +%FT%TZ
timeout 120 srun --overlap --jobid 172660 -n1 -N1 timeout 90 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-330
PID=$(ps -u $(id -u) -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
echo "rank $PID; tree:"; ps -u $(id -u) -o pid,ppid,etimes,comm,args --forest | grep -v -E "ps -u|grep" | cut -c1-250 | head -30
echo "== mountinfo (target, source root, fs)"; awk '{for(i=1;i<=NF;i++) if($i=="-"){fs=$(i+1);src=$(i+2)}; print $5, $4, fs, src}' /proc/$PID/mountinfo | grep -v -E "^/(proc|dev|sys)" | head -60
echo "== host /tmp/jjyeung"; ls -la /tmp/jjyeung /tmp/jjyeung/a_6ed2c7aa 2>&1 | head; echo "TK_JOBDIR=$(tr '\0' '\n' < /proc/$PID/environ | grep -E '^TK_JOBDIR=' | cut -d= -f2)"
STEP
