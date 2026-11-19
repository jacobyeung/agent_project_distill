export TZ=UTC; date -u +%TZ
timeout 60 srun --jobid=173051 --overlap -n1 --mem=0 bash -c 'ps -u $USER -o pid,ppid,etime,pcpu,rss,args --sort=-pcpu | grep -v "ps -u" | head -12 | cut -c1-220; ls /tmp | grep q_22c714e1; du -sh /tmp/q_22c714e1_173051 2>/dev/null; ls /tmp/q_22c714e1_173051 2>/dev/null | head' 2>&1 | head -30
