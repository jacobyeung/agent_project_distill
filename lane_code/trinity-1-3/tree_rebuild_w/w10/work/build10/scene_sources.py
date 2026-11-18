from pathlib import Path
import json,sys
from collections import Counter
L=Path(__file__).resolve().parents[2];B=L/'work/build10';P=B/'proofs/division'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned
bindings=load(B/'F6_BINDING.json');division=load(pinned(bindings['division']));train=set(division['train_scenes']);heldout=set(division['heldout_scenes'])
results={}
for family,source in load(B/'inputs/row_sources.json').items():
    if family not in ('recovery','absolute_distance','units'):continue
    counts=Counter();examples=[]
    with Path(source['source']['path']).open() as f:
        for line in f:
            row=json.loads(line)
            from student_pilot.carrier_c1_routing import alias_of
            scene=row['dataset']+'/'+row['scene'] if row.get('dataset') else row.get('provenance',{}).get('alias') or alias_of(row['canonical'])
            counts['read']+=1
            counts['outside']+=scene not in train;counts['heldout']+=scene in heldout
            if scene not in train and len(examples)<5:examples.append(dict(qid=row['qid'],scene=scene))
    results[family]=dict(counts=counts,examples=examples,source=source['source'])
(P/'ROUTING_SCENES.json').write_text(json.dumps(dict(division=bindings['division'],families=results),indent=2)+'\n')
print(json.dumps(results))
