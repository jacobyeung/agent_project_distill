S=/dev/shm/jjyeung/b05; date -u +%T; tmux ls 2>&1 | head; tail -c 1500 $S/pilot2_console.log; echo; ps -eo pid,user,etime,args | grep -v grep | grep -i "owngrd\|vnice" | cut -c1-200
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader; nvidia-smi -L | sed -n 3p
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader); do ps -o pid,user,etime,args -p $p | tail -1 | cut -c1-160; done
ls -la $S/pilot2; tail -c 600 $S/pilot2/train.jsonl
ls -la /tmp/terminator/ 2>/dev/null | grep jjyeung | head
