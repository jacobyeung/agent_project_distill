export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
K=/project/community/jjyeung/okh7/x_69d2930d
cat $K/o/gcs_673bc60f_m100.done
gsutil ls -l "gs://cmu-gpucloud-jjyeung/q8/8865619b/673bc60f_m100.tar*" 2>&1 | head
echo TARB64; cd $K/runs/673bc60f && tar cf - inputs/data_receipt.json inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/result.json binding.json | base64 -w0; echo
