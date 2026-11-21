export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c '
cd /tmp/a15_dbg_174134
echo "== processes of this user on the node now (read only)"
ps -u $(id -un) -o pid,ppid,lstart,etime,pcpu,rss,args --width 400 | cut -c1-74,150-400 | grep -v -E "sleep 15|ps -u" | head -60
echo "== gpus"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr "\n" ";"; echo; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr "\n" ";"; echo
echo "== scratch top level"; ls -la --time-style=+%H:%M:%S . | cut -c1-110
echo "== tr and tr2 (listing only)"; ls -la --time-style=+%H:%M:%S tr tr2 2>&1 | cut -c1-110 | head -50
echo "== n2k/p and n2k"; ls -la --time-style=+%H:%M:%S n2k/p n2k | cut -c1-110
echo "== my tr.log"; cat log/tr.log
echo "== eva tail"; grep -c . n2/eva.jsonl; tail -n 1 n2/eva.jsonl | cut -c1-700
echo "== c4a log tail"; tail -c 700 log/c4a.log
'
squeue -j 174134 -h -o "%i %T %M %N"
