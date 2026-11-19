cd /scratch/jjyeung; /scratch/jjyeung/envs/p1cpu/bin/python - > /tmp/fbp2_c2.list <<'P'
import json,os
c=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json'))
out=set()
def w(x):
    if isinstance(x,dict): [w(v) for v in x.values()]
    elif isinstance(x,list): [w(v) for v in x]
    elif isinstance(x,str) and x.startswith('/scratch/jjyeung/') and os.path.isfile(x) and os.path.getsize(x)<60e6: out.add(x[len('/scratch/jjyeung/'):])
w(c)
for p in sorted(out): print(p)
P
wc -l < /tmp/fbp2_c2.list; du -ch $(cat /tmp/fbp2_c2.list) | tail -1
tar cf - -T /tmp/fbp2_c2.list | timeout 300 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib "cd /scratch/jjyeung/orch_n30/fb_pack/ro && tar xf - --skip-old-files && echo EXTRACTED" 2>&1 | tail -3
