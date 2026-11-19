export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173057 -X -n -o State,Elapsed 2>/dev/null; tail -c 600 $X/j/173057.out; echo
sstat -j 173057.batch -n -o MaxRSS,AveRSS,AveCPU 2>/dev/null
