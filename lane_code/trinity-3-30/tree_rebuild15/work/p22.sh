R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal5; date -u +%TZ
grep -n -E "Error|error|refus|Traceback|raise|R1_|E[0-9][0-9]" $R/train_budget.log | grep -v -E "FutureWarning|error_file|elastic/errors" | head -20 | cut -c1-500
cat $R/RUN_REFUSAL.json | head -c 1500; echo; head -c 800 $R/authorization_budget.json; echo; tail -5 $R/authorize_budget.log | cut -c1-300
