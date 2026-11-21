export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
touch $X/o/174133/RELEASE; echo "RELEASE touched $(date -u +%TZ)"; sleep 45
sacct -j 174133 -n -X -o State,ExitCode,Elapsed,End | head -1; cat $X/o/174133/HOLD_END.txt 2>/dev/null | head -4
squeue -j 174132 -h -o "%i %T %M"; grep -n "AS_EXPECTED\|PASS\|FAIL" $X/t_fa5d00a8e996/r.txt | tail -4 | cut -c1-300
