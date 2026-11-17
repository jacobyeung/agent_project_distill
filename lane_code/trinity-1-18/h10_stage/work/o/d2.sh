export TZ=UTC; date -u +%FT%TZ
timeout 90 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c '
P=2445095
for i in 1 2 3 4 5; do nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; sleep 2; done
ps -o pid,ppid,etime,pcpu,nlwp,stat,wchan:30,args -p $P --ppid $P | cut -c1-220
ps -eo pid,ppid,etime,pcpu,args | awk -v p=$P "\$2==p" | cut -c1-200
grep -E "State|Threads|VmRSS" /proc/$P/status
ls -la /proc/$P/fd 2>/dev/null | grep -v -E "socket|pipe|anon|/dev/" | tail -15 | cut -c40-250
ls /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin | grep -i spy
cat /proc/$P/task/*/stat 2>/dev/null | awk "{print \$3, \$14, \$15}" | sort | uniq -c | sort -rn | head
' 2>&1 | head -80
