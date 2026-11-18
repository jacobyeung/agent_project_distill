export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb; J=170710
date -u +%FT%TZ; squeue -h -j $J -o '%i %T %M %N'; tail -2 $K/o/$J.steps
scancel --signal=USR1 --batch $J; echo "scancel_rc=$?"; sleep 20; tail -3 $K/o/$J.w.steps; tail -2 $K/o/$J.steps
