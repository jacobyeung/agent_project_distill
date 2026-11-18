M=/scratch/jjyeung/n30_mirror
for d in pooled_rule count_diag rows_r1; do echo "== $d"; ls -la $M/$d | head -20; done
for t in $M/pooled_rule/*.tar $M/pooled_rule/*.tgz; do [ -f "$t" ] && { echo "-- $t"; tar tf $t | grep -E "budget_2048/request.json|A544|ACCEPTED|arkit_3dod|adff67f7ae9" | head; }; done
