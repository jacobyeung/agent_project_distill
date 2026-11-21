TZ=UTC date +%TZ; nohup srun --overlap --jobid 174134 -N1 -n1 nice -n 15 /usr/bin/python3 -I - > /tmp/rv1j_b.out 2>&1 <<"PY" &
import sys,json,sqlite3,os,collections
N='/tmp/q_22c714e1_174134'; DBG='/tmp/a15_dbg_174134'
import glob
sys.path.insert(0,N+'/p/s'); sys.path.insert(1,N+'/s/np226'); sys.path.extend(glob.glob(N+'/s/c7d31ddd/venvs/rwtrain_torch211_cu129/lib/python3*/site-packages'))
import student_pilot.r1_persisted as rp
_orig=rp.relocated
def reloc(pin):
    try:
        p=str(_orig(pin))
        if os.path.isfile(p): return p
    except Exception: pass
    p=pin['path']; sha=pin['sha256']
    for c in (p.replace('/tmp/q_22c714e1/',N+'/',1), N+'/p/q/u/'+sha, N+'/u/'+sha, p):
        if os.path.isfile(c): return c
    return p
rp.relocated=reloc
from student_pilot.r2_scene_bindings import rows
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import pinned, load
from collections import Counter
Q=N+'/p/q'
c=json.load(open(Q+'/c.json'))
rule=Exclusions(c['dev_scene_exclusions'], c['benchmark_scene_exclusions'])
def lab(row):
    m=rule.matches(row); return (bool(m['dev']),bool(m['benchmark']))
# stream rows
stream={}
with sqlite3.connect('file:'+Q+'/selection/rows.sqlite?mode=ro',uri=True) as con:
    for i,t in con.execute('SELECT i,row FROM rows ORDER BY i'):
        r=json.loads(t); stream[r['qid']]=lab(r)
S_listed={q for q,v in stream.items() if any(v)}
print('stream rows',len(stream),'listed in stream (a,b)',sum(stream[q][0] for q in S_listed),sum(stream[q][1] for q in S_listed),flush=True)
# base (camera group)
sc0=json.load(open(Q+'/sc/0/0.json')); kept=set(load(pinned(sc0['indices']))); popn=sc0['scene_rebuild']['population_count']
base={}; Lb_idx=set(); n=0
for i,r in enumerate(rows(sc0['scene_rebuild']['population'])):
    n+=1; v=lab(r); base[r['qid']]=(v,r.get('question_type'))
    if any(v): Lb_idx.add(i)
cLb=set(range(popn))-kept
Lb={q for q,(v,t) in base.items() if any(v)}
Ab={q for q in base if q in stream}
print('base rows',n,popn,'myL==censusL(idx)',Lb_idx==cLb,len(Lb_idx),len(cLb),'| base qids in stream',len(Ab),flush=True)
print('base L&A',len(Lb&Ab),' L-A',len(Lb-Ab),' types of L-A',Counter(base[q][1] for q in Lb-Ab).most_common(6))
print('stream listed == base L&A:',S_listed==(Lb&Ab),' stream listed not from base',len(S_listed-set(base)))
# pool
man=json.load(open(Q+'/sc/p/0.json'))
def tsv(p): return {tuple(l.rstrip('\n').split('\t',1)) for l in open(p) if l.strip()}
cdev=tsv(Q+'/sc/p/dev_s1.tsv'); cben=tsv(Q+'/sc/p/eval_rooms.tsv')
a0m=json.load(open(Q+'/selection/materialization.json')) if os.path.exists(Q+'/selection/materialization.json') else {}
deferred=set(a0m.get('source_deferrals',{}))
mdev,mben=set(),set(); per=Counter(); poolkeys={}
for s in man['sets']:
    name=s['name']; kind='packed' if 'packed' in s['files'] else 'rows'
    pin={k:s['files'][kind][k] for k in ('path','sha256')}
    for r in rows(pin):
        a,b=lab(r); pr=(name,r['qid']); poolkeys.setdefault(r['qid'],set()).add(name)
        if a: mdev.add(pr); per[(name,'a')]+=1
        if b: mben.add(pr); per[(name,'b')]+=1
print('pool my dev==census dev',mdev==cdev,len(mdev),len(cdev),' my b==census b',mben==cben,len(mben),len(cben),flush=True)
print('deferred sources',sorted(deferred))
def cnt(names): return (sum(per[(n,'a')] for n in names), sum(per[(n,'b')] for n in names))
used=[s['name'] for s in man['sets'] if s['name'] not in deferred]
print('used',len(used),'listed in used (a,b)',cnt(used),' listed in deferred (a,b)',cnt(deferred))
up=json.load(open(Q+'/selection/receipt.json'))['source_scene_exclusions']['sources'] if os.path.exists(Q+'/selection/receipt.json') else {}
print('upstream receipt per source (a,b) vs mine:',{k:((v['dev_matches'],v['benchmark_matches']),cnt([k.split('/',1)[1]])) for k,v in up.items() if k.startswith('pool/')})
pl={q for (n,q) in mdev|mben}
sq=set(stream)
print('stream qids that are pool-listed',len(sq&pl),' stream qids found only in deferred sources',sum(1 for q in sq if q in poolkeys and poolkeys[q]<=deferred))
print('stream qids neither base nor pool',len(sq-set(base)-set(poolkeys)))
PY
sleep 60; cat /tmp/rv1j_b.out
