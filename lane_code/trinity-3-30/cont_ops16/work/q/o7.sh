which gsutil gcloud 2>&1 | head -2
timeout 100 gsutil ls gs://cmu-gpucloud-jjyeung/q8/ 2>&1 | head -30
