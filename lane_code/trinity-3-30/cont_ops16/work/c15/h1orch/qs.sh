sinfo -h -o "%P %a %l %D %c %m %G %t" | sort -u | head -20; sacctmgr -n show assoc user=jjyeung format=account,partition,qos 2>/dev/null | head
