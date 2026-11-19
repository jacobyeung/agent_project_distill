export TZ=UTC; date -u +%FT%TZ
K=/project/community/jjyeung/okh7/x_ee227714
squeue -j 172660 -o '%i %T %M %R'
wc -l $K/o/172660.err; grep -v cgroup $K/o/172660.err | tail -5 | cut -c1-200; grep -c cgroup $K/o/172660.err; tail -3 $K/o/172660.steps | cut -c1-200
ls -la --time-style=+%H:%M:%S $K/o/ | grep 172660 | awk '{print $5,$6,$7}'
ls -la --time-style=+%H:%M:%S $K/runs/6ed2c7aa 2>&1 | awk '{print $5,$6,$7}' | tail -n +2
sstat -j 172660.batch -o JobID,AveCPU,MaxRSS 2>&1 | tail -2
