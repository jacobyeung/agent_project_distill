export TZ=UTC; date -u +%TZ; squeue -j 174112,174110 -h -o "%i %P %T %M %l %S %R"
sinfo -h -o "%P %a %D %t %G" | head -20
sacctmgr -n show qos format=Name%20,MaxJobsPU,MaxTRESPU%30 2>/dev/null | head -10
squeue -p advanced,preempt -h -o "%i %P %u %T %M %l %b %R" | head -12
