TZ=UTC sinfo -o '%P %a %l %D %t' | head -20; TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %N %R'; sacctmgr -n show assoc user=$USER format=account,partition,qos%40 2>/dev/null | head
