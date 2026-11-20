export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
grep -v "archive members verified" $X/j/a15_cot_ap24d9b8e2_173555.log | tail -8 | cut -c1-250; ls $X/o/173555/ 2>&1 | head; ls -la $X/o/173555/live 2>/dev/null | head
