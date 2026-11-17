export TZ=UTC
squeue -j 170786 -h -o "%i %T %M %R start=%S" 2>&1; sacct -j 170786 -X -n -o State,Start,ExitCode 2>&1
P=/project/community/jjyeung/okh7/ae71c903/af35386aa3e; ls -la --time-style=+%H:%M:%S $P 2>&1 | tail -n +2 | head; test -s $P/JOB.log && tail -n 3 $P/JOB.log | cut -c1-250
sstat -j 170786.batch -n -o AveCPU,MaxRSS,MaxDiskRead 2>&1 | head -2
