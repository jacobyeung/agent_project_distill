export TZ=UTC; date -u +%TZ
timeout 60 srun --overlap --jobid=174113 -N1 -n1 bash -c 'ps -eo pid,ppid,etime,pcpu,rss,args --sort=-pcpu -u $USER | head -12 | cut -c1-230; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader; ls -la --time-style=+%H:%M:%S /tmp/q_22c714e1/p/q 2>/dev/null | tail -15'
