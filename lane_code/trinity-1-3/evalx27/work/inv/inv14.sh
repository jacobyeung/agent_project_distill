set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
timeout 200 gcloud storage ls -l 'gs://cmu-gpucloud-jjyeung/**' > /home/jjyeung/okit/tmp/gsls_evalx27.txt 2>&1
echo rc=$?; wc -l /home/jjyeung/okit/tmp/gsls_evalx27.txt; tail -2 /home/jjyeung/okit/tmp/gsls_evalx27.txt
grep -E '^ *(3686400|72160) ' /home/jjyeung/okit/tmp/gsls_evalx27.txt | head
grep -E '2026-11-1[45]T' /home/jjyeung/okit/tmp/gsls_evalx27.txt | grep -v '/q8/8865619b/469ddece_m' | sort -k2 | head -120
