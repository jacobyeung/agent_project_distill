export TZ=UTC; P=/project/community/jjyeung/bf94a7976a7e9
squeue -u jjyeung -h -o "%i %j %P %T %M %R"; tail -n 4 $P/a/score.log | cut -c1-300; ls $P/a/s 2>/dev/null | tr '\n' ' '; echo
