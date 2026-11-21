K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go
date -u +%TZ
cat -n $K/b/a.py < /dev/null | sed -n 20,110p | cut -c1-260
