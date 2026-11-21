export TZ=UTC; date -u +%TZ
squeue -j 174198 -h -o '%T|%M|%N|%L'
timeout 100 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC; D=/tmp/a15_f16_174198
for i in 1 2 3 4 5 6 7 8; do grep -q 'proof: ps lines' $D/w1/log/stop.log 2>/dev/null && break; sleep 5; done
echo "== stop.log"; cut -c1-330 $D/w1/log/stop.log
echo "== rc: $(cat $D/w1/log/rc 2>/dev/null)"; tail -n 2 $D/w1/log/go.log | cut -c1-200
echo "== q.err tail"; tail -c 400 $D/w1/log/q.err
echo "== tb"; tail -c 500 $D/w1/w/top/tb.txt 2>/dev/null
echo "== my processes naming a15_f16 now:"; ps -u $(id -u) -o pid=,stat=,etime=,args= --width 160 | grep 'a15_f16' | grep -v 'grep\| ps -u' | cut -c1-160
echo "== marked processes (A15_RUN=...w1):"; for p in /proc/[0-9]*; do [ -O $p ] && tr '\0' '\n' 2>/dev/null < $p/environ | grep -qx "A15_RUN=$D/w1" && echo ${p#/proc/}; done
echo "== frames dir at the stop"; ls -la --time-style=+%H:%M:%S $D/w1/w/top/p/q/p/frames_* 2>/dev/null | cut -c1-110
echo "== q/RESULT.json: $(ls $D/w1/w/top/p/q/RESULT.json 2>&1 | cut -c1-80)"
echo "== gpus $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader 2>/dev/null | tr '\n' ';')"
echo "== df $(df -h /tmp | tail -1 | awk '{print $3"/"$2}')"
EOS
echo "== login-node srun clients of mine for this job naming a15_f16:"; pgrep -u $(id -u) -af 'srun --overlap --jobid 174198' | grep 'a15_f16' | cut -c1-140
date -u +%TZ
