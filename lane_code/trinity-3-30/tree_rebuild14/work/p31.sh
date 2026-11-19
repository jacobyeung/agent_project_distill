W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
grep -n "^diff\|^+++ " $W/w24/out/TREE.diff </dev/null | grep -i carrier_c1 | head; grep -c "^+++ " $W/w24/out/TREE.diff </dev/null
sed -n 550,566p $W/w24/work/tree_r1/student_pilot/carrier_c1.py </dev/null | cut -c1-200
grep -n -E "def wrap_model" -A16 $W/w24/work/tree_r1/student_pilot/carrier_c1_run.py </dev/null | cut -c1-200
grep -rn "tie_word_embeddings" $W/w24/work/build24f/rehearsal/p2 2>/dev/null </dev/null | head -3 | cut -c1-200
grep -n -i -E "model|tie|fixture" $W/w24/work/build24f/REHEARSAL_OVERRIDES.json </dev/null | head -10 | cut -c1-200
