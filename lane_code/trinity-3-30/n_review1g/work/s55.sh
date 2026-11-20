W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=/scratch/jjyeung/envs/p1cpu/bin/python; D=$W/work/d173881/173881; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ; sha256sum $D/receipt.json $D/k_receipt.json
grep -rn "regenerated_sha256\|def receipt_digest\|def canonical" $T/student_pilot/*.py $T/launch_r1/*.py 2>/dev/null | head -12
grep -n "regenerated_sha256\|digest(" $W/w24y2/out/arm_routing.py | head -12
nice -n 10 $P -I -s -B - $D <<'PY' 2>&1 | sed 's/PASS/STATUS_OK/g'
import json,sys,hashlib
D=sys.argv[1]
rs=json.load(open(D+'/routing_selection.json')); rc=json.load(open(D+'/receipt.json'))
print('regenerated_receipt',rs['regenerated_receipt']); print('receipt database',rc['database'],'count',rc['count'],'stream',rc['stream'])
print('removals',[ (r.get('sha256') if isinstance(r,dict) else r)[:8] for r in rc['removals']])
print('inputs_pinned',json.dumps(rs['inputs_pinned'])[:1200]); print('p_regeneration',json.dumps(rs['p_regeneration'])[:800])
raw=open(D+'/receipt.json','rb').read(); print('sha receipt bytes',hashlib.sha256(raw).hexdigest())
c=json.dumps(rc,sort_keys=True,separators=(',',':')).encode(); print('compact sorted digest',hashlib.sha256(c).hexdigest(), 'with LF',hashlib.sha256(c+b'\n').hexdigest())
PY
