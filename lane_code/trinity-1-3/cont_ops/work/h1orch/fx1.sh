export TZ=UTC; date -u +%TZ
O=/project/community/jjyeung/okh7
chmod 700 -- $O/r && stat -c '%a %n' $O $O/r $O/x_4b3114cf $O/i_1be16f28
test -e $O/r/766136c1 && echo RS_EXISTS || echo RS_absent
