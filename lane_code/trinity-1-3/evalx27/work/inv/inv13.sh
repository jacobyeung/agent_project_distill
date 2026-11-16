set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
C=/project/community/jjyeung
echo "==== gs evalx_native"; timeout 90 gcloud storage ls -l -r gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/ 2>&1 | head -80
echo "==== gs state-copy"; timeout 60 gcloud storage ls gs://cmu-gpucloud-jjyeung/q8/8865619b/state-copy/ 2>&1 | head -20
echo "==== gs q8/8f11536b"; timeout 60 gcloud storage ls -l gs://cmu-gpucloud-jjyeung/q8/8f11536b/ 2>&1 | head -30
echo "==== cache"; ls -la $C/cache; ls $C/cache/* | head -60
echo "==== vview"; ls $C/official_reads/vview/arkitscenes | wc -l; ls -la $C/official_reads/vview/scannet | head -5; ls $C/official_reads/vview/scannet | wc -l; ls $C/official_reads/vview/scannetpp | wc -l
echo "==== expect68 head"; head -c 1500 $C/official_reads/expect68.json; echo
echo "==== hf datasets"; ls -d $C/*/hf* $C/*/*/datasets--nyu-visionx* $C/cache/*/datasets--* 2>/dev/null | head
grep -n "VSI-Bench\|parquet\|load_dataset\|test-00000\|jsonl" $C/official_reads/tree/official/run_eval_hc.py | head -30
