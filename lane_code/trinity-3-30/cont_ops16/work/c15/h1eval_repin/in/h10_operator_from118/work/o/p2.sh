export TZ=UTC
P=/project/community/jjyeung
echo "== evalx env versions"; timeout 60 nice -n 19 grep -rh -o -E '"(transformers|torch|torchvision|scipy|timm|iopath|pycocotools|ftfy)": *"[^"]+"' /home/jjyeung/okit/evalx_results /home/jjyeung/okit/ifp0_results 2>/dev/null | sort | uniq -c | head -30
echo "== c7d31ddd"; ls -la $P/c7d31ddd | head -30
echo "== i_bb09a77d"; ls -la $P/okh7/i_bb09a77d | head -40
echo "== i_1be16f28"; ls -la $P/okh7/i_1be16f28 | head -40
echo "== cp4tk_rt/kit"; ls -la $P/cp4tk_rt/kit | head -40
echo "== gcs"; CLOUDSDK_CONFIG=$P/gcloud timeout 60 gsutil ls -l 'gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar.part*' 2>&1 | head; CLOUDSDK_CONFIG=$P/gcloud timeout 60 gsutil ls -a 'gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar.part00-of-04' 2>&1 | head -3
echo "== sam/g3t candidates"
for d in $P/cp4tk_rt $P/orch_qwen_stage $P/open_model_port $P/q7e/stage $P/distill $P/cache $P/okh7/b7e31d84a90c62f5 $P/okh7/k1tmp; do timeout 40 nice -n 19 find $d -maxdepth 4 \( -name 'sam3*.pt' -o -name 'model.safetensors' -o -iname '*g3t*' -o -iname '*vggt*' \) -printf '%s %p\n' 2>/dev/null | head -10; done
echo "== done $(date -u +%T)"
