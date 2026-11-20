export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
for J in 173567 173568; do test -f $X/j/a15_cot_ap24d9b8e2_$J.log && { echo "== $J"; grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -6 | cut -c1-300; }; done
if grep -q '"s1-staging-result-v1", "status": "PASS"' $X/j/a15_cot_ap24d9b8e2_173567.log 2>/dev/null && [ "$(squeue -h -j 173568 -o %T)" = PENDING ]; then scancel 173568 && echo "cancelled 173568"; fi
ls -la $X/o/173567/ 2>/dev/null | head -30
test -f $X/o/173567/q.steps && tail -4 $X/o/173567/q.steps | cut -c1-250
echo "== jd2.sh"; head -30 $X/jd2.sh | cut -c1-300; ls $X/n | head; ls $X/n_r $X/n_s 2>&1 | head
