export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o '%.10i %.10P %.22j %.8T %.10M %R'; sacct -j 173051 -X -n -o JobID,State,Elapsed,ExitCode 2>/dev/null | head -3
ls -la $X/j/; tail -c 1200 $X/j/173051.out 2>/dev/null
sstat -j 173051.batch -n -o MaxRSS,AveCPU 2>/dev/null | head -2
ls /project/community/jjyeung/okh7/l_94a76bda/in | tr "\n" " "
