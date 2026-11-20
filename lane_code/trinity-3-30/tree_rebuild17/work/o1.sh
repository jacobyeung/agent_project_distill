export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
for J in 173555; do test -f $X/j/a15_cot_ap24d9b8e2_$J.log && { echo "== $J"; grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -5 | cut -c1-250; }; done
squeue -w orchard-community-1 -o "%.10i %.10P %.10u %.8T %.10M %.6b" ; sinfo -p advanced,preempt -o "%P %n %T %G" | head -12
