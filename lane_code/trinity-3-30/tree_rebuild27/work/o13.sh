export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
squeue -j 174132,174133 -h -o "%i %T %M"; ls -la --time-style=+%H:%M:%S $X/o/174133 2>&1 | tail -n +2 | awk '{print $6,$5,$7}' | tr '\n' ' '; echo
cat $X/o/174133/HOLD.txt 2>/dev/null | head -12 | cut -c1-200; tail -3 $X/o/174133/j2.log 2>/dev/null | cut -c1-200; cat $X/o/174133/tb.txt 2>/dev/null | head -3
tail -4 $X/t_fa5d00a8e996/r.txt 2>/dev/null | cut -c1-300
