export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
for J in 173512 173513; do test -f $X/j/a15_cot_ap24d9b8e2_$J.log && { echo "== $J"; grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -5 | cut -c1-250; }; done
