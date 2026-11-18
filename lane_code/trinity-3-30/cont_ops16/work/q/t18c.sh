M=/scratch/jjyeung/n30_mirror
tar tvf $M/pooled_rule/pooled_rule_lane_20261118.tar | grep -E "request.json|e193|SPEC.json|PLAN.json|ACCEPTED|arkit|ITEMS" | head -30
tar tf $M/count_diag/work_mirror_20261118T1107Z.tar | head -40
ls -R $M/count_diag/out | head -30
