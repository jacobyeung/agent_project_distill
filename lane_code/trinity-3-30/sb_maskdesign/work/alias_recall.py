import sys,json,collections,time
sys.path.insert(0,'/scratch/jjyeung/orch_n30/sb_kbox4')
import numpy as np
import train_pricing as T
F=T.F;K1=T.R.K1
ids=set(T.read(T.R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
caps=[c for c in json.loads(T.read(T.ROOT/'pinned_train.json'))['captures'] if any(r['id'] in ids for r in c['rows'])]
print('captures',len(caps),flush=True)
def dec(rle):
    m=np.repeat(np.arange(len(rle['counts']))%2==1,rle['counts']).reshape(rle['size'],order='F')
    return F.resize(m,F.SHAPE)[::2,::2]
def iou(m,t):
    i=np.count_nonzero(m&t);u=np.count_nonzero(m|t);return i/u if u else 0.
objs={};gate=collections.Counter();t0=time.time();srcs=collections.Counter()
for ci,c in enumerate(caps):
    key=T.R.digest(c['canonical'])[:16]
    cache=json.loads(open(K1/'run_convert_2'/key/'candidates.json').read())
    gt,_=T.R.gt_arrays(c);inst=gt['instances']
    rows=[r for r in c['rows'] if r['id'] in ids]
    w=collections.Counter(n for r in rows for n in r['operands'])
    for name,weight in w.items():
        iid=int(c['gt_name_ids'][name][0]);o=dict(raw=0.,cap30=0.,all=0.,alias=0.,w=weight,ds=c['canonical'].split('/')[0],nvis=0,alias_src=set())
        for slot in range(32):
            t=inst[slot]==iid
            if not t.any():continue
            o['nvis']+=1
            rec=cache['frames'][str(slot)]['phrases'].get(name)
            if rec is None:continue
            ent=[]
            for p in rec.get('instances',[]):
                sp=p.get('source_prompt',name);pres=float(p.get('source_presence',rec['presence']))
                if float(p['score'])*pres<.05:continue
                ent.append((float(p['score']),sp,p))
            ent.sort(key=lambda e:-e[0])
            raw=[e for e in ent if e[1]==name][:30]
            if not raw:
                s=rec.get('all_instance_scores') or [0.];mx=max(s);pr=float(rec['presence'])
                gate[('pres<.05' if pr<.05 else 'pres .05-.2' if pr<.2 else 'pres>=.2','cond>=.5' if mx>=.5 else 'cond .3-.5' if mx>=.3 else 'cond .05-.3' if mx>=.05 else 'cond<.05')]+=weight
            rawset={id(e[2]) for e in raw};cap30={id(e[2]) for e in ent[:30]}
            for s_,sp,p in ent:
                v=iou(dec(p['mask']),t);srcs[(name,sp)]+=1
                if id(p) in rawset:o['raw']=max(o['raw'],v)
                if id(p) in cap30:o['cap30']=max(o['cap30'],v)
                o['all']=max(o['all'],v)
                if sp!=name:
                    o['alias']=max(o['alias'],v)
                    if v>=.5:o['alias_src'].add(sp)
        objs[(c['canonical'],name)]=o
    if ci%40==0:print('done',ci+1,round(time.time()-t0),flush=True)
O=list(objs.values());W=sum(o['w'] for o in O)
def rep(title,f):print(title,'unique %d/%d (%.1f%%) row-weighted %d/%d (%.1f%%)'%(sum(f(o) for o in O),len(O),100*np.mean([f(o) for o in O]),sum(o['w'] for o in O if f(o)),W,100*sum(o['w'] for o in O if f(o))/W))
rep('raw pool has IoU>=.5 (cap 30)',lambda o:o['raw']>=.5)
rep('raw+alias pool cap 30 has IoU>=.5',lambda o:o['cap30']>=.5)
rep('raw+alias pool uncapped has IoU>=.5',lambda o:o['all']>=.5)
rep('raw miss recovered by alias (cap 30)',lambda o:o['raw']<.5 and o['cap30']>=.5)
rep('raw miss recovered by alias (uncapped)',lambda o:o['raw']<.5 and o['all']>=.5)
rep('raw hit lost under cap 30 with aliases',lambda o:o['raw']>=.5 and o['cap30']<.5)
by=collections.defaultdict(lambda:[0,0,0,0,set()])
for (cap,name),o in objs.items():
    b=by[name];b[0]+=o['w'];b[1]+=o['w']*(o['raw']<.5);b[2]+=o['w']*(o['raw']<.5 and o['cap30']>=.5);b[3]+=o['w']*(o['raw']<.5 and o['all']>=.5);b[4]|=o['alias_src']
print('BY NAME (row-weighted operands): name n raw_miss recovered_cap30 recovered_uncapped alias_sources_with_hit')
for k,v in sorted(by.items(),key=lambda kv:-kv[1][1])[:30]:print('   %-16s %4d %4d %4d %4d %s'%(k,v[0],v[1],v[2],v[3],sorted(v[4])))
print('names with alias-source instances in cache',sorted({n for (n,sp) in srcs if sp!=n}))
print('ZERO-RAW-CANDIDATE visible frames (row-weighted) presence x best conditional score:');tot=sum(gate.values())
for k,v in sorted(gate.items(),key=lambda kv:-kv[1]):print('   %-14s %-12s %5d %.1f%%'%(k[0],k[1],v,100*v/tot))
