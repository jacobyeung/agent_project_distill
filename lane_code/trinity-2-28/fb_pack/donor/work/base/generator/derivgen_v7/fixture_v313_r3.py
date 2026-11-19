"""Serial review fixtures with literal scene labels and explicit target scope."""
import json,copy,itertools,re,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from types import SimpleNamespace
from scipy.spatial import ConvexHull
def extent_ends(P):
    xy=P[:,:2];hull=xy[ConvexHull(xy).vertices];best=None
    for i in range(len(hull)):
        u=hull[(i+1)%len(hull)]-hull[i];u/=np.linalg.norm(u);v=np.array([-u[1],u[0]])
        Q=xy@np.column_stack((u,v));span=np.ptp(Q,axis=0)
        key=(float(np.prod(span)),i)
        if best is None or key<best[0]:best=(key,u if span[0]>=span[1] else v)
    axis=best[1]
    if axis[np.argmax(np.abs(axis))]<0:axis=-axis
    t=xy@axis
    return int(np.argmin(t)),int(np.argmax(t)),axis,float(np.ptp(t))

import numpy as np
from derivgen import ground_v312 as old
from derivgen import box_v313 as box
from derivgen.ground_v313 import Session,GTInstances,render,witness_pair
from derivgen.ground_v312_io import GTClip,reference
from derivgen.ground_v312_quality import shuffled_item
from derivgen.ground_v313_tokens import tokenizer_for_rows,gate_positions
BASE=Path('/scratch/jjyeung/orch_cd');OUT=Path('out/fixtures_r4');OUT.mkdir(exist_ok=True)
scenes=json.loads((BASE/'ground_rows/work/pilot_expanded_input/scenes.json').read_text())
source=[json.loads(s) for s in (BASE/'ground_rows/out/pilot_v4/candidates.jsonl').read_text().splitlines()]
backend=old.load_backend(BASE/'ground_rows/work/backend_v3122/ground_lifting.py')
P,M,_=reference(str(BASE/'mdg_next/work/rkit'))
tokenizer=tokenizer_for_rows(BASE/'derivgen/inputs/tokenizer_01/tokenizer.json',keypoint_calls=True)
count=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids)
families=['gap_witness','relative_gap_witness','unresolved','instances','counting','appearance_order','surface_pair','surface_pair_full','surface_pair_unavailable','extent_ends','absolute_sampled_box','relative_sampled_box']
rows={k:[] for k in families};refusals=Counter()
def absq(a,b):return f'Measuring from the closest point of each object, what is the distance between the {a} and the {b} (in meters)?'
def relq(a,bs):return f'Measuring from the closest point of each object, which of these objects ({", ".join(bs)}) is the closest to the {a}?'
def add(kind,row,scene,scope='benchmark'):
    if len(rows[kind])>=20:return
    if kind in ('relative_sampled_box','relative_gap_witness','appearance_order'):
        cap=20//len(row['options'])
        if sum(r['answer']==row['answer'] for r in rows[kind])>=cap:return
    row.update(family=kind,scene=scene,frame_indices=scenes[scene]['frame_indices'],training_admitted=False,
        review_scope=scope,excluded_from_benchmark_scoring=scope!='benchmark',
        reviewer_instruction='Check tool arithmetic and the declared target. Exclude observation/analytic fixtures from benchmark accuracy.' if scope!='benchmark' else 'Check benchmark wording and the measured gap against the independent answer; rounded boxes do not determine the measurement.',
        mdg_gate_token_positions=gate_positions(tokenizer,row['suffix'],keypoint_calls=True))
    if scope.startswith('analytic_complete_surface'):
        for event in row['events']:
            event['audit']=dict(box_provider='fit_gbox_best_v1',distance_rule='visible_surface',fixture_geometry='analytic_complete_discrete_surfaces')
    old.validate_evidence(row);assert row['suffix_tokens']<=5000
    assert row['question'] and row['answer']!='review-only'
    rows[kind].append(row)
def manual(q,s,calls,answer,conclusion):
    lines=['<think>','I will inspect the requested object observations.']
    for call in calls:lines.extend([call,old.wrap(s.execute(call))])
    lines += [conclusion,'</think>',f'<answer>{answer}</answer>'];suffix='\n'.join(lines)
    return dict(qid=q['qid'],type=q['type'],question=q['question'],options=q.get('options',[]),roles=q['roles'],
        answer=str(answer),answer_content=str(answer),suffix=suffix,suffix_tokens=count(suffix),events=s.events,
        gt_answer=str(answer),gt_authority=q.get('gt_authority','observed geometry fixture'),spec_version='3.13')

