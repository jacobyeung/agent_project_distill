export TZ=UTC
scontrol hold 171356; echo hold rc=$?
squeue -h -j 171356 -o "%i|%T|%R"
stat -c "%a %n" /project/community/jjyeung/okh7/x_69d2930d/b; ls -A /project/community/jjyeung/okh7/x_69d2930d/b | grep -c pycache
