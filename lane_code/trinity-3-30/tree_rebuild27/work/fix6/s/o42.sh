export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -j 174134 -h -o "%i %T %M %N"
ls -la --time-style=+%H:%M:%S $X/o/174134 | awk '{print $6, $7}' | tr '\n' ' '; echo
[ -e $X/o/174134/RELEASE ] && echo "RELEASE present" || echo "RELEASE absent"
pgrep -u $(id -un) -af "srun --overlap --jobid 174134" | cut -c1-150
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" ";"; echo; ps -u $(id -un) -o pid,etime,args --width 200 | grep -E "a15_dbg_174134" | grep -v -E "grep|ps -u" | cut -c1-40,120-200; echo "job dir p/q mtime: $(stat -c %y /tmp/q_22c714e1_174134/p/q | cut -c1-19)  p: $(stat -c %y /tmp/q_22c714e1_174134/p | cut -c1-19)  top: $(stat -c %y /tmp/q_22c714e1_174134 | cut -c1-19)"; du -sh /tmp/a15_dbg_174134 2>/dev/null'
