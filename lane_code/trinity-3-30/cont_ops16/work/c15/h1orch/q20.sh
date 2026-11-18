export TZ=UTC; date -u +%TZ
tail -n 3 /project/community/jjyeung/okh7/x_4b3114cf/o/170527.steps | cut -c1-200
sstat -j 170527.batch -n -o AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite 2>&1
squeue -j 170527 -h -o '%T %M'
