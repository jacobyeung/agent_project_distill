K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go
ls -la $K $K/k | head -60
cd $K && tar cf - --exclude='k/t_*.tar' . | gzip -c | base64 -w0 > /scratch/jjyeung/orch_n30/n_review/r1b/kng24m1.b64; wc -c /scratch/jjyeung/orch_n30/n_review/r1b/kng24m1.b64
