export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb; RS=/project/community/jjyeung/okh7/r/39504485; J=170710
date -u +%FT%TZ; cat $K/o/gcs_17c4ffa4_m100.done 2>&1; echo
env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud gcloud storage ls -l 'gs://cmu-gpucloud-jjyeung/q8/8865619b/17c4ffa4_m100*' 2>&1 | tail -6
ls -la --time-style=+%T $RS 2>&1 | tail -8; ls -la --time-style=+%T $K/runs/17c4ffa4/ $K/runs/17c4ffa4/m100 2>&1 | tail -12
ls $K/o | grep -E "^$J\.|gcs_" | tr '\n' ' '; echo; squeue -h -u jjyeung -o '%i %j %P %T' | grep -v jjy_
