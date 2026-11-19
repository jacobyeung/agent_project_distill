import json
from pathlib import Path
import numpy as np
from test_v313 import session,item,count,backend,Geometry,masks,instances,raster_fixture
from derivgen.ground_v313 import Session,render,witness_pair
from derivgen.ground_v312 import wrap,validate_evidence
import os
from collections import Counter
from derivgen.ground_v312_quality import shuffled_item
out=Path(os.environ.get('V313_FIXTURES', 'out/fixtures_r2'));out.mkdir(parents=True,exist_ok=True)
all_rows={}
def raw_row(kind,index,s,calls):
 lines=['<think>','I will inspect the requested observed geometry.']
 for call in calls:
  lines.extend([call,wrap(s.execute(call))])
 lines += ['</think>','<answer>review-only</answer>']
 suffix='\n'.join(lines)
 r=dict(qid=f'{kind}-{index}',type=kind,suffix=suffix,events=s.events,suffix_tokens=count(suffix),
        spec_version='3.13',synthetic_fixture=True,training_admitted=False)
 if kind in ('unresolved','instances'):
  r['question']='How many chair(s) do we have in this room?'
 elif kind.startswith('surface_pair'):
  r['question']='Measuring from the closest point of each object, what is the distance between the stand and the face (in meters)?'
 validate_evidence(r)
 return r
for kind in ['gap_witness','relative_gap_witness','unresolved','instances','counting','appearance_order',
             'surface_pair','surface_pair_full','surface_pair_unavailable','extent_ends']:
 rows=[]
 letter_counts=Counter()
 for i in range(80 if kind in ('appearance_order','relative_gap_witness') else 20):
  if kind in ['gap_witness','relative_gap_witness']:
   q=item('object_abs_distance' if kind=='gap_witness' else 'object_rel_distance');q['qid']=f'{kind}-{i}'
   q['question']=('Measuring from the closest point of each object, what is the distance between the stand and the face (in meters)?' if kind=='gap_witness' else 'Measuring from the closest point of each object, which of these objects (face, far) is the closest to the stand?')
   q=shuffled_item(q)
   r=render(q,session(),count)
   r.update(roles=q['roles'],option_shuffle=q.get('option_shuffle'))
  elif kind=='counting':
   q,s,_=raster_fixture(i);q['question']='How many chair(s) do we have in this room?';r=render(q,s,count)
  elif kind=='instances':
   _,s,_=raster_fixture(i);r=raw_row(kind,i,s,['<ground obj="chair" mode="instances">'])
  elif kind=='unresolved':
   resolver=lambda name:[dict(e,instance_id=k) for k in range(2+i%3) for e in instances('stand')]
   s=Session(backend,Geometry(),masks,instances=resolver)
   r=raw_row(kind,i,s,['<ground obj="chair">'])
  elif kind=='appearance_order':
   def resolver(name):
    m,p=masks('stand');m[:]=False;m[(i%10) if name=='chair' else 20+i%10,20:28,20:28]=True
    return [dict(instance_id=name,masks=m,prob=m.any(axis=(1,2)).astype(float))]
   s=Session(backend,Geometry(),masks,instances=resolver)
   q=dict(qid=f'appearance-{i}',type='object_appearance_order',roles=dict(cands=['chair','table']),
          options=['A. chair, table','B. table, chair'],question='What will be the first-time appearance order of the following categories in the video: chair, table?',gt_answer='A',gt_authority='synthetic native raster first frames')
   q=shuffled_item(q)
   r=render(q,s,count)
   r.update(option_shuffle=q['option_shuffle'],roles=q['roles'])
  elif kind in ('surface_pair','surface_pair_full'):
   def resolver(name):
    m,p=masks(name);base=np.roll(m[3],-(i%3) if name=='stand' else i%7,axis=1);m[:]=False;m[(1 if name=='stand' else 18)+i%7]=base
    return [dict(instance_id=name,masks=m,prob=m.any(axis=(1,2)).astype(float))]
   s=Session(backend,Geometry(),masks,instances=resolver,keypoint_calls=True)
   def provider(op,names):
    pair=witness_pair(backend,*(s.objects[n] for n in names))
    result=dict(status='ok',observed_surface_points=True,**pair)
    if kind=='surface_pair_full':
     A,B=[np.asarray(s.objects[n]['points'][str(f)]) for n,f in zip(names,pair['frames'])]
     full=float(np.linalg.norm(A[:,None]-B[None,:],axis=2).min())
     result.update(full_surface_distance_m=full,true_closest_visible=True,full_surface_authority='synthetic complete discrete surfaces: exhaustive Cartesian distance')
    return result
   s.keypoint_provider=provider
   r=raw_row(kind,i,s,['<ground obj="stand">','<ground obj="face">','<surface_pair a="stand" b="face" mode="closest_visible">'])
   r['surface_audit']=dict(surfaces={n:s.objects[n]['points'] for n in ['stand','face']},pair={k:(v if k!='positions' else [p.tolist() for p in v]) for k,v in provider('surface_pair',['stand','face']).items()})
  else:
   def provider(op,names):
    if kind=='surface_pair_unavailable':return dict(status='unavailable')
    p=np.array([1+i*.03,3,1.]);q=p+np.array([.97+i*.02,0,0])
    v=dict(status='ok',positions=[p.tolist(),q.tolist()],frames=[2,19],distance_m=float(np.linalg.norm(p-q)),observed_surface_points=True)
    return v
   s=session(keypoint_calls=True,keypoint_provider=provider)
   calls=['<ground obj="stand">','<ground obj="face">']
   calls += ['<extent_ends obj="stand" axis="longest_observed">' if kind=='extent_ends' else '<surface_pair a="stand" b="face" mode="closest_visible">']
   r=raw_row(kind,i,s,calls)
  if kind in ('appearance_order','relative_gap_witness'):
   if letter_counts[r['answer']] >= 10:continue
   letter_counts[r['answer']] += 1
  r.update(synthetic_fixture=True,training_admitted=False)
  rows.append(r)
  if len(rows)==20:break
 assert len(rows)==20, (kind,'fixture shortage')
 if letter_counts:assert dict(letter_counts)=={'A':10,'B':10},letter_counts
 all_rows[kind]=rows
 (out/(kind+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
report=dict(rows_by_type={k:len(v) for k,v in all_rows.items()},total=sum(map(len,all_rows.values())),
 max_suffix_tokens=max(r['suffix_tokens'] for rows in all_rows.values() for r in rows),
 letter_balance={k:dict(Counter(r['answer'] for r in all_rows[k])) for k in ['appearance_order','relative_gap_witness']},
 synthetic=True,training_admitted=False,note='Format/geometry fixtures; review-only answers are not VQA targets.')
(out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
