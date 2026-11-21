export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c '
cd /tmp/a15_dbg_174134
echo "== my frame audit process (the only process of mine left that holds a GPU context)"
P=$(pgrep -u $(id -u) -f "python -B -s c4.py /tmp/a15_dbg_174134/n2 admit a" | tr "\n" " "); echo "pids: $P"
for p in $P; do echo "cmd: $(tr "\0" " " < /proc/$p/cmdline | cut -c1-200)"; kill -TERM $p && echo "TERM sent to $p"; done
sleep 4
echo "== processes of this user on the node now"
ps -u $(id -un) -o pid,ppid,lstart,etime,pcpu,rss,args --width 330 | grep -v -E "ps -u|grep|sleep 15|slurm_script|srun|bash -c" | cut -c1-70,150-330 | head -40
echo "== gpus"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr "\n" ";"; echo; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr "\n" ";"; echo
echo "== scratch top level (listing only)"; ls -la --time-style=+%H:%M:%S . | cut -c1-110
echo "== tr and tr2 (listing only, nothing written)"; ls -la --time-style=+%H:%M:%S tr tr2 2>&1 | cut -c1-110 | head -40
echo "== n2k/p"; ls -la --time-style=+%H:%M:%S n2k/p n2k | cut -c1-110
echo "== my tr.log"; cat log/tr.log
'
squeue -j 174134 -h -o "%i %T %M %N"
