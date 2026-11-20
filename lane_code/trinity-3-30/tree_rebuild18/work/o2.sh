export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_173567.log | tail -4 | cut -c1-300
if grep -q '"s1-staging-result-v1", "status": "PASS"' $X/j/a15_cot_ap24d9b8e2_173567.log 2>/dev/null && [ "$(squeue -h -j 173568 -o %T)" = PENDING ]; then scancel 173568 && echo "cancelled 173568"; fi
ls $X/o/173567/; tail -3 $X/o/173567/q.steps | cut -c1-250
echo "== jd2 tail"; sed -n 31,200p $X/jd2.sh; echo "== j.sh"; cat $X/j.sh
