export TZ=UTC
date -u +%FT%TZ
sinfo -o '%P %G %c %m %N %a %l' 2>&1 | head -12
echo "--- assoc"; sacctmgr -nP show assoc user=$USER format=account,partition,qos,maxjobs,grptres 2>&1 | head -10
echo "--- qos"; sacctmgr -nP show qos format=name,maxjobsperuser,maxtrespu,maxwall,preempt,priority 2>&1 | head -12
echo "--- squeue 170209"; squeue -j 170209 -o '%.10i %.9P %.30j %.2t %.10M %.10l %.20S %.20e %R' 2>&1
