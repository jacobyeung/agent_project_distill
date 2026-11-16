export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7; RS=/project/community/jjyeung/okh7/r/63e57182
date -u +%FT%TZ; cat $KB/o/gcs_359fcc3c_m200.done; echo
env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud gcloud storage ls -l 'gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m200*' 2>&1 | tail -6
ls -la $RS; ls $KB/o | grep '^170111\.' ; squeue -h -u jjyeung -o '%i %j %P %T' | grep -v jjy_
