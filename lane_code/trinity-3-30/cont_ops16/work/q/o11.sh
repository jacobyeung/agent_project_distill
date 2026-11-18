export TZ=UTC
timeout 100 srun --overlap --jobid 172658 -n1 --cpus-per-task=1 --mem=2G bash -c 'B=/tmp/a_172658_a2e46c0504e; ls $B; R=$B/sj/aa2e46c0504e/r; find $R -maxdepth 5 | head -30; ls -la $R/logs; tail -n 5 $R/logs/* 2>/dev/null | tail -20' 2>&1 | tail -50
