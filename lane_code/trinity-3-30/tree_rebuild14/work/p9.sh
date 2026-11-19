W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; T=$W/w24/work/tree_r1; date -u +%TZ
sed -n 113,140p $T/launch_r2/persistence.py </dev/null
echo "== h.py"; cat $K/b/h.py </dev/null | head -40
grep -n -c r2_persistence $K/k/*.json </dev/null
ls $W/inputs/p_configs </dev/null; for f in $W/inputs/p_configs/*; do echo "-- $f"; grep -o '"r2_persistence"[^}]*}' $f </dev/null | head -2 | cut -c1-600; done
grep -rn "r2_persistence" $T/launch_r1 $T/student_pilot/r1_*.py </dev/null | head -10 | cut -c1-200
ls $W/w24/work/build24d/go </dev/null | tr '\n' ' '
