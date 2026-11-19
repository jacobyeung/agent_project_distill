R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal; 
awk '/Traceback/{c++} c==1' $R/train_fresh.log | grep -v "^\s*\^" | head -45 | cut -c1-260
head -c 600 $R/fresh_rank0.json; echo; grep -n -i "fixture\|tiny\|model" $R/../REHEARSAL_PATHS.md | head -10 | cut -c1-250
