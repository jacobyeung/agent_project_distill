O=/project/community/jjyeung/okh7; date -u +%TZ; pgrep -f t_og8a.sh >/dev/null && echo RUNNING || echo DONE; grep -v ": OK$" $O/t_og8a.log | tail -n 15 | cut -c1-300
