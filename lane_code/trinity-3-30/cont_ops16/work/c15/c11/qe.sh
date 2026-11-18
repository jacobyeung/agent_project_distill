export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb
date -u +%TZ; squeue -u jjyeung -h -o "%i %j %P %T %M %r" | grep -v -E '^1678|^16827|^167739'
sacct -j 170710 -X -n -o State,End,ExitCode 2>&1 | head -1
tail -n 2 $K/o/170710.w.steps | cut -c1-200; ls -la --time-style=+%T /project/community/jjyeung/okh7/r/39504485 | grep -E 'A\.|B\.' 
ls -la --time-style=+%T /project/community/jjyeung/okh7/ae71c903/a24ea1a1936/ 2>&1 | tail -n +4
cat /project/community/jjyeung/bf94a7976a7e9/a/pull.log; ls -la /project/community/jjyeung/bf94a7976a7e9/a/e | tail -n +4
sstat -j 170808.batch -n -o AveCPU,MaxDiskRead 2>&1 | head -1
