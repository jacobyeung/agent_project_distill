export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb
date -u +%TZ; squeue -u jjyeung -h -o "%i %j %P %T %M %r" | grep -v -E '^1678|^16827|^167739'
cat $K/o/gcs_17c4ffa4_m100.done 2>/dev/null; ls $K/o | grep -E 'gcs_17c4|H1_STOP|mstop' | tr '\n' ' '; echo
tail -n 3 $K/o/170710.steps | cut -c1-200; tail -n 2 $K/o/170710.w.steps | cut -c1-200
ls /project/community/jjyeung/okh7/ae71c903/af35386aa3e/
