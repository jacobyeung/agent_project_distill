F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out/admit_test.py
sed -n 125,180p $F
grep -n "segment(" $F | head -3; n=$(grep -n "def segment" $F | cut -d: -f1); sed -n "${n},$((n+25))p" $F
grep -n "offline_pins\|map" /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out/ADMIT_TEST_USAGE.md | head
