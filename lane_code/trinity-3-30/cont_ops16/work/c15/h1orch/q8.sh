O=/project/community/jjyeung/okh7
date -u +%TZ; pgrep -f t_c94bbc4e.sh >/dev/null && echo RUNNING || echo EXITED
grep -c ': OK$' $O/t_c94bbc4e.log; grep -v ': OK$' $O/t_c94bbc4e.log | tail -n 25 | cut -c1-300
ls $O/i_1be16f28 2>&1 | tr '\n' ' '
ls $O/i_1be16f28/*.json 2>/dev/null | tr "\n" " "
