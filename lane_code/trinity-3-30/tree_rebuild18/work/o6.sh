X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173567; date -u +%TZ; squeue -u $USER -o "%.10i %.10P %.8T %.10M"
cat $O/q1.json; echo; cat $O/r1.json; echo; cat $O/db_bytes.json; echo; cat $O/dbb.log; echo
grep -v "^\s*$" $O/r.log | tail -8 | cut -c1-1500; echo; grep -n -i "refus\|error\|Traceback\|R1_\|E[0-9][0-9]\b" $O/r.log | tail -12 | cut -c1-600
tail -6 $X/j/a15_cot_ap24d9b8e2_173567.log | cut -c1-400; tail -20 $X/j/a15_cot_ap24d9b8e2_173567.err 2>/dev/null | cut -c1-400
