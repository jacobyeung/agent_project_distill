TZ=UTC scontrol show job 174261 | grep -E 'TRES|NumNodes|SubmitTime|Account|QOS' | head -6
sinfo -p general -o '%n %G %T %C' | head
TZ=UTC squeue -p general -o '%.10i %.10u %.20j %.8T %b %R' | head
sacctmgr -n show assoc user=jjyeung format=account,partition,qos,grptres,maxjobs,maxtres 2>/dev/null | head
