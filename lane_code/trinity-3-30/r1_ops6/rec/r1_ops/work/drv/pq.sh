export TZ=UTC; date -u
sinfo -p preempt -o '%P %a %l %D %c %m %d %G %N' 2>&1 | head
sinfo -p general,advanced -o '%P %d %N' | head
squeue -p preempt -o '%i %u %j %T %M %R' | head
scontrol show partition preempt 2>&1 | grep -i -E 'QOS|MaxTime|PreemptMode|Nodes=|DefMem|MaxMem' 
sacctmgr -n show qos format=name,maxsubmitjobsperuser,maxjobsperuser,preempt 2>/dev/null | head
