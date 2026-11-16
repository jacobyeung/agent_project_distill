O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
wc -l $O/t_6c30c594.log; grep -v ': OK$' $O/t_6c30c594.log | head -60 | cut -c1-400
grep -c ': OK$' $O/t_6c30c594.log
ls -la $B | head -50; ls -la $B/p $B/p/b 2>&1 | head -40
stat -c '%a %n' $B/p/b/r.sh
ls -la /project/community/jjyeung/okh7/x_07ca49df/b/r.sh
