export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173076 -n -X -o JobID,State,NodeList 2>/dev/null | head -2
grep -n -E "init|93ccadab|m544|tar .* verified|small|extra" $X/j/173076.out 2>/dev/null | grep -v cgroup | head -15 | cut -c1-250
squeue -u $USER -h -o "%i %j %P %T %M %N" 2>/dev/null
