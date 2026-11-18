export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%FT%TZ; squeue -h -j 170111 -o '%i %T %M %N'; tail -2 $KB/o/170111.steps
scancel --signal=USR1 --batch 170111; echo "scancel_rc=$?"; sleep 20; tail -3 $KB/o/170111.w.steps; tail -2 $KB/o/170111.steps
