export TZ=UTC; date -u +%TZ
sed -n 41,75p /project/community/jjyeung/okh7/x_f5c353f7/o/170111.steps | cut -c1-160
echo ==NOW; tail -n 4 /project/community/jjyeung/okh7/x_4b3114cf/o/170527.steps | cut -c1-200
sstat -j 170527.batch -n -o AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite 2>&1
