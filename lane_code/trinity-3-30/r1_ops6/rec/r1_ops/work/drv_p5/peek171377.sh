export TZ=UTC
sstat -a -j 171377 -P -o JobID,AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite 2>&1 | head
date -u +%T
sleep 30
sstat -a -j 171377 -P -o JobID,AveCPU,MaxDiskRead,MaxDiskWrite 2>&1 | head
tail -2 /project/community/jjyeung/okh7/x_69d2930d/o/171377.steps
