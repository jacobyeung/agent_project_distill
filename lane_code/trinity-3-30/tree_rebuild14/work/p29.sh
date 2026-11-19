R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal; date -u +%TZ; ls $R | tr '\n' ' '; echo
wc -c $R/train_fresh.log; grep -v "^\s*$" $R/train_fresh.log | grep -E -i "error|refus|Traceback|raise|exception|failed" | sort | uniq -c | sort -rn | head -15 | cut -c1-300
tail -40 $R/train_fresh.log | cut -c1-300
