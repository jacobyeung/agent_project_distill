W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z12; K=$Z/out/kit_n_go
date -u +%TZ
echo "== l.py"; cat $K/b/l.py < /dev/null
echo "== v.py"; cat $K/b/v.py < /dev/null | head -80
echo "== resolve.py (wc, refusals)"; wc -l $K/b/resolve.py < /dev/null; grep -n 'raise\|exit\|print\|pool\|def ' $K/b/resolve.py < /dev/null | head -60
echo "== job.sh"; cat $K/job.sh < /dev/null | head -80
echo "== arm_routing.py 1-60"; sed -n 1,60p $W/w24z11b/out/arm_routing.py < /dev/null
echo "== arm_launch.py verdict part"; grep -n -i 'verdict\|PASS\|522a3be3\|a49f117f\|5e35c3ce\|regenerated' $W/w24z11b/out/arm_launch.py < /dev/null | head -60