for scene,e in scenes.items():
    clip=GTClip(e['gt']['path'],e['frame_indices'],P,M);resolver0=GTInstances(clip);resolved={};lifted={}
    def resolver(n):
        if n not in resolved:resolved[n]=resolver0(n)
        return resolved[n]
    def lift(n,m,p,g,*,tau):
        key=(n,id(m),tau)
        if key not in lifted:lifted[key]=backend.lift_object(n,m,p,g,tau=tau)
        return copy.deepcopy(lifted[key])
    cached=SimpleNamespace(**{k:getattr(backend,k) for k in ['render_ground','gap_objects','render_gap','render_gaps','public_centres','number']},lift_object=lift)
    def session(**kw):return Session(cached,clip.geo,clip.masks,instances=resolver,**kw)
    normals=[r for r in source if r['scene']==scene and r['type']=='object_abs_distance' and not r['not_seen']]
    singles={}
    for name in sorted(set(map(str,clip.geo.labels))):
        s=session();objects=s._instances(name)
        if len(objects)==1:singles[name]=objects[0]
        native=sum(str(l)==name for l in clip.geo.labels)
        if objects and len(objects)==native:
            q=dict(qid=f'count-{scene}-{name}',type='object_counting',question=f'How many {name}(s) are in this room?',roles=dict(obj=name),gt_answer=str(native),gt_authority='native GT instance IDs; every instance has eligible support',options=[])
            for kind in ['counting','instances']:
                r=render(q,session(),count);r['roles']=q['roles'];add(kind,r,scene)
            if native>1:
                q['qid']='unresolved-'+q['qid']
                r=manual(q,session(),[f'<ground obj="{name}">',f'<ground obj="{name}" mode="instances">'],native,
                    f'The singular reference is unresolved. The enumeration finds {native} instances.')
                add('unresolved',r,scene)
    for i,src in enumerate(normals):
        a,b=[src['roles'][k] for k in ['a','b']]
        q={k:copy.deepcopy(src[k]) for k in ['qid','type','question','options','roles','gt_answer']};q['gt_authority']='pinned pilot_v4 independent annotated-box sampler'
        if len(rows['absolute_sampled_box'])<20:
            try:
                clip.validate_operands(q)
                q['independent_ordered_boxes']=[dict(name=n,**{k:np.asarray(v).tolist() for k,v in clip.geo.obb[int(singles[n]['instance_id'])].items()}) for n in [a,b]]
                r=render(q,session(box_provider=box.AnnotationBoxProvider()),count)
                r.update(roles=q['roles'],gt_answer=q['gt_answer'],gt_authority=q['gt_authority'],gt_agrees=True)
                old.replay(r,session(box_provider=box.AnnotationBoxProvider()));add('absolute_sampled_box',r,scene)
            except ValueError as exc:refusals[str(exc)]+=1
        if all(len(rows[k])>=20 for k in ['gap_witness','surface_pair','surface_pair_unavailable','extent_ends']):continue
        # Observation fixtures use benchmark wording but declare the visible target.
        q.pop('gt_answer',None);q['target_distance_rule']='visible_surface';q['gt_authority']='selected-frame observed surfaces (not benchmark boxes)'
        if len(rows['gap_witness'])<20:
            try:r=render(q,session(distance_rule='visible_surface'),count);r['roles']=q['roles'];add('gap_witness',r,scene,'visible_surface_observation')
            except ValueError as exc:refusals[str(exc)]+=1
        if len(rows['surface_pair'])<20:
            s=session(keypoint_calls=True)
            def provider(op,ns):
                pair=witness_pair(cached,*(s.objects[n] for n in ns))
                return dict(status='ok',observed_surface_points=True,**pair) if pair else dict(status='unavailable')
            s.keypoint_provider=provider
            for n in [a,b]:s.execute(f'<ground obj="{n}">')
            body=s.execute(f'<surface_pair a="{a}" b="{b}" mode="closest_visible">')
            if 'visible pair distance ' in body:
                ans=re.search(r'visible pair distance (\d+\.\d+) m',body)[1]
                lines=['<think>','I will measure the visible surfaces.']+[v for ev in s.events for v in [ev['call'],ev['response']]]+['The visible pair distance is '+ans+' m.','</think>',f'<answer>{ans}</answer>']
                suffix='\n'.join(lines);r=dict(qid=q['qid']+'-surface',type=q['type'],question=q['question'],options=[],roles=q['roles'],answer=ans,suffix=suffix,suffix_tokens=count(suffix),events=s.events,spec_version='3.13')
                add('surface_pair',r,scene,'visible_surface_observation')
        if len(rows['surface_pair_unavailable'])<20:
            s=session(keypoint_calls=True,keypoint_provider=lambda *_:dict(status='unavailable'))
            calls=[f'<ground obj="{n}">' for n in [a,b]]+[f'<surface_pair a="{a}" b="{b}" mode="closest_visible">',f'<gap a="{a}" b="{b}">']
            probe=session();[probe.execute(c) for c in calls[:2]];ans=probe.execute(calls[-1]).splitlines()[0].removesuffix(' m')
            if ans not in ('not seen','unresolved'):
                r=manual(q,s,calls,ans,f'The surface-pair provider is unavailable. The mask gap reports {ans} m.');add('surface_pair_unavailable',r,scene,'visible_surface_observation; forced provider failure')
        if len(rows['extent_ends'])<20 and a in singles:
            obj=singles[a];frame=obj['best']
            cloud=np.concatenate([np.asarray(obj['points'][str(f)]) for f in obj['frames']])
            point_frames=np.concatenate([np.full(len(obj['points'][str(f)]),f,int) for f in obj['frames']])
            start,end,axis,_=extent_ends(cloud)
            indices=[start,end];ends=cloud[indices];frames=point_frames[indices].tolist();distance=float(np.linalg.norm(ends[0]-ends[1]))
            s=session(keypoint_calls=True,keypoint_provider=lambda *_:dict(status='ok',positions=ends.tolist(),frames=frames,distance_m=distance,observed_surface_points=True))
            qe=dict(qid=q['qid']+'-extent',type='object_size_estimation',question=f'What is the length of the longest dimension (length, width, or height) of the {a}, measured in centimeters?',roles=dict(obj=a),options=[])
            probe=session(keypoint_calls=True,keypoint_provider=s.keypoint_provider)
            probe.execute(f'<ground obj="{a}">')
            printed=probe.execute(f'<extent_ends obj="{a}" axis="longest_observed">').splitlines()[-1].split()[-2]
            ans=str(int(round(float(printed)*100)))
            r=manual(qe,s,[f'<ground obj="{a}">',f'<extent_ends obj="{a}" axis="longest_observed">'],ans,f'The observed horizontal endpoint separation is {printed} m, or {ans} cm. This does not establish the full object size.')
            r['extent_audit']=dict(axis_world_xy=axis.tolist(),frames=frames,provider='hrp_rows/work/keypoints.py:extent_ends',source_sha256=hashlib.sha256((BASE/'hrp_rows/work/keypoints.py').read_bytes()).hexdigest())
            add('extent_ends',r,scene,'observed_horizontal_extent; excluded from full-size benchmark')
    # Derive independent sampler labels from annotation boxes before rendering.
    for a,b,c in itertools.combinations(singles,3):
        if len(rows['relative_sampled_box'])>=20 and len(rows['relative_gap_witness'])>=20 and len(rows['appearance_order'])>=20:break
        ns=[a,b,c]
        if len(rows['appearance_order'])<20:
            first={n:singles[n]['first'] for n in ns}
            if len(set(first.values()))==3:
                order=', '.join(sorted(ns,key=first.get));perms=[', '.join(p) for p in itertools.permutations(ns)][:4]
                if order not in perms:perms[-1]=order
                qa=dict(qid=f'appearance-{scene}-{a}-{b}-{c}',type='object_appearance_order',roles=dict(cands=ns),question='What will be the first-time appearance order of the following categories in the video: '+', '.join(ns)+'?',options=[f'{chr(65+i)}. {v}' for i,v in enumerate(perms)],gt_answer=chr(65+perms.index(order)),gt_authority='eligible recorded native instance first frames')
                qa=shuffled_item(qa)
                try:r=render(qa,session(),count);r.update(roles=qa['roles'],option_shuffle=qa['option_shuffle']);add('appearance_order',r,scene,'observed_first_frames')
                except ValueError as exc:refusals[str(exc)]+=1
        qr=dict(qid=f'relbox-{scene}-{a}-{b}-{c}',type='object_rel_distance',roles=dict(target=a,cands=[b,c]),question=relq(a,[b,c]),options=[f'A. {b}',f'B. {c}'],gt_authority='native annotation boxes; independent raw ordered sampler')
        raw=[]
        for n in ns:
            ob=clip.geo.obb[int(singles[n]['instance_id'])];raw.append(box.box(ob['centroid'],ob['axesLengths'],np.asarray(ob['normalizedAxes']).reshape(3,3)))
        ds=[box.sampled_box_512(raw[0],bb) for bb in raw[1:]];qr['gt_answer']='AB'[int(np.argmin(ds))]
        qr=shuffled_item(qr)
        qr['independent_ordered_boxes']=[dict(name=n,**{k:np.asarray(v).tolist() for k,v in clip.geo.obb[int(singles[n]['instance_id'])].items()}) for n in [a,*qr['roles']['cands']]]
        if len(rows['relative_sampled_box'])<20:
            try:
                clip.validate_operands(qr);r=render(qr,session(box_provider=box.AnnotationBoxProvider()),count)
                r.update(roles=qr['roles'],option_shuffle=qr['option_shuffle'],gt_answer=qr['gt_answer'],gt_authority=qr['gt_authority'],gt_agrees=True,independent_pair_distances_m=dict(zip([b,c],ds)))
                old.replay(r,session(box_provider=box.AnnotationBoxProvider()));add('relative_sampled_box',r,scene)
            except ValueError as exc:refusals[str(exc)]+=1
        if len(rows['relative_gap_witness'])<20:
            qr.pop('gt_answer');qr['target_distance_rule']='visible_surface'
            try:r=render(qr,session(distance_rule='visible_surface'),count);r.update(roles=qr['roles'],option_shuffle=qr['option_shuffle']);add('relative_gap_witness',r,scene,'visible_surface_observation')
            except ValueError as exc:refusals[str(exc)]+=1
    print(scene,{k:len(v) for k,v in rows.items()},flush=True)

