export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
ls -la $X/o/173964 $X/o/173964_x $X/o/173964_y 2>&1 | head -40; echo ---j2.log; tail -c 6000 $X/o/173964/j2.log; echo; echo ---j2.err; tail -c 3000 $X/o/173964/j2.err; echo; echo ---y; cat $X/o/173964_y/ls.txt 2>/dev/null | head -30
