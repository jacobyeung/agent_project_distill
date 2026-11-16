import sys, glob, collections, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_owngrd/work/code2')
from owngrd.common import read_json
W='/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_partial/'
cp=collections.Counter(); why_role=collections.Counter(); ub_num=ub_den=0; multi=collections.Counter()
distill_frames=collections.Counter(); per_name_weight=[]
for f in sorted(glob.glob(W+'*.labels.json.gz')):
    lab=read_json(f)
    slots=list(lab['frames'])
    for name,v in lab['clip_presence'].items():
        role=lab['roles'][name]
        cp[(role, v)]+=1
        rows=[lab['frames'][s][name] for s in slots]
        ids=sorted({i for r in rows for i in r['gt_visible']})
        if ids:
            multi[min(len(ids),6)]+=1
            # upper bound: best 4 frames (greedy, sep 2) covering distinct ids, capped 5
            cover=[set(r['gt_visible']) for r in rows]; chosen=[]; got=set()
            for _ in range(4):
                best=max((i for i in range(len(rows)) if all(abs(i-j)>=2 for j in chosen)), key=lambda i: len(cover[i]-got), default=None)
                if best is None: break
                chosen.append(best); got|=cover[best]
            ub_num+=min(5,len(got)); ub_den+=len(ids)
        valid=[r for r in rows if r['presence'] is not None]
        dis=[r for r in rows if r['presence'] is None or role in ('confuser','absent')]
        for r in rows:
            if r['presence'] is None: distill_frames[(r['why'], 'target_hi' if r['teacher_presence']>.5 else 'target_lo')]+=1
        # effective per-frame weight of a disputed frame vs agreed frame in presence head
        nd=[r for r in rows if r['why']=='disputed_absent']
        if nd and valid and role=='gt':
            per_name_weight.append((0.5/len(dis))/(1.0/len(valid)))
print('clip_presence by role', dict(cp))
tot=sum(cp.values()); print('items',tot,'absent items frac %.3f'%(sum(v for (r,p),v in cp.items() if p==0)/tot), 'None frac %.3f'%(sum(v for (r,p),v in cp.items() if p is None)/tot))
print('presence-None frames by why and teacher target', dict(distill_frames))
print('GT-instance count per name', dict(multi))
print('recall@5 upper bound over all GT instances with 4 shortlisted frames: %.3f (%d/%d)'%(ub_num/ub_den, ub_num, ub_den))
if per_name_weight: print('disputed frame weight / agreed frame weight in presence head: median %.1f'%np.median(per_name_weight), len(per_name_weight))
