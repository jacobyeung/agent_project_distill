W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ; wc -c $W/work/arm_0216Z.log < /dev/null
tail -1 $W/work/arm_0216Z.log < /dev/null | /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import json,sys
v=json.loads(sys.stdin.read())
def sh(x,d=0):
    if isinstance(x,dict): return {k:sh(v,d+1) for k,v in x.items()} if d<3 else '{..}'
    if isinstance(x,list): return x if len(json.dumps(x))<400 else '[%d]'%len(x)
    return x
print(json.dumps(sh(v),indent=1))"
head -c 3000 $W/work/arm_0216Z.log < /dev/null
