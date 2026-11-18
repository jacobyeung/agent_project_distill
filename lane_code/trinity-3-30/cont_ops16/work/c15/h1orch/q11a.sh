export TZ=UTC
sacct -j 170757 -X -n -o JobID,JobName%24,State,Start,End,Elapsed,ExitCode 2>&1
P=/project/community/jjyeung/okh7/ae71c903/ae470417b41; ls -la --time-style=+%H:%M:%S $P 2>&1 | head -20
test -s $P/EXIT.json && head -c 1500 $P/EXIT.json; echo
squeue -u jjyeung -h -o "%i %j %P %T %M %R" 2>&1
