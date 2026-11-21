export TZ=UTC; date -u +%TZ
squeue -j 174198 -h -o '%T|%M|%N|%L'
timeout 110 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC; D=/tmp/a15_f16_174198
echo "== frames dir before the stop"; ls -la --time-style=+%H:%M:%S $D/w1/w/top/p/q/p/frames_* 2>/dev/null | cut -c1-110
bash $D/n/stop.sh coordinator-2144Z > /dev/null 2>&1
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do pgrep -u $(id -u) -f 'n/wd.sh' > /dev/null || break; sleep 2; done
W=$(pgrep -u $(id -u) -f 'n/wd.sh' | head -1); if [ -n "$W" ]; then pkill -P "$W" 2>/dev/null; kill "$W" 2>/dev/null; sleep 1; echo "watchdog $W ended by hand"; fi
echo "== stop.log"; cut -c1-330 $D/w1/log/stop.log
echo "== rc: $(cat $D/w1/log/rc 2>/dev/null)"; tail -n 1 $D/w1/log/go.log | cut -c1-200
echo "== q.err tail"; tail -c 300 $D/w1/log/q.err
echo "== tb: $(ls $D/w1/w/top/tb.txt 2>&1 | cut -c1-90)"
echo "== my processes naming a15_f16 now ($(date -u +%TZ)):"; ps -u $(id -u) -o pid=,stat=,etime=,args= --width 160 | grep 'a15_f16' | grep -v 'grep\| ps -u' | cut -c1-160
echo "== marked processes (A15_RUN=...w1):"; for p in /proc/[0-9]*; do [ -O $p ] && tr '\0' '\n' 2>/dev/null < $p/environ | grep -qx "A15_RUN=$D/w1" && echo ${p#/proc/}; done
echo "== gpus $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader 2>/dev/null | tr '\n' ';')"
echo "== end $(date -u +%TZ)"
EOS
echo "== login-node srun clients of mine naming a15_f16:"; pgrep -u $(id -u) -af 'srun --overlap --jobid 174198' | grep 'a15_f16' | cut -c1-140
date -u +%TZ
