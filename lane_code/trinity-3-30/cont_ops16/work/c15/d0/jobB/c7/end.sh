export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7; RS=/project/community/jjyeung/okh7/r/63e57182
date -u +%T; squeue -h -j 170111 -o '%i %T %M' ; sacct -n -X -j 170111 -o State,ExitCode,End -P | head -1
tail -4 $KB/o/170111.w.steps; tail -2 $KB/o/170111.steps; ls -la --time-style=+%T $RS | tail -8; ls $KB/o | grep 170111
