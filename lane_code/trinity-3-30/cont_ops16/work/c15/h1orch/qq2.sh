O=/project/community/jjyeung/okh7; W=$O/i_1be16f28/q_c492e8d1
date -u +%TZ; pgrep -f t_3d5e7d75.sh >/dev/null && echo RUNNING || echo DONE
tail -n 15 $O/t_3d5e7d75.log | cut -c1-300
ls -la $W 2>&1 | head; ls $W/o 2>/dev/null; test -f $W/o/q.json && head -c 3000 $W/o/q.json
