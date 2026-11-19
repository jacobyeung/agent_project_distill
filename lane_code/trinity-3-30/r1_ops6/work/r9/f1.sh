export TZ=UTC
date -u +%FT%TZ
df -PB1G /project/community/jjyeung | tail -1
scontrol show partition preempt | tr ' ' '\n' | grep -E 'AllowAccounts|AllowQos|MaxTime|DefMem|MaxMem|PreemptMode|QoS|TRES|OverSubscribe|Default' 
squeue -h -p preempt -t PD | wc -l; squeue -h -p preempt -t R | wc -l
squeue -h -p preempt -t PD -o '%Q %r %b' | sort -rn | head -5
sacctmgr -n show assoc user=$USER format=account,partition,qos 2>/dev/null | head
ls -la /project/community/jjyeung/okh7/r/6ed2c7aa/ 2>&1 | head; ls /project/community/jjyeung/okh7/x_ee227714/o/ | grep -i 'slot\|172660' | head
python3 - <<'P'
import json;c=json.load(open('/project/community/jjyeung/okh7/x_69d2930d/k/0.json'));print(list(c)); print(json.dumps(c.get('extra',[]))[:800])
P
tail -c 600 /project/community/jjyeung/okh7/x_ee227714/o/172660.w.steps 2>/dev/null
