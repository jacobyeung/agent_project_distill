export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
grep -n -i 'plan\|dp\.py\|budget\|free' $X/o/174444/j2.log 2>/dev/null | tail -8 | cut -c1-400
tail -4 $X/o/174444/j2.log | cut -c1-300
