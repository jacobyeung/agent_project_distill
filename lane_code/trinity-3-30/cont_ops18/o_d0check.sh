export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
K=/project/community/jjyeung/okh7
for d in $K/x_f5c353f7/o/gcs_359fcc3c_m200.done $K/x_07ca49df/o/gcs_469ddece_m544.done $K/x_07ca49df/o/gcs_469ddece_mstop.claim; do echo "== $d"; cat $d 2>&1 | head -3; done
ls $K/x_f5c353f7/runs/359fcc3c/inputs/ 2>&1 | head; ls $K/x_f5c353f7/runs/359fcc3c/inputs/prepare_*/prepared 2>&1 | head
ls $K/x_07ca49df/runs/469ddece/inputs/ 2>&1 | head
timeout 60 gsutil ls -l 'gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m200.tar*' 'gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar*' 2>&1 | tail -12
