W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go
date -u +%TZ
grep -n "weights\|device" $K/b/pl.py < /dev/null | cut -c1-260 | head
ls -la $W/w24z16b/out < /dev/null | tail -8; ls $W/w24z16b/work < /dev/null
