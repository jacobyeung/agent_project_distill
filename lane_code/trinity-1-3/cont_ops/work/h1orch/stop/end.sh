export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb; RS=/project/community/jjyeung/okh7/r/39504485; J=170710
date -u +%T; squeue -h -j $J -o '%i %T %M'; sacct -n -X -j $J -o State,ExitCode,End -P | head -1
tail -4 $K/o/$J.w.steps; tail -3 $K/o/$J.steps; ls -la --time-style=+%T $RS | tail -8; ls $K/o | grep -E "^$J\."
