export TZ=UTC; date -u +%TZ; sinfo -s 2>&1 | head -20; for p in $(sinfo -h -o %P | tr -d '*' | sort -u); do scontrol show partition $p 2>/dev/null | grep -oE "PartitionName=[^ ]+|MaxTime=[^ ]+|PreemptMode=[^ ]+|Priority[A-Za-z]*=[^ ]+|QoS=[^ ]+|MaxNodes=[^ ]+|DefMemPerCPU=[^ ]+|TRES=[^ ]+" | tr '\n' ' '; echo; done
sinfo -o '%P %G %D %t %c %m' 2>&1 | head -30
squeue -u $USER -o '%i %j %P %T %M %l %b' 2>&1 | head
sacctmgr -n show assoc user=$USER format=partition,qos,maxjobs,grptres 2>&1 | head
