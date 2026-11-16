export TZ=UTC
stat -c '%a %U %n' /project/community/jjyeung/okh7 /project/community/jjyeung 2>&1
for d in x_4b3114cf i_1be16f28 r/766136c1; do test -e /project/community/jjyeung/okh7/$d && echo "EXISTS $d" || echo "absent $d"; done
squeue -u jjyeung -o '%i %j %P %T %M %l %R' 2>&1 | head -20
