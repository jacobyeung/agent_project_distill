K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go
cd $K && tar cf - --exclude=k/l.json --exclude='k/t_*.tar' . | base64 -w0
