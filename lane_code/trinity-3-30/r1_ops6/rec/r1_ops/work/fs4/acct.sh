export TZ=UTC
sacctmgr -n -P show assoc user=$USER format=account,partition,qos,maxjobs 2>&1 | head -20
echo ==; sacctmgr -n -P show qos format=name,maxjobsperuser,maxtrespu,maxsubmitpu 2>&1 | head -30
echo ==; sinfo -h -o '%P %a %l %D %C' | head -20
echo ==; squeue -u $USER -h -o '%i|%j|%P|%T|%M|%l|%R' | grep -v jjy_
echo ==; ls -la /tmp/jjyeung 2>&1 | head -3
