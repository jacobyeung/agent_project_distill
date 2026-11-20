K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/out/kit_n_go
cd $K && tar cf - --exclude='k/t_*.tar' --exclude='k/l.json' --exclude='k/7.json' . | gzip -c | base64 -w0
