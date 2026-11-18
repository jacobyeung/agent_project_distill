export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7; RS=/project/community/jjyeung/okh7/r/63e57182
date -u +%T; squeue -h -j 170111 -o '%i %T %M'; tail -3 $KB/o/170111.w.steps | cut -c1-150; tail -2 $KB/o/170111.steps | cut -c1-150; ls -la --time-style=+%T $RS | grep -v 'RUN\|binding\|total\| \.$\| \.\.$'; ls --time-style=+%T -la $KB/o | grep 'gcs_359fcc3c_\|170111.SLOT\|170111.gslot' | tail -4
tail -c 300000 $KB/runs/359fcc3c/metrics_170111.jsonl | tail -1 | head -c 20; echo
