W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1; K=$W/w24/out/kit_n_go
echo "=== entry.py 150-260"; sed -n 150,260p $T/launch_r1/entry.py
echo "=== s1_routing 196-240"; sed -n 196,240p $T/student_pilot/s1_routing.py
echo "=== s1_routing 440-500"; sed -n 440,500p $T/student_pilot/s1_routing.py
echo "=== production_proof def/_run"; grep -n "def \|check_host\|stage_host\|twins\|augment" $T/launch_r1/production_proof.py | head -50
echo "=== x.py"; cat $K/b/x.py; echo "=== rd.py"; cat $K/b/rd.py
echo "=== pl.py regeneration"; grep -n "regenerat\|/tmp/q_22c714e1\|'p'\|logical" $K/b/pl.py | head -20
