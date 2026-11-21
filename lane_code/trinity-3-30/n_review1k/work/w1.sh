export TZ=UTC; date -u +%TZ
X=/project/community/jjyeung/okh7/x_22c714e1
ls $X/u | grep '^a49f117f' < /dev/null
timeout 200 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
/usr/bin/python3 -B -I - <<'PY'
import sys, json, hashlib, os, glob
sys.path.insert(0, '/tmp/a15_f16_174198/w1/w/top/p/s' if os.path.isdir('/tmp/a15_f16_174198/w1/w/top/p/s/student_pilot') else '/tmp/q_22c714e1_174198/p/s'); print('tree', sys.path[0])
from student_pilot.p3_provenance import digest
X='/project/community/jjyeung/okh7/x_22c714e1'
P='/tmp/a15_f16_174198/w1/w/top/p/q'
NJ=b'/tmp/jjyeung/q_22c714e1'; NS=b'/tmp/q_22c714e1/'
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
u=[p for p in glob.glob(X+'/u/a49f117f*')]
print('reviewed selection files', u)
exp=None
for p in u:
    try: v=json.load(open(p)); exp=v.get('regenerated_sha256'); print('reviewed', p[-70:], 'file sha', sh(p)[:12], 'regenerated_sha256', exp)
    except Exception as e: print('reviewed read', p, e)
r=P+'/selection/receipt.json'
print('selection dir', sorted(os.listdir(P+'/selection')) if os.path.isdir(P+'/selection') else 'ABSENT')
if os.path.exists(r):
    raw=open(r,'rb').read(); v=json.loads(raw)
    print('walk receipt sha', sh(r)[:12], 'tree digest', digest(v), 'equal reviewed', digest(v)==exp, 'NJ', raw.count(NJ), 'NS/', raw.count(NS))
    print('database', v['database']['path'], v['database']['sha256'], 'file sha', sh(v['database']['path']) if os.path.exists(v['database']['path']) else 'path not visible outside sandbox')
    d=P+'/selection/rows.sqlite'
    if os.path.exists(d): print('rows.sqlite at walk P', sh(d))
    print('materialization', v['materialization']['sha256'], 'source', v['source']['sha256'], 'count', v['count'], 'scenes', len(v.get('scenes') or []) if isinstance(v.get('scenes'), list) else v.get('scenes') if not isinstance(v.get('scenes'), dict) else len(v['scenes']))
    ex=v.get('source_scene_exclusions',{}).get('expected',{})
    print('pool reference shas', sorted({e.get('reference',{}).get('sha256','')[:8] for k,e in ex.items() if isinstance(e,dict) and 'reference' in e}))
for name in ('host.json','RESULT.json'):
    for p in glob.glob('/tmp/a15_f16_174198/w1/w/top/**/'+name, recursive=True)[:3]:
        try:
            v=json.load(open(p)); print(name, p, {k:v.get(k) for k in ('status','refusal','steps','regenerated_sha256')})
        except Exception as e: print(name, p, e)
PY
EOS
date -u +%TZ
