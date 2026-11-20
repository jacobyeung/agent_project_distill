export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_173567.log | tail -5 | cut -c1-400
ls -la $X/o/173567/ $X/o/173567/live 2>/dev/null | grep -v "^total\| \.$\| \.\.$"; tail -4 $X/o/173567/q.steps | cut -c1-250; tail -c 1200 $X/o/173567/q.log; for f in r.log dr.log; do test -f $X/o/173567/live/$f && tail -c 1500 $X/o/173567/live/$f; done
