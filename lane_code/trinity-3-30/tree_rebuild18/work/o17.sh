export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173626; O=$X/o/$J
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,End,ExitCode
grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -5 | cut -c1-300
ls -la $O $O/live 2>/dev/null | grep -v "^total\| \.$\| \.\.$" | cut -c30-; test -f $O/q1.json && cat $O/q1.json; test -f $O/r1.json && cut -c1-300 $O/r1.json; echo; test -f $O/rdiff.log && tail -5 $O/rdiff.log
test -f $O/r.log && grep -n "R1_\|Error\|refus" $O/r.log | tail -4 | cut -c1-300
