W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go
date -u +%TZ
echo "== pc.py 190-370"; sed -n 190,370p $K/b/pc.py < /dev/null | cut -c1-250
echo "== cs.py 60-125"; sed -n 60,125p $K/b/cs.py < /dev/null | cut -c1-250
echo "== sv.py 55-100"; sed -n 55,100p $K/b/sv.py < /dev/null | cut -c1-250
echo "== x.py"; cat $K/b/x.py < /dev/null | cut -c1-250
