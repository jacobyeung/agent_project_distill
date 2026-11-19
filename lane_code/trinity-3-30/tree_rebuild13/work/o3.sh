export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173076
squeue -j $J -h -o "%i %P %T %M %R %N" 2>/dev/null; sacct -j $J -n -X -o JobID,State,Elapsed,ExitCode 2>/dev/null | head -2
squeue -p preempt -h -o "%T %u" | sort | uniq -c | head; sinfo -p preempt -h -o "%a %D %T %G" | head -5
test -f $X/j/$J.out && { stat -c %s $X/j/$J.out; grep -v "_cgroup_procs_check\|unable to read" $X/j/$J.out | tail -c 2500; }

if squeue -j $J -h -o %T | grep -q RUNNING; then timeout 60 srun --jobid=$J --overlap -n1 --mem=0 bash -c 'cg=$(cat /proc/self/cgroup | head -1 | cut -d: -f3); d=/sys/fs/cgroup$cg; for i in 1 2 3; do d=$(dirname $d); echo "$d cur=$(cat $d/memory.current 2>/dev/null) $(grep -E "^(anon|file|shmem) " $d/memory.stat 2>/dev/null | tr "\n" " ")"; done' 2>&1 | head -5; fi
