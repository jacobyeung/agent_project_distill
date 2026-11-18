export TZ=UTC
K=/project/community/jjyeung/okh7/x_69d2930d/o
squeue -j 170956 -h -o "%i %T %M %N"
sstat -j 170956.batch -n -P -o AveCPU,MaxRSS,MaxDiskRead 2>/dev/null | head -2
tail -3 $K/170956.steps
ls -la --time-style=+%H:%M $K | tail -4
