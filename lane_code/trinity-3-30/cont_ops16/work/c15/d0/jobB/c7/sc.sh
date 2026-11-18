export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%FT%TZ; tail -c 300000 $KB/runs/359fcc3c/metrics_170111.jsonl | tail -1 | head -c 20; echo
scancel 170111; echo "scancel_rc=$? at $(date -u +%FT%TZ)"; sleep 45; squeue -h -j 170111 -o '%i %T %M' 2>&1; sacct -n -X -j 170111 -o State,ExitCode,End -P | head -1; tail -3 $KB/o/170111.w.steps
