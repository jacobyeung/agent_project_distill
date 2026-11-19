import sys,json,collections
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
BEST={'heater':'radiator','coat hanger':'coat rack'}
P={}
for c in caps:
    key=T.R.digest(c['canonical'])[:16]
    cache=json.loads(open(K1/'run_convert_2'/key/'candidates.json').read())
    gt,_=T.R.gt_arrays(c);inst=gt['instances']
    for name in {n for r in c['rows'] if r['id'] in ids for n in r['operands']}:
        iid=int(c['gt_name_ids'][name][0]);b=dict(raw05=0.,raw30=0.,w30=0.)
        w=BEST.get(name,name)
        for slot in range(32):
            t=inst[slot]==iid
            if not t.any():continue
            rec=cache['frames'][str(slot)]['phrases'].get(name)
            if rec is None:continue
            by=collections.defaultdict(list)
            for p in rec.get('instances',[]):
                sp=p.get('source_prompt',name);pres=float(p.get('source_presence',rec['presence']))
                if float(p['score'])*pres>=.05:by[sp].append((float(p['score']),p))
            for sp in {name,w}:
                for s,p in sorted(by.get(sp,[]),key=lambda e:-e[0])[:30]:
                    x=iou(dec(p['mask']),t)
                    if sp==name:
                        b['raw05']=max(b['raw05'],x)
                        if s>=.3:b['raw30']=max(b['raw30'],x)
                    if sp==w and s>=.3:b['w30']=max(b['w30'],x)
        P[(c['canonical'],name)]=b
recs=json.load(open('/scratch/jjyeung/orch_n30/sb_maskfail/out/MASKFAIL.json'))['records']
ops=collections.defaultdict(list)
for r in recs:ops[(r['row'],r['object'])].append(r)
thr=np.linspace(.5,.95,10)
def mra(p,l):return 0. if p is None else float(np.mean(abs(p-l)/l<=1-thr+1e-12))
sc={}
with open('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl') as f:
    for line in f:
        if '"A0_deployed"' in line or '"A2_gt_masks"' in line:
            r=json.loads(line)
            if r['arm'] in('A0_deployed','A2_gt_masks'):sc[(r['arm'],r['row_id'])]=mra(r['prediction'],r['label'])
byrow=collections.defaultdict(list)
for (row,obj),rs in ops.items():
    rs=sorted(rs,key=lambda r:r['frame']);vis=[r for r in rs if r['visible'] and r['valid']];served=[r for r in rs if r['served_area']>0]
    pf=rs[0].get('pricing_best_frame');pr=rs[pf-1] if pf else None
    mx=max([r['iou'] for r in vis],default=0.);mp=max([r['precision'] for r in served],default=0.)
    if not served:cat='refused'
    elif pr is not None and pr['visible'] and (pr['iou'] or 0)>=.5:cat='good'
    elif mx>=.5:cat='poorframe'
    elif mx<.1 and mp<.2:cat='wrong'
    else:cat='weak'
    byrow[row].append(dict(cat=cat,name=obj,**P[(rs[0]['capture'],obj)]))
N=len(byrow)
def gap(rows):return 100*sum(sc[('A2_gt_masks',r)]-sc[('A0_deployed',r)] for r in rows)/N
bad=lambda o:o['cat'] in('wrong','refused')
sel=[r for r,os_ in byrow.items() if any(bad(o) for o in os_)]
print('rows with a wrong-object or refused operand',len(sel),'gap %.2f'%gap(sel))
L3=[r for r in sel if all(o['raw30']>=.5 for o in byrow[r] if bad(o))]
L2=[r for r in sel if r not in set(L3) and all(o['raw05']>=.5 for o in byrow[r] if bad(o))]
L1=[r for r in sel if not all(o['raw05']>=.5 for o in byrow[r] if bad(o))]
print('layer 3: every bad operand has an IoU>=.5 raw candidate at score>=.3 (lift floor): rows %d gap %.2f'%(len(L3),gap(L3)))
print('layer 2: only below the lift floor (joint>=.05, score<.3): rows %d gap %.2f'%(len(L2),gap(L2)))
print('layer 1: not in the raw pool at joint>=.05: rows %d gap %.2f ; of which refused rows %d gap %.2f'%(len(L1),gap(L1),sum(any(o['cat']=='refused' for o in byrow[r]) for r in L1),gap([r for r in L1 if any(o['cat']=='refused' for o in byrow[r])])))
ph=[r for r in sel if not all(o['raw30']>=.5 for o in byrow[r] if bad(o)) and all(max(o['raw30'],o['w30'])>=.5 for o in byrow[r] if bad(o))]
print('rows outside layer 3 whose bad operands are all reachable at the lift floor once heater->radiator and coat hanger->coat rack: rows %d gap %.2f (A0 %.1f A2 %.1f)'%(len(ph),gap(ph),100*np.mean([sc[('A0_deployed',r)] for r in ph]),100*np.mean([sc[('A2_gt_masks',r)] for r in ph])))
hr=[r for r,os_ in byrow.items() if any(o['name'] in BEST for o in os_)]
print('rows naming heater or coat hanger',len(hr),'A0 %.1f A2 %.1f gap %.2f ; with a bad heater/coat hanger operand: %d'%(100*np.mean([sc[('A0_deployed',r)] for r in hr]),100*np.mean([sc[('A2_gt_masks',r)] for r in hr]),gap(hr),sum(any(bad(o) and o['name'] in BEST for o in byrow[r]) for r in hr)))
ref=[r for r,os_ in byrow.items() if any(o['cat']=='refused' for o in os_)]
print('refused rows',len(ref),'names',collections.Counter(o['name'] for r in ref for o in byrow[r] if o['cat']=='refused').most_common(8))
