export TZ=UTC; date -u +%TZ
sacct -j 170525 -X -n -o JobID,State,ExitCode,Start,End,Elapsed,NodeList 2>&1
K=/project/community/jjyeung/okh7/x_4b3114cf
ls -la --time-style=+%H:%M:%S $K/o
cat $K/o/170525.err
stat -c '%a %U %n' /project/community/jjyeung/okh7 /project/community/jjyeung/okh7/r /project/community/jjyeung/okh7/r/* 2>&1 | head -20
