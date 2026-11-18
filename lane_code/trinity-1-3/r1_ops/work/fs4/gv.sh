export TZ=UTC; K=/project/community/jjyeung/okh7/x_69d2930d; STEP=${1:-100}
date -u +%FT%TZ; cat $K/o/gcs_673bc60f_m$STEP.done 2>&1; echo; cat $K/o/gcs.log 2>&1 | sed -E 's#https?://[^ "]+#[URL]#g' | tail -5
env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud gcloud storage ls -l "gs://cmu-gpucloud-jjyeung/q8/8865619b/673bc60f_m$STEP*" 2>&1 | tail -6
ls -la --time-style=+%T /project/community/jjyeung/okh7/r/673bc60f 2>&1 | tail -6
grep -E 'export|m100|m200' $K/o/171377.steps 2>/dev/null | tail -5
