export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173056 -n -o JobID,Partition,State,Start,End,Elapsed,ExitCode,NodeList 2>/dev/null; ls -la $X/j; tail -c 1500 $X/j/173056.out 2>/dev/null
