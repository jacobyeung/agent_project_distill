export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
X=/project/community/jjyeung/okh7/x_22c714e1; W=$X/w; test ! -e $W && mkdir -m 700 $W
cat > $W/g.sh <<'EOS'
set -euo pipefail; umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
W=/project/community/jjyeung/okh7/x_22c714e1/w; O=q8/8865619b/6ed2c7aa_m400.tar
for i in 0 1 2 3; do
  test ! -e "$W/$i"
  nice -n 10 gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$O.part0$i-of-04" "$W/$i.partial"
  mv "$W/$i.partial" "$W/$i"; echo "$(date -u +%TZ) part $i $(stat -c %s $W/$i)"
done
echo "$(date -u +%TZ) DONE"
EOS
cd $W && nohup bash $W/g.sh > $W/g.log 2>&1 < /dev/null & 
sleep 20; cat $W/g.log; ls -la $W
