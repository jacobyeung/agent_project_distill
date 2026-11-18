"""Load the paired direct reads for the pooled harm rule (read-only inputs; writes PAIRS.npz + PAIRS_META.json here).
dev-S1 = family main (seven direct types, 150 items each); R0-dev = family a7 (seven direct types under --types direct)."""
import json, hashlib, glob, re, sys
import numpy as np
C='/scratch/jjyeung/orch_n30/cont_ops/work'
SRC=dict(
 S544=C+'/d0/readk/evidence/A544.jsonl',
 S_D0m200=C+'/d0/readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl',
 S_D0m100=C+'/h1read/kit/build/af35386aa3e/fetched/x/ITEMS.jsonl',
 S_H1m100=C+'/h1read/kit/build/a24ea1a1936/fetched/x/ITEMS.jsonl',
 R544=C+'/h1read/kit/build/adff67f7ae9/fetched/x/ITEMS.jsonl',
 R_D0m200=C+'/h1read/kit/build/ae470417b41/fetched/x/ITEMS.jsonl',
 R_D0m100=C+'/h1read/kit/build/af35386aa3e/fetched/x/ITEMS.jsonl',
 R_H1m100=C+'/h1read/kit/build/a24ea1a1936/fetched/x/ITEMS.jsonl')
# the eight direct types of the pooled rule, in registration order
TYPES=('object_counting','object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard',
       'object_rel_distance','object_size_estimation','route_planning','obj_appearance_order')
SHARED=TYPES[:6]; S_ONLY=('route_planning',); R_ONLY=('obj_appearance_order',)
S_TYPES=SHARED+S_ONLY; R_TYPES=SHARED+R_ONLY
ARMS=('544','D0m200','D0m100','H1m100')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def rows(p,fam,types):
    out={}
    for l in open(p):
        if not l.strip(): continue
        r=json.loads(l)
        if r['family']!=fam or r['task_type'] not in types: continue
        if r['id'] in out: raise ValueError('duplicate '+r['id'])
        if r['budget']!=2048 or not (0<=r['score']<=1): raise ValueError('bad row')
        out[r['id']]=r
    return out
def size_units():
    """dev-S1 object-size question unit from the D0 m100 main journals (h1size.py's rule)."""
    U=[('centimet','cm'),('millimet','mm'),('meter','m'),('metre','m'),('inch','in'),('feet','ft'),('foot','ft'),('yard','yd')]
    out={}
    for f in sorted(glob.glob(C+'/h1read/kit/build/af35386aa3e/fetched/x/main/a0/results/budget_2048/*/items_a0.jsonl')):
        for l in open(f):
            d=json.loads(l)
            if d.get('question_type')!='object_size_estimation': continue
            q=d['question'].lower(); u='?'
            for k,v in U:
                if k in q: u=v; break
            else:
                for v in ('cm','mm','m'):
                    if re.search(r'\b%s\b'%v,q): u=v; break
            out[d['id']]=u
    return out
def build():
    meta=dict(sources={k:dict(path=v,sha256=sha(v)) for k,v in SRC.items()},types=TYPES,arms=ARMS); arrays={}
    for ds,fam,types in (('S','main',S_TYPES),('R','a7',R_TYPES)):
        R={a:rows(SRC[(ds+'544') if a=='544' else ds+'_'+a],fam,types) for a in ARMS}
        ids=sorted(R['544'])
        for a in ARMS:
            if set(R[a])!=set(ids): raise ValueError('%s %s: item keys differ from the 544 read (%d vs %d)'%(ds,a,len(R[a]),len(ids)))
            for i in ids:
                x,y=R['544'][i],R[a][i]
                for f in ('task_type','room','scene','scoring_basis','level','pair_id','count_kind'):
                    if x.get(f)!=y.get(f): raise ValueError('metadata differs %s %s %s'%(ds,a,f))
        rooms=sorted({R['544'][i]['room'] for i in ids}); ri={r:k for k,r in enumerate(rooms)}
        arrays[ds+'_type']=np.array([TYPES.index(R['544'][i]['task_type']) for i in ids])
        arrays[ds+'_room']=np.array([ri[R['544'][i]['room']] for i in ids])
        arrays[ds+'_score']=np.array([[float(R[a][i]['score']) for a in ARMS] for i in ids])
        same=[0,0]
        for a in ARMS[1:]:
            for i in ids:
                if str(R['544'][i]['prediction'])==str(R[a][i]['prediction']):
                    same[0]+=1; same[1]+= R['544'][i]['score']==R[a][i]['score']
        meta[ds]=dict(family=fam,items=len(ids),rooms=len(rooms),steps={a:sorted({R[a][i]['step'] for i in ids}) for a in ARMS},
            per_type={t:int((arrays[ds+'_type']==TYPES.index(t)).sum()) for t in types},
            rooms_per_type={t:len({R['544'][i]['room'] for i in ids if R['544'][i]['task_type']==t}) for t in types},
            same_prediction_pairs=same[0],same_prediction_same_score=same[1],
            item_keys_sha256=hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest(),
            item_room_type_sha256=hashlib.sha256(''.join('%s\t%s\t%s\n'%(i,R['544'][i]['room'],R['544'][i]['task_type']) for i in ids).encode()).hexdigest(),
            rooms_sha256=hashlib.sha256(('\n'.join(rooms)+'\n').encode()).hexdigest())
        meta[ds+'_ids']=ids; meta[ds+'_rooms']=rooms
        if ds=='S':
            u=size_units(); imp=np.array([1 if u.get(i) in ('in','ft','yd') else 0 if u.get(i) in ('cm','mm','m') else -1 for i in ids])
            imp[arrays['S_type']!=TYPES.index('object_size_estimation')]=-1; arrays['S_imperial']=imp
            meta['S']['size_units']={k:int(sum(1 for i in ids if R['544'][i]['task_type']=='object_size_estimation' and u.get(i)==k)) for k in sorted(set(u.values()))}
    if set(meta['S_rooms'])&set(meta['R_rooms']): raise ValueError('room keys shared between sets')
    allrooms=['devS1:'+r for r in meta['S_rooms']]+['R0dev:'+r for r in meta['R_rooms']]
    meta['room_list_sha256']=hashlib.sha256(('\n'.join(allrooms)+'\n').encode()).hexdigest(); meta['rooms_total']=len(allrooms)
    np.savez('PAIRS.npz',**arrays); json.dump(meta,open('PAIRS_META.json','w'),indent=1)
    open('ROOM_LIST.txt','w').write('\n'.join(allrooms)+'\n')
    return meta
if __name__=='__main__':
    m=build()
    for ds in 'SR': print(ds,json.dumps({k:v for k,v in m[ds].items()}))
    print('room_list_sha256',m['room_list_sha256'],m['rooms_total'])
    for k,v in m['sources'].items(): print(k,v['sha256'][:8],v['path'])
