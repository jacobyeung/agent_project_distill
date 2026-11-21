set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w29f7; mkdir -p $W/t; cd $W
TAR=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix/n_go/k/t_e047002134f979bd.tar
sha256sum $TAR
[ -f $W/t/student_pilot/carrier_c1_run.py ] || tar xf $TAR -C $W/t
ls $W/t | head -3; sha256sum $W/t/student_pilot/carrier_c1_run.py $W/t/student_pilot/c1_pose_mix.py $W/t/student_pilot/carrier_c1_data.py
cat > $W/a1.py <<'PY'
import sys, json, sqlite3, hashlib, collections, os
W, ROWS, A3, D0, REM = sys.argv[1:6]
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
print('rows sha', sha(ROWS)); print('a3v2 sha', sha(A3)); print('0d28 sha', sha(D0)); print('removal601 sha', sha(REM), os.path.getsize(REM))
sys.path.insert(0, W+'/t')
from student_pilot.row_removals import row_keys
a3=json.load(open(A3)); d0=json.load(open(D0))
a3t,a3h=set(a3['train_scenes']),set(a3['heldout_scenes']); d0t,d0h=set(d0['train_scenes']),set(d0['heldout_scenes'])
print('a3v2 train/held',len(a3t),len(a3h),'0d28 train/held',len(d0t),len(d0h),'d0t<=a3t',d0t<=a3t,'d0h<=a3h',d0h<=a3h,'d0t&a3h',len(d0t&a3h))
rem=[json.loads(l) for l in open(REM) if l.strip()]; remk={r['row_key'] for r in rem}
print('removal601 rows',len(rem),'keys',len(remk),'fields',sorted({k for r in rem for k in r}),'reasons',collections.Counter(r.get('reason') for r in rem))
c=sqlite3.connect('file:'+ROWS+'?mode=ro',uri=True)
n,lo,hi=c.execute('SELECT count(*),min(i),max(i) FROM rows').fetchone(); print('db count',n,lo,hi)
cls=collections.Counter(); scenes=collections.defaultdict(set); out=[]; qids=set(); dup=0
for i,raw in c.execute('SELECT i,row FROM rows ORDER BY i'):
    r=json.loads(raw); s=r['dataset']+'/'+r['scene']
    if r['qid'] in qids: dup+=1
    qids.add(r['qid'])
    k=('A3TRAIN' if s in a3t else 'A3HELD' if s in a3h else 'NEITHER')
    k0=('D0TRAIN' if s in d0t else 'D0HELD' if s in d0h else 'D0OUT')
    cls[k]+=1; cls[k+'|'+k0]+=1; scenes[k].add(s); scenes['ALL'].add(s); scenes[k+'|'+k0].add(s)
    rk=row_keys(r); inrem=bool(rk & remk)
    cls[k0+'|inrem=%s'%inrem]+=1
    if k=='NEITHER' or k0!='D0TRAIN':
        out.append(dict(i=i,cls=k,cls0=k0,inrem=inrem,dataset=r['dataset'],scene=r['scene'],qid=r['qid'],
            row_keys=sorted(rk),question_type=r.get('question_type',r.get('category')),answer=r.get('answer'),
            target=r.get('target'),question=(r.get('student_input') or {}).get('question',r.get('question')),
            keys=sorted(r),prov=sorted((r.get('provenance') or {}).keys()) if isinstance(r.get('provenance'),dict) else None,
            source=r.get('source'),source_dataset=r.get('source_dataset')))
print('dup qids',dup)
for k,v in sorted(cls.items()): print('COUNT',k,v)
for k,v in sorted(scenes.items()): print('SCENES',k,len(v))
json.dump(out,open(W+'/out601.json','w'),indent=1)
nei=[o for o in out if o['cls']=='NEITHER']
print('NEITHER rows',len(nei),'inrem',sum(o['inrem'] for o in nei))
bys=collections.defaultdict(list)
for o in nei: bys[o['dataset']+'/'+o['scene']].append(o)
print('NEITHER scenes',len(bys))
for s,v in sorted(bys.items()):
    print('NS',s,len(v),dict(collections.Counter(o['question_type'] for o in v)),'qid_prefix',dict(collections.Counter(o['qid'].split('_')[0] for o in v)))
print('example', json.dumps(nei[0], default=str)[:1500])
o474=[o for o in out if o['cls']=='A3TRAIN']
print('A3-only rows',len(o474),'inrem',sum(o['inrem'] for o in o474),'datasets',collections.Counter(o['dataset'] for o in o474))
print('out keys cover removal601:', {k for o in out for k in o['row_keys']} & remk == remk, 'every out row in removal601', all(o['inrem'] for o in out))

PY
date -u +%TZ
R=$(ls /scratch/jjyeung/orch_n30/n_review/r1j/div/*601.jsonl)
nice -n 10 python3 -I -B $W/a1.py $W /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite /scratch/jjyeung/orch_n30/n_review/r1j/div/f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5 /scratch/jjyeung/orch_n30/n_review/r1j/div/0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad $R 2>&1
date -u +%TZ
