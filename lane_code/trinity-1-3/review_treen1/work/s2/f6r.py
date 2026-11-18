import json,os,sys,collections
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c');K=W/'pkg';sys.path[:0]=[str(K/'work/tree_r1')]
os.environ['R2_FIXTURES']=str(K/'fixtures')
from student_pilot.r2_adapters import normalize
d=json.load(open('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json'));train=set(d['train_scenes']);held=set(d['heldout_scenes'])
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    ind=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    fr={raw['qid']:dict(fps=24.,total_num_frames=ind[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in ind])}
    return normalize(raw,fr)
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out');out={}
for fam,p in (('recovery',R/'recovery_v3/rows.jsonl'),('absolute_distance',R/'vehN_pool_abs_distance/repaired/rows.jsonl'),('units',R/'vehN_units/repaired/rows_slice.jsonl')):
    c=collections.Counter()
    for l in open(p):
        r=norm(json.loads(l));sc=str(r.get('dataset'))+'/'+str(r.get('scene'));c['in_train' if sc in train else 'outside']+=1;c['heldout']+=sc in held
    out[fam]=dict(c)
print(out);(W/'F6_routing.json').write_text(json.dumps(out))
