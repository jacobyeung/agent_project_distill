export TZ=UTC; date -u +%FT%TZ
timeout 80 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c '
P=$(pgrep -f "boot.py -B -I 5.py" | while read p; do [ "$(cat /proc/$p/comm)" = python ] && echo $p; done | head -1); echo P=$P
which py-spy gdb 2>&1 | head -3
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
for t in /proc/$P/task/*; do echo $(basename $t) $(awk "{print \$14+\$15}" $t/stat) $(cat $t/comm) $(cat $t/wchan); done
sleep 10
for t in /proc/$P/task/*; do echo $(basename $t) $(awk "{print \$14+\$15}" $t/stat); done
cat /proc/$P/stack 2>&1 | head
' 2>&1 | head -60
