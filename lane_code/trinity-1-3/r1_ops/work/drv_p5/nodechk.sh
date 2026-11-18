export TZ=UTC
scontrol show node orchard-community-0 | grep -E 'CPUAlloc|CPUTot|RealMemory|AllocMem|Gres|AllocTRES|CfgTRES|State|Partitions'
scontrol show job 171337 | grep -E 'JobState|Reason|NumNodes|NumCPUs|TRES|ReqNodeList|ExcNodeList|Partition|QOS'
sacctmgr -n -P show qos format=Name,MaxTRESPU,MaxJobsPU,MaxSubmitPU 2>/dev/null | head -12
squeue -p advanced -h -o '%i|%u|%T|%b|%N|%R' | head -30
sinfo -p advanced -h -o '%n|%C|%G|%e|%T' | head -20
