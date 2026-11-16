set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
C=/project/community/jjyeung
echo "==== gs top"; timeout 60 gcloud storage ls gs://cmu-gpucloud-jjyeung/ 2>&1 | head -40
echo "==== gs q8"; timeout 60 gcloud storage ls gs://cmu-gpucloud-jjyeung/q8/ 2>&1 | head -40
echo "==== gs q8/8865619b"; timeout 90 gcloud storage ls -l gs://cmu-gpucloud-jjyeung/q8/8865619b/ 2>&1 | head -80
for a in 3e0e8a36 8b677689; do echo "==== alias $a"; ls -la $C/$a/; for d in $C/$a/*/; do echo "$d $(ls $d | wc -l) $(du -sh $d 2>/dev/null | cut -f1)"; done; done
echo "==== f3069074"; ls -laL $C/f3069074.tar; tar tvf $C/f3069074.tar | head -30
echo "==== official tree"; ls -la $C/official_reads/tree/official $C/official_reads/tree/official/* | head -40