# Full-surface positive fixtures require complete authority; use explicitly analytic
# discrete surfaces and genuine source-scene names, never claim a real full mesh.
oldfull=[json.loads(s) for s in Path('out/fixtures_r2/surface_pair_full.jsonl').read_text().splitlines()]
for i,r in enumerate(oldfull):
    src=source[i];scene=src['scene'];a,b=[src['roles'][k] for k in ['a','b']]
    def rename(value):
        if isinstance(value,str):return re.sub(r'\bstand\b',lambda _:a,re.sub(r'\bface\b',lambda _:b,value))
        if isinstance(value,list):return [rename(v) for v in value]
        if isinstance(value,dict):return {rename(k):rename(v) for k,v in value.items()}
        return value
    r=rename(r);ans=re.search(r'full surface gap (\d+\.\d+) m',r['suffix'])[1]
    r.update(qid=f'analytic-full-{i}',question=absq(a,b),answer=ans,roles=dict(a=a,b=b),options=[],
        source_name_qid=src['qid'],gt_authority='synthetic complete discrete surfaces; not the real source scene geometry')
    r['suffix']=r['suffix'].replace('<answer>review-only</answer>',f'<answer>{ans}</answer>');r['suffix_tokens']=count(r['suffix'])
    add('surface_pair_full',r,scene,'analytic_complete_surface; names borrowed from real scene')
