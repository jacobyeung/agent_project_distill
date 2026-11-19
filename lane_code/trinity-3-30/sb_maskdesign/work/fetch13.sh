echo "=== mfrev verdict"; head -c 7000 /scratch/jjyeung/orch_n30/sb_mfrev/REVIEW_VERDICT.md; echo; ls /scratch/jjyeung/orch_n30/sb_mfrev | head -30
mkdir -p /tmp/sbmd_jjyeung && cd /tmp/sbmd_jjyeung
cat > alias_recall2.py <<'PYEOF'
import sys,json,collections,time
sys.path.insert(0,'/scratch/jjyeung/orch_n30/sb_kbox4')
import numpy as np
import train_pricing as T
F=T.F;K1=T.R.K1
ids=set(T.read(T.R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
caps=[c for c in json.loads(T.read(T.ROOT/'pinned_train.json'))['captures'] if any(r['id'] in ids for r in c['rows'])]
def dec(rle):
    m=np.repeat(np.arange(len(rle['counts']))%2==1,rle['counts']).reshape(rle['size'],order='F')
    return F.resize(m,F.SHAPE)[::2,::2]
def iou(m,t):
    i=np.count_nonzero(m&t);u=np.count_nonzero(m|t);return i/u if u else 0.
objs={}
for ci,c in enumerate(caps):
    key=T.R.digest(c['canonical'])[:16]
    cache=json.loads(open(K1/'run_convert_2'/key/'candidates.json').read())
    gt,_=T.R.gt_arrays(c);inst=gt['instances']
    rows=[r for r in c['rows'] if r['id'] in ids]
    w=collections.Counter(n for r in rows for n in r['operands'])
    for name,weight in w.items():
        iid=int(c['gt_name_ids'][name][0]);best=collections.defaultdict(float);nfr=collections.Counter();o=dict(w=weight,name=name)
        for slot in range(32):
            t=inst[slot]==iid
            if not t.any():continue
            rec=cache['frames'][str(slot)]['phrases'].get(name)
            if rec is None:continue
            by=collections.defaultdict(list)
            for p in rec.get('instances',[]):
                sp=p.get('source_prompt',name);pres=float(p.get('source_presence',rec['presence']))
                if float(p['score'])*pres<.05:continue
                by[sp].append((float(p['score']),p))
            allent=sorted([(s,sp,p) for sp,v in by.items() for s,p in v],key=lambda e:-e[0])[:30]
            hit=set()
            for sp,v in by.items():
                for s,p in sorted(v,key=lambda e:-e[0])[:30]:
                    x=iou(dec(p['mask']),t)
                    for tag,ok in ((sp+'@.05',True),(sp+'@.3',s>=.3)):
                        if ok:
                            best[tag]=max(best[tag],x)
                            if x>=.5:hit.add(tag)
                    if any(p is q for _,_,q in allent):
                        for tag,ok in (('POOL@.05',True),('POOL@.3',s>=.3)):
                            if ok:
                                best[tag]=max(best[tag],x)
                                if x>=.5:hit.add(tag)
            for tag in hit:nfr[tag]+=1
        o['best']=dict(best);o['nfr']=dict(nfr);objs[(c['canonical'],name)]=o
O=list(objs.values());Wt=sum(o['w'] for o in O)
def rec(tagf):return sum(o['w'] for o in O if tagf(o))
raw=lambda o,fl:o['best'].get(o['name']+fl,0.)>=.5
print('row-weighted operands',Wt)
print('raw@.05 %d  raw@.3(lift floor) %d  pooled@.05 %d  pooled@.3 %d'%(rec(lambda o:raw(o,'@.05')),rec(lambda o:raw(o,'@.3')),rec(lambda o:o['best'].get('POOL@.05',0)>=.5),rec(lambda o:o['best'].get('POOL@.3',0)>=.5)))
def bestpolicy(o,fl):
    return max([v for k,v in o['best'].items() if k.endswith(fl) and not k.startswith('POOL')],default=0.)>=.5
print('any single phrase alone (oracle per object) @.05 %d @.3 %d'%(rec(lambda o:bestpolicy(o,'@.05')),rec(lambda o:bestpolicy(o,'@.3'))))
names=collections.defaultdict(list)
for o in O:names[o['name']].append(o)
print('BY NAME: per phrase alone, row-weighted objects with an IoU>=.5 candidate at conditional score>=.3 (and joint>=.05); n; [median frames with such a candidate among hits]')
tot_raw=0;tot_best=0
for n,v in sorted(names.items(),key=lambda kv:-sum(o['w'] for o in kv[1])):
    phr=sorted({k[:-3] for o in v for k in o['best'] if k.endswith('@.3') and not k.startswith('POOL')}|{n})
    cnt={p:sum(o['w'] for o in v if o['best'].get(p+'@.3',0.)>=.5) for p in phr}
    med={p:(np.median([o['nfr'].get(p+'@.3',0) for o in v if o['best'].get(p+'@.3',0.)>=.5]) if cnt[p] else 0) for p in phr}
    N=sum(o['w'] for o in v);tot_raw+=cnt[n];b=max(cnt,key=lambda p:(cnt[p],p==n));tot_best+=cnt[b]
    if len(phr)>1 or cnt[n]<N*0.8:
        print('   %-14s n=%3d '%(n,N)+' | '.join('%s=%d[%.0f]'%(p,cnt[p],med[p]) for p in phr)+('   <-- best single phrase: %s'%b if b!=n else ''))
print('TOTAL raw-name@.3 %d ; best single phrase per name (in-sample choice)@.3 %d of %d'%(tot_raw,tot_best,Wt))

PYEOF
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=/tmp/sbmd_jjyeung/cache MPLCONFIGDIR=/tmp/sbmd_jjyeung/mpl TMPDIR=/tmp/sbmd_jjyeung
ulimit -v 40000000
echo "=== ALIAS2"; nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B alias_recall2.py 2>&1 | tail -c 9000
