set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
date -u
P=/project/community/jjyeung/okh7/x27ret
echo "== pool write test"
timeout 60 bash -c "dd if=/dev/urandom of=$P/.wtest_op bs=1M count=4 conv=fsync 2>&1 | tail -1"; echo rc=$?
S1=$(sha256sum $P/.wtest_op | cut -c1-64); echo pool_sha=$S1
echo "== gcs prefix write test"
timeout 90 gcloud storage cp $P/.wtest_op gs://cmu-gpucloud-jjyeung/q8/x27r/_wtest/wtest_op 2>&1 | tail -2; echo rc=$?
S2=$(timeout 90 gcloud storage cat gs://cmu-gpucloud-jjyeung/q8/x27r/_wtest/wtest_op | sha256sum | cut -c1-64); echo gcs_sha=$S2
[ "$S1" = "$S2" ] && echo GCS_READBACK_OK
: > $P/.wtest_op
squeue -u jjyeung -p general -o "%.10i %.28j %.8T %.20S %R"
