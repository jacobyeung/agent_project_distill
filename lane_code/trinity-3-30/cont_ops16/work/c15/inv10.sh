TZ=UTC sinfo -p general,advanced -o '%P %G %c %m %D %t %l' | head -20
TZ=UTC scontrol show job 170008 | grep -E 'TRES|Partition|StartTime|TimeLimit' | head
sacctmgr -nP show qos format=name,maxtresperuser,maxjobsperuser,maxsubmitjobsperuser 2>/dev/null | grep -iE 'general|advanced|normal' | head
