W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24c/work/tree_r1
cat $W/work/hash24h1/DIFFS/tree__student_pilot__r1_handover.py.md | head -120
echo "@@@ callers"; grep -rn --include=*.py -E "r1_launch22|validate_removals|_same_pin_bytes|bind_handover|def donor|compare_configs" $T/student_pilot $T/launch_r1 | grep -v '/tests/' | cut -c1-220 | head -40
echo "@@@ pp imports"; sed -n '1,30p' $T/launch_r1/production_proof.py | grep -n import
