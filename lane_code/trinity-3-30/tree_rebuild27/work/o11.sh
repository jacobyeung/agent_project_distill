export TZ=UTC; O=/project/community/jjyeung/okh7/x_22c714e1/o/174113
grep -n "Traceback\|Error\|cuda\|CUDA" $O/q.log | cut -c1-300 | head -20; tar tvf $O/o.tar | head -20
cat $O/a6.json | head -c 900; echo; cat $O/r1.json | head -c 600