# Multiple questions may exercise one real ambiguous name; these are explicit
# format variants, excluded from unique benchmark yield.
if rows['unresolved']:
    originals=list(rows['unresolved'])
    while len(rows['unresolved'])<20:
        r=copy.deepcopy(originals[len(rows['unresolved'])%len(originals)]);r['qid']+=f'-format-{len(rows["unresolved"])}'
        r['format_variant']=True;add('unresolved',r,r['scene'],'real_instance_ambiguity; repeated format variant')
for kind,rr in rows.items():
    (OUT/(kind+'.jsonl')).write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rr))
summary=dict(rows_by_family={k:len(v) for k,v in rows.items()},total=sum(map(len,rows.values())),
    letter_counts={k:dict(Counter(r['answer'] for r in rows[k])) for k in ['relative_sampled_box','relative_gap_witness','appearance_order']},
    max_suffix_tokens=max(r['suffix_tokens'] for rr in rows.values() for r in rr),refusals=dict(refusals),training_admitted=False,
    scope='Benchmark box families use real geometry and independent answers. Observation families use benchmark wording with an explicit observation target; exclude them from benchmark scoring. Full-surface positives are analytic fixtures with real scene names.')
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
assert all(len(rr)==20 for rr in rows.values()),summary['rows_by_family']
