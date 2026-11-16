O=/project/community/jjyeung/okh7
date -u +%TZ; pgrep -f t_fd24a874.sh >/dev/null && echo RUNNING || echo EXITED
grep -c ': OK$' $O/t_fd24a874.log; grep -v ': OK$' $O/t_fd24a874.log | tail -n 25 | cut -c1-300
ls $O/i_1be16f28 2>&1 | tr '\n' ' '
