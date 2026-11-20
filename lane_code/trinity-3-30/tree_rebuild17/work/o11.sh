export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
grep -v "archive members verified\|joined\|staged$" $X/j/a15_cot_ap24d9b8e2_173555.log | tail -4 | cut -c1-300; ls -la $X/o/173555/ | tail -n +2; tail -c 800 $X/o/173555/q.log | cut -c1-300
