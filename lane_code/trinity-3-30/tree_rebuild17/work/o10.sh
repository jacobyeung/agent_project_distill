export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
cat $X/o/173555/q.steps | tail -5 | cut -c1-200; tail -c 600 $X/o/173555/q.log | cut -c1-300
if grep -q '"s1-staging-result-v1", "status": "PASS"' $X/j/a15_cot_ap24d9b8e2_173555.log && [ "$(squeue -h -j 173556 -o %T)" = PENDING ]; then scancel 173556 && echo "cancelled 173556"; fi
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
