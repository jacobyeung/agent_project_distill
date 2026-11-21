W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; D=$W/work/d173912/173912; P=/scratch/jjyeung/envs/p1cpu/bin/python; K=$W/w24z12/out/kit_n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
ls -la $D < /dev/null | head -40
sha256sum $D/routing_selection.json $D/receipt.json $D/db_bytes.json < /dev/null
ls -la $W/work/d173881/173881 < /dev/null | head -60
sha256sum $W/work/d173881/173881/routing_selection.json $W/work/d173881/173881/receipt.json < /dev/null 2>&1
nice -n 10 $P -I -s -B - <<'PY'
import json,hashlib
D='/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912'
s=json.load(open(D+'/routing_selection.json')); r=json.load(open(D+'/receipt.json')); b=json.load(open(D+'/db_bytes.json'))
print('selection keys',sorted(s))
print('rows',s.get('rows'),'regenerated_sha256',s.get('regenerated_sha256'),'regenerated_receipt',s.get('regenerated_receipt'),'logical_output',s.get('logical_output'))
print('inputs_pinned keys',sorted(s['inputs_pinned']))
for k in ('routing_database','routing_base'): print(' ',k,json.dumps(s['inputs_pinned'].get(k))[:300])
dig=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
print('receipt compact digest',dig,'schema',r.get('schema'),'stream',r.get('stream'),'count',r.get('count'),'database',json.dumps(r.get('database'))[:200])
print('db_bytes files',[(f.get('sha256'),f.get('size')) for f in b.get('files',[])][:6])
PY
echo "== writers in kit b/ and tree"
grep -n -l 'reader_filters\|population.json\|first_batch\|f1.json\|WAITING_REVIEW\|c0.json\|census' $K/b/*.py $K/b/*.sh < /dev/null 2>/dev/null
grep -n 'reader_filters\|population.json\|first_batch_check\|f1.json\|WAITING_REVIEW\|"c%d\|c{\|s2.json\|h0.json' $K/b/*.py < /dev/null 2>/dev/null | cut -c1-260 | head -60
ls $W/w24/work/build24k/rehearsal_k6 < /dev/null 2>&1 | head -30
