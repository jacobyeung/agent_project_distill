set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
echo "==== code_f665 members"; timeout 60 gcloud storage cat gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/code_f665b6efa2cdac0c.tar | tar tvf - | awk '{print $3,$6}' | head -80
echo "==== code_4d05 members"; timeout 60 gcloud storage cat gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/code_4d05c37b29479787.tar | tar tvf - | awk '{print $3,$6}' | head -120
echo "==== runtime shas"; cat /home/jjyeung/okit/p/d59945c1/SHA256SUMS.* /project/community/jjyeung/okh7/SHA256SUMS.* /project/community/jjyeung/cp4tk_rt/kit/SHA256SUMS.big /home/jjyeung/okit/u/4d66fc2a/SHA256SUMS.* 2>/dev/null | grep -E '07006213|56c7705a|4b11b4df|e3189038|ae9247f7'
R=/home/jjyeung/okit/evalx_results/ebe307cf4/result.tar.gz
for f in metadata/NATIVE_RUNTIME.json metadata/STAGING.json metadata/ORCHARD_NATIVE.json; do echo "==== $f"; tar xzOf $R $f | head -c 6000; echo; done
