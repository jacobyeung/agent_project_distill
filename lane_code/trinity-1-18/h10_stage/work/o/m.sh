export TZ=UTC
date -u +%FT%TZ
squeue -j 170674 -h -o '%i %T %M %l %N %r' 2>&1
sstat -a -j 170674 --noheader --format=JobID%20,AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite,AveCPUFreq 2>&1 | head -4
P=/project/community/jjyeung/okh7/ae71c903; ls -la $P/b01ec87a6f29b00029ab2 2>&1 | head
sacct -j 170674 -n -o JobID%20,State,Elapsed,ExitCode 2>&1 | head -4
