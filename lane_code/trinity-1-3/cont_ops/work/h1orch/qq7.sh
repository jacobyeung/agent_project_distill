O=/project/community/jjyeung/okh7; W=$O/i_1be16f28/q_6c18a2bf
date -u +%TZ; pgrep -f t_d1faeea1.sh >/dev/null && echo RUNNING || echo DONE
tail -n 8 $O/t_d1faeea1.log | cut -c1-300; cat $W/b.log 2>/dev/null | tail -8; ls $W $W/o 2>&1; test -f $W/o/q.json && head -c 4000 $W/o/q.json
