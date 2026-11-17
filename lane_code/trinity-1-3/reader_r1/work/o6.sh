scancel 170853; sleep 3
TZ=UTC squeue -u $USER -p general -o '%i %j %T %M %l %R'
sinfo -s
sacctmgr -n show assoc user=$USER format=account,partition,qos%40 2>/dev/null | head
sacctmgr -n show qos format=name%20,maxjobspu,maxtrespu%40 2>/dev/null | head -20
tail -3 /project/community/jjyeung/e09e45fda45db/a/cpu_check.log
