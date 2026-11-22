W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out
ls -la $W | head -20
cat $W/admit_test.sh | head -40
grep -n "stop_and_milestones" -A14 $W/admit_test.py | head -40
grep -n "tree_seal\|9d2bbb8a\|TREE" $W/admit_test.py | head -12
