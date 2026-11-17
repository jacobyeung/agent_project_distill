export TZ=UTC
scontrol show partition general 2>&1 | grep -E "MaxTime|DefaultTime|MaxNodes|State|TotalNodes|QoS|AllowAcc" | head
sinfo -p general -o '%n %t %G %C' 2>&1 | head -20
squeue -p general -o '%i %j %u %T %M %l %b %Q' 2>&1 | head -20
squeue -u jjyeung -o '%i %j %P %T %M %l %b' 2>&1
sacctmgr -n show assoc user=jjyeung format=account,partition,qos,maxtres,maxwall 2>&1 | head
