export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
squeue -u $USER -h -o "%i %P %j %T %r"; sacct -j 174085 -n -P -o JobID,State,ExitCode,Start,End,Elapsed,NodeList,Reason | head -5
scontrol show job 174085 2>&1 | head -30 | cut -c1-200; ls -la $X/o/174085 $X/o/174085_live 2>&1 | head; tail -20 $X/o/174085/j2.log 2>&1; tail -20 $X/o/174085/j2.err 2>&1
