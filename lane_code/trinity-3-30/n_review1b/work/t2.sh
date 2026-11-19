W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1; K=$W/w24/out/kit_n_go
for f in $W/w24/out/BUILD24M1_REPORT.md $W/w24/out/DELIVERY_24M1.json $K/b/rg.py $K/b/a.py $W/w24/out/jr.sh $W/w24/out/arm_routing.py; do echo "=== $f $(sha256sum < $f | cut -c1-16)"; cat $f; done
echo "=== entry.py routing grep"; grep -n "regenerated\|routing_selection\|selection" $T/launch_r1/entry.py | head -40
echo "=== production_proof grep"; grep -n "regenerated\|routing_selection\|def check_host_selection" $T/launch_r1/production_proof.py | head -30
echo "=== s1_routing def build"; grep -n "^def \|materializ" $T/student_pilot/s1_routing.py | head -60
