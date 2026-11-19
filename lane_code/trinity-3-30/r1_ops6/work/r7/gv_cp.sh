export TZ=UTC; K=/project/community/jjyeung/okh7/x_ee227714; STEP=${1:-400}
date -u +%FT%TZ; cat $K/o/gcs_6ed2c7aa_m$STEP.done 2>&1; echo; cat $K/o/gcs.log 2>&1 | sed -E 's#https?://[^ "]+#[URL]#g' | tail -5
env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud gcloud storage ls -l "gs://cmu-gpucloud-jjyeung/q8/8865619b/6ed2c7aa_m$STEP*" 2>&1 | tail -6
ls -la --time-style=+%T /project/community/jjyeung/okh7/r/6ed2c7aa 2>&1 | tail -6
grep -E 'export|m400|m600' $K/o/172660.steps 2>/dev/null | tail -5
