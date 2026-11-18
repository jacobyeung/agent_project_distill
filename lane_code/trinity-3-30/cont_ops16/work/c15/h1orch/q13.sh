O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
date -u +%TZ; pgrep -f 'i_1be16f28/z.sh' >/dev/null && echo Z_RUNNING || echo Z_DONE
grep -v ': OK$' $O/t_c94bbc4e.z.log | tail -n 12 | cut -c1-300
ls $B | grep -E 'ready|result|compare|anon' | tr '\n' ' '; echo; stat -c '%a %n' $O/x_4b3114cf 2>&1
test -f $B/compare.json && cat $B/compare.json
