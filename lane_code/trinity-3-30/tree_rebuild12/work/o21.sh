export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173051 -X -n -o State,Elapsed 2>/dev/null; tail -c 600 $X/j/173051.out; echo
sstat -j 173051.batch -n -o MaxRSS,AveRSS,AveCPU 2>/dev/null
