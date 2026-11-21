export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; L=$X/o/174113_live; date -u +%TZ
ls -la --time-style=+%H:%M:%S $L | tail -n +2 | awk '{print $6, $5, $7}'
tail -c 1500 $L/t_q.steps 2>/dev/null | tr -d '\r' | tail -8 | cut -c1-240
grep -o 'R1_PROCESSOR[^"]*' $L/t_q.log | head -2; grep -c . $L/t_q.log
