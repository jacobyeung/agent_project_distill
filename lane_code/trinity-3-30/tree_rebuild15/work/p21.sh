B=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f; R=$B/rehearsal5; date -u +%TZ
grep -v "^\s*$" $B/rehearsal_run5.log | tail -25 | cut -c1-400
ls $R | tr '\n' ' '; echo
tail -25 $R/train_budget.log 2>/dev/null | grep -v -E "FutureWarning|set_state_dict_type|Loading weights|fast path" | tail -12 | cut -c1-600
ls $R/target/o/rehearsal/live 2>/dev/null | tr '\n' ' '
