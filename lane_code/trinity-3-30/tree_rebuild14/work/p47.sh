R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal2; date -u +%TZ
head -c 1500 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal_run2.log; echo; ls $R | tr '\n' ' '; echo
wc -c $R/train_fresh.log; grep -E "Error|error:|refus|Refus" $R/train_fresh.log | sort | uniq -c | sort -rn | head -8 | cut -c1-300
awk '/Traceback/{c++} c==1' $R/train_fresh.log | grep -v "^\s*\^" | grep -v site-packages | head -30 | cut -c1-250
