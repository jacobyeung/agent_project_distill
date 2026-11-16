import json, hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
from derivgen.box_v313 import box,serialize,BoxRegistry,sampled_box_512,replay_audit,number,audit_box,SAMPLER,parse
from derivgen.ground_v312 import wrap
BASE=Path('/scratch/jjyeung/orch_cd');OUT=Path('out');pins={}
def read(p):
    b=Path(p).read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def jl(p):return [json.loads(s) for s in read(p).splitlines()]
def load(p):return json.loads(read(p))
def frame(p):
    with np.load(p) as z:pose=np.asarray(z['c2w'][0],dtype=np.float64)
    up=np.array([0.,0.,1.]);h=pose[:3,2].copy();h[2]=0;h/=np.linalg.norm(h)
    return pose[:3,3],np.column_stack([np.cross(h,up),up,h])
def public(raw,t,F):return box((np.asarray(raw['centroid'])-t)@F,raw['axesLengths'],np.asarray(raw['normalizedAxes']).reshape(3,3)@F)
def check(pool,qid,names,raws,label,t,F):
    reg=BoxRegistry();events=[]
    for i,(name,raw) in enumerate(zip(names,raws),1):
        value=public(raw,t,F);body=serialize(name,f'B{i}',[1],1,value);reg.ingest(body,value)
        events.append(dict(call=f'<ground obj="{name}" mode="box">',response=wrap(body),audit=dict(full_precision_box=audit_box(value),box_label=f'B{i}',box_provider='annotation_full_box_v1',numpy_version=np.__version__)))
    body,values=reg.gap(names[0],names[1:]);events.append(dict(call=f'<gap a="{names[0]}" b="{names[1]}" rule="sampled_box_512">',response=wrap(body),audit=dict(sampler=dict(SAMPLER),ordered_box_labels=['B1','B2'],box_provider='annotation_full_box_v1',numpy_version=np.__version__)))
    got=replay_audit(events)[0];assert got==values[0]
    a,b=[reg.records[f'B{i}']['value'] for i in [1,2]]
    reverse=sampled_box_512(b,a)
    sign=box(**b);sign['axes'][0]*=-1
    flipped=sampled_box_512(a,sign)
    rounded=[parse(e['response'].split('\n',1)[1].rsplit('\n',1)[0])['value'] for e in events[:2]]
    rounded_gap=sampled_box_512(*rounded)
    return dict(printed_box_replay_m=rounded_gap,printed_box_error_m=abs(rounded_gap-label),printed_box_within_5pct=abs(rounded_gap-label)<=.05*abs(label),pool=pool,qid=qid,independent_label=label,printed_answer=number(got,2),
        canonical_answer=number(label,2),equal=number(got,2)==number(label,2),error_m=got-label,
        reverse_changes=number(reverse,2)!=number(got,2),sign_changes=number(flipped,2)!=number(got,2),events=events,
        support_note='Numeric serializer audit only; frame 1 is a placeholder, not a visibility claim.')
rows=[]
scenes=load(BASE/'ground_rows/work/pilot_expanded_input/scenes.json')
training=jl(BASE/'ground_rows/out/pilot_v4/candidates.jsonl')
for scene,e in scenes.items():
    p=e['gt']['path'];t,F=frame(p)
    with np.load(p) as z:
        boxes={str(n):dict(centroid=c,axesLengths=l,normalizedAxes=a) for n,c,l,a in zip(z['labels'],z['obb_centroid'],z['obb_lengths'],z['obb_axes'])}
    for r in training:
        if r['scene']==scene and r['type']=='object_abs_distance' and not r['not_seen']:
            ns=[r['roles'][k] for k in ['a','b']];rows.append(check('training',r['qid'],ns,[boxes[n] for n in ns],float(r['gt_answer']),t,F))
labels=jl(BASE/'e3_extents/out/dev_abs_distance_box_labels.jsonl')
annotations=load(BASE/'e3_extents/out/e3d/ANNOTATED_BOXES.json');groups=defaultdict(list)
for r in labels:groups[r['scene']].append(r)
for scene,group in sorted(groups.items()):
    sid=scene.split('/')[-1];t,F=frame(BASE/'toolprog/work/gt/scannet'/(sid+'.npz'))
    for r in group:
        ns=[o['name'] for o in r['objects']];bs=[annotations[sid][str(o['instance_id'])] for o in r['objects']]
        rows.append(check('dev',r['qid'],ns,bs,float(r['box_rule_label']),t,F))
summary={}
for pool,n in [('training',252),('dev',239)]:
    rr=[r for r in rows if r['pool']==pool];assert len(rr)==n
    summary[pool]=dict(total=n,survived=sum(r['equal'] for r in rr),max_error_m=max(abs(r['error_m']) for r in rr),
        reverse_changes=sum(r['reverse_changes'] for r in rr),axis_sign_changes=sum(r['sign_changes'] for r in rr),audit_replays=n,
        printed_box_median_error_m=float(np.median([r['printed_box_error_m'] for r in rr])),
        printed_box_p95_error_m=float(np.percentile([r['printed_box_error_m'] for r in rr],95)),
        printed_box_within_5pct=sum(r['printed_box_within_5pct'] for r in rr),
        printed_box_within_5pct_percent=100*sum(r['printed_box_within_5pct'] for r in rr)/n)
assert all(r['equal'] for r in rows),summary
(OUT/'AUDIT_REPLAY_r4.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
(OUT/'AUDIT_REPLAY_r4.json').write_text(json.dumps(dict(summary=summary,numpy_version=np.__version__,source_pins=pins),indent=2)+'\n')
for pool,r in summary.items():
    print(f"{pool}: matches {r['survived']}/{r['total']}; printed-box median {r['printed_box_median_error_m']:.2f} m, p95 {r['printed_box_p95_error_m']:.2f} m; within 5% {r['printed_box_within_5pct']}/{r['total']} ({r['printed_box_within_5pct_percent']:.2f}%)")
