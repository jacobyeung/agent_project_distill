W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=/scratch/jjyeung/envs/p1cpu/bin/python; D=$W/work/d173881/173881
date -u +%TZ; for d in w24y2 w24z4; do echo "== $d"; sha256sum $W/$d/out/ARM_ROUTING_USAGE.md $W/$d/out/arm_routing.py 2>&1; done
cat $W/w24y2/out/ARM_ROUTING_USAGE.md | head -80
nice -n 10 $P -I -s -B - $D <<'PY' 2>&1 | sed 's/PASS/STATUS_OK/g'
import json,sys,collections
D=sys.argv[1]
pc=json.load(open(D+'/proc_check.json')); print('proc_check top',{k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in pc.items()})
st=collections.Counter((r['key'][0], r.get('n',{}).get('status'), r.get('p',{}).get('status'), r.get('status')) for r in pc['rows']); print('proc rows',dict(st))
print('proc sample keys',[r['key'] for r in pc['rows'][:3]], 'other keys', sorted(pc['rows'][0]))
rs=json.load(open(D+'/routing_selection.json')); print('routing_selection top',{k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in rs.items()})
rc=json.load(open(D+'/receipt.json')); print('receipt.json top',json.dumps({k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in rc.items()})[:1500])
PY
