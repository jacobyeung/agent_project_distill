export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173051 -n -o JobID,State,Elapsed,ExitCode 2>/dev/null; squeue -u $USER -h -o '%i %P %j %T %M'
tail -n 30 $X/j/173051.out | cut -c1-250; ls -la $X/j
