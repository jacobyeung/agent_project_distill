export TZ=UTC; date -u +%TZ
timeout 60 srun --jobid=173051 --overlap -n1 --mem=0 bash -c 'cg=$(cat /proc/self/cgroup | head -1 | cut -d: -f3); for d in /sys/fs/cgroup$cg /sys/fs/cgroup$(dirname $cg) /sys/fs/cgroup$(dirname $(dirname $cg)); do [ -f $d/memory.stat ] && { echo $d; grep -E "^(anon|file|shmem|file_dirty|active_file|inactive_file) " $d/memory.stat; cat $d/memory.current $d/memory.max 2>/dev/null; }; done; ps -eo rss,comm --sort=-rss | head -5' 2>&1 | head -40
sstat -j 173051.batch -n -o MaxRSS,AveRSS 2>/dev/null; tail -c 300 /project/community/jjyeung/okh7/x_22c714e1/j/173051.out
