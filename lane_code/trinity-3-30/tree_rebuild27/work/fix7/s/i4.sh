W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
for f in $W/w28fix/src/bfix.py $W/w28fix/src/mg.py $W/w28fix/src/r.sh $W/w28fix/src/sum.py $W/w28fix/work/SHA256SUMS.diff $W/w28fix/work/cpu6_sim6.out; do echo "==== $f"; head -c 4500 $f; echo; done
echo "==== t.py head"; head -60 $W/w28fix/src/t.py
ls $W/w28fix/packet $W/w28fix/vt | head -30
grep -n "def reseal\|def cap\b\|def cap(" -A14 $W/w24z11b/out/arm_routing.py | head -50
ls $W/w27fix/packet | head; ls $W/w27fix/src | head
