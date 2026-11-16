export TZ=UTC; date -u +%FT%TZ
echo "-- my jobs"; squeue -u jjyeung -h -o '%i %j %P %T %q' | head -30; squeue -u jjyeung -h | wc -l
echo "-- qos"; sacctmgr -n -P show qos format=Name,MaxSubmitPU,MaxJobsPU,MaxWall 2>&1 | head -20
echo "-- assoc"; sacctmgr -n -P show assoc user=jjyeung format=Account,Partition,QOS,MaxSubmit,MaxJobs 2>&1 | head -10
scontrol show partition general 2>&1 | grep -i "qos\|MaxTime"
