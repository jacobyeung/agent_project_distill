export TZ=UTC; L=/project/community/jjyeung/okh7/x_22c714e1/o/174113_live; date -u +%TZ
tail -c 700 $L/t_q.log; echo; tail -3 $L/t_q.steps | cut -c1-200; cat $L/mem.txt | grep -E '^(anon|file) ' | head -2
