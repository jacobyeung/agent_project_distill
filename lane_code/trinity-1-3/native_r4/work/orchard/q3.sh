export TZ=UTC
sinfo -p general -o '%P %a %l %D %G %f' | head
sacct -j 170056,170111 -X -o JobID,JobName%30,Partition,Account,ReqTRES%60,Timelimit,State
sacctmgr -n show assoc user=$USER format=Account,Partition,QOS%40 | head
scontrol show partition general | head -20
