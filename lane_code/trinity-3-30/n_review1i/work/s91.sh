W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go
date -u +%TZ
grep -n "weights\|'device'\|f\.json\|production_proof\|rv\.py\|review" $K/b/z.py $K/b/u.py $K/b/a.py $K/b/h.py < /dev/null | cut -c1-260 | head -30
sed -n 44,60p $W/w24z14/out/admit_test.py < /dev/null | cut -c1-250
