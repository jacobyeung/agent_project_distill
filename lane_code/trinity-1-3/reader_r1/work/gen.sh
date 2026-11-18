export TZ=UTC; date -u +%FT%TZ; sinfo -p general -N -o '%N %t %G %C'; squeue -p general -h -o '%i %u %j %T %M %l %b %R' | head; scontrol show job 172456 | grep -E 'StartTime|Reason|TRES'
