import json, re, sys
from collections import defaultdict, Counter
C='/scratch/jjyeung/orch_n30/cont_ops16/work/c15'
F={'vsti200':C+'/h1vsti/kit/build/a35f73e87f0/fetched/x/r6/a0/results/0/items_a0.jsonl',
   'R0dev200':C+'/h1read/kit/build/a8102c3207b/fetched/x/a7/a0/results/0/items_a0.jsonl',
   'devS1_200':C+'/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/0/items_a0.jsonl'}
FR=re.compile(r'frames? (\d+(?:\.\d+)?)')
for name,p in F.items():
    d=defaultdict(lambda:[0,0.0,0,0]); ex=[]; spac=Counter()
    for l in open(p):
        r=json.loads(l); md=(r.get('media') or {}).get('metadata') or {}
        ts=md.get('timestamps') or (r.get('media') or {}).get('timestamps')
        fps=r.get('fps') or md.get('fps'); tot=r.get('total_num_frames') or md.get('total_num_frames')
        idx=r.get('source_frame_indices') or (r.get('media') or {}).get('source_frame_indices')
        if idx and fps: sp=(idx[-1]-idx[0])/31.0/fps
        elif ts: sp=(ts[-1]-ts[0])/(len(ts)-1)
        else: sp=None
        b='?' if sp is None else ('<=1.5s' if sp<=1.5 else ('1.5-4s' if sp<=4 else '>4s'))
        t=(r.get('raw_generation') or '').split('</think>')[0]; nums=[float(x) for x in FR.findall(t)]
        k=(r['question_type'],b); x=d[k]; x[0]+=1; x[1]+=r['score'] or 0; x[2]+=bool(nums and max(nums)>32); x[3]+=bool(nums)
        if len(ex)<3 and nums and max(nums)>32: ex.append((r['id'],fps,tot,round(sp,2) if sp else None,str(ts)[:80],sorted(set(nums))[-4:], idx[-3:] if idx else None))
    print('==',name)
    for k,v in sorted(d.items()): print('  %-30s %-7s n=%3d acc=%5.1f cites>32: %3d of %3d citing' % (k[0],k[1],v[0],100*v[1]/v[0],v[2],v[3]))
    for e in ex: print('  ex',e)
