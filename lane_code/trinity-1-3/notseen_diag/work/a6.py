import json,collections,re,numpy as np
MC='n2r/mc/sj/mask_recall_run/results/'
man={v:{c['native']:c for c in json.load(open(MC+v+'/MANIFEST.json'))['captures']} for v in ('dense','dense_aliases')}
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
rows=json.load(open('calls.json'))
H=collections.defaultdict(set)
for r in rows:
    if r['family']=='ground' and r['st'] in ('seen','not seen'): H[(r['id'],r['mode'],r['name'])].add(r['st'])
pairs=sorted(set((i,n) for (i,m,n) in H if m=='none'))
cache={}
def load(v,native):
    k=(v,native)
    if k not in cache:
        c=man[v].get(native)
        if c is None: cache[k]=None
        else:
            f=MC+v+'/candidates/'+c['scene'].replace('/','__')+'.npz'
            cache[k]=json.loads(np.load(f)['payload'].tobytes())
    return cache[k]
def area(rle):
    h,w=rle['size']; cnt=rle['counts']; on=sum(cnt[1::2]); return on/(h*w)
def stats(c,name):
    if c is None: return dict(cache='missing')
    ph=name.strip().lower()
    phrases=c['phrases']
    used=ph if ph in phrases else None
    if used is None:
        for cand in (ph[:-1] if ph.endswith('s') else None, ph[:-2] if ph.endswith('es') else None):
            if cand and cand in phrases: used=cand;break
    if used is None: return dict(cache='phrase_absent',phrases=len(phrases))
    nf03=0;maxs=0;maxj=0;n005=0;areas=[];pres=[];allmax=0;fr03=[]
    for slot in range(32):
        rec=c['frames'][str(slot)]['phrases'].get(used)
        if rec is None: continue
        pres.append(rec.get('presence',0)); allmax=max(allmax,max(rec.get('all_instance_scores') or [0]))
        ins=rec.get('instances') or []
        n005+=len(ins)
        s03=[e for e in ins if float(e['score'])>=.3]
        if s03: nf03+=1; fr03.append(slot+1); areas+= [area(e['mask'] if isinstance(e['mask'],dict) else eval(e['mask'])) for e in s03]
        for e in ins: maxs=max(maxs,float(e['score'])); maxj=max(maxj,float(e['joint_score']))
    return dict(cache='ok',phrase=used,n_kept=n005,n_frames_s03=nf03,max_score=maxs,max_joint=maxj,max_presence=max(pres) if pres else 0,
                max_query_score=allmax,max_area_s03=max(areas) if areas else 0,med_area_s03=float(np.median(areas)) if areas else 0,frames_s03=fr03,
                frames_match=c.get('frame_indices')==I_frames)
out=[]
for i,n in pairs:
    it=I[i]; I_frames=it['source_frame_indices']
    d=stats(load('dense',it['native']),n); a=stats(load('dense_aliases',it['native']),n)
    st=next(iter(H[(i,'none',n)]))
    out.append(dict(id=i,name=n,native=it['native'],dataset=it['dataset'],h1=st,dense=d,alias=a,
                    x05=next(iter(H.get((i,'scale_scene:0.5',n),{None}))), x2=next(iter(H.get((i,'scale_scene:2',n),{None})))))
json.dump(out,open('pairs_cache.json','w'))
C=collections.Counter()
for o in out:
    d=o['dense']
    if d['cache']!='ok': cls=d['cache']
    elif d['n_kept']==0: cls='A_no_proposal'
    elif d['n_frames_s03']==0: cls='B_below_score_floor'
    else: cls='C_proposal_s03'
    o['cls']=cls; C[(o['h1'],cls)]+=1
for k,v in sorted(C.items()): print(k,v)
print('frames_match',collections.Counter(o['dense'].get('frames_match') for o in out))
json.dump(out,open('pairs_cache.json','w'))
