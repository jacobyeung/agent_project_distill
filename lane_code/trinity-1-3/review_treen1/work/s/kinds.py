import json,sys,collections
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_treen1/work/pkg')
sys.path[:0]=[str(K/'work/tree_r1')]
from student_pilot.extent_receipt import required
from student_pilot.r2_adapters import normalize
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=indices[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    return normalize(raw,frames)
srcs={f:K/'work/rows_slices/slices_final'/(f+'.jsonl') for f in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded','a0_room')}
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
srcs.update(rep_recovery=R/'recovery_v3/rows.jsonl',rep_dist=R/'vehN_pool_abs_distance/repaired/rows.jsonl',rep_units=R/'vehN_units/repaired/rows_slice.jsonl')
for f,p in srcs.items():
    c=collections.Counter()
    for i,line in enumerate(open(p)):
        raw=json.loads(line);row=norm(raw)
        stream='vqa' if f=='a0_room' else 'routing'
        g=row.get('ground_record',row)
        can=(g.get('canonical') or row.get('provenance',{}).get('canonical') or row.get('dataset','?')+'/')
        c[(row.get('question_type',row.get('type',g.get('type'))),required(row,stream),can.split('/')[0],bool(g.get('not_seen')))]+=1
    print(f,i+1,dict(c))
