"""Separate visible-frame limits from compatibility counts and missing inputs."""
import ast,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/build8/proofs/audit'
rows=json.loads((L/'work/build7/proofs/audit/FRAME64_REMAINING_SITES.json').read_text())
def site(name,function,owner=None):
 root=ast.parse((T/name).read_text())
 if owner:root=next(n for n in ast.walk(root) if isinstance(n,ast.ClassDef) and n.name==owner)
 nodes=ast.walk(root)
 return name+':'+str(next(n.lineno for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==function))
result=[]
for row in rows:
 name=row['file'];text=row['text'];r=dict(row)
 r['source']='work/build7/proofs/audit/FRAME64_REMAINING_SITES.json'
 r['proof']='work/build8/proofs/frames/results.json; work/build8/proofs/frame_stream/results.json; work/build8/proofs/direct/results.json; work/build8/proofs/final_repairs/results.json'
 if name.endswith('carrier_c1_routing.py'):
  function='direct_row' if row['line']>=880 else 'c1_row' if row['line']>=760 else 'query_tensor' if row['line']>=690 else 'camera' if row['line']>=275 else '__init__'
  r.update(status='closed locally',evidence=site(name,function),reason='The visible frame dimension is now derived from the configured count, the pose tensor or the bound RGB frame list; both supported counts run through native tiny-model proofs.')
 elif name.endswith('ground_sources.py'):
  function='native_candidates' if row['line']<100 else '_detect' if row['line']>=150 else '__init__'
  r.update(status='closed locally',evidence=site(name,function,'TowerSAM3' if function=='__init__' else None),reason='The cache reader uses the actual clip count; the tower boundary validates and retains that count. Both supported counts use the real cache producer and candidate reader.')
 elif name.endswith('carrier_c1_data.py'):
  nested=any(w in text for w in ('anchor','Nested','nested_indices')) and ('not nested' not in text)
  r.update(status='compatibility count' if nested else 'closed locally',evidence=name+':'+str(row['line']),
   reason='The nested compatibility layout intentionally supervises its anchor subset inside a denser clip; this is not the configured visible-frame dimension.' if nested else 'The operative dimension follows frame_count or the RGB list. Remaining fixed-count wording describes a legacy contract or error message; native preservation producer, reader and RGB forward pass at both supported counts.')
 elif name.endswith('camera_rows.py'):
  if '[:32]' in text:
   r.update(status='not a frame dimension',reason='This is the row-identity digest width.',evidence=site(name,'_row'))
  elif 163<=row['line']<=195:
   r.update(status='blocked',blocker='FRAME64_CANONICAL_GT_LOADER_UNQUALIFIED',evidence=site(name,'from_gt_scene'),reason='The local adapter uses the manifest count, but the upstream GTScene loader still binds the legacy fixed-size canonical NPZ inventory. Full qualification needs an admitted canonical GT/RGB/annotation input and its frame-count contract; no loader stand-in was used.')
  elif row['line']>=500:
   r.update(status='blocked',blocker='SEALED_GOAL_SCENE_EXCLUSIONS_MISSING',evidence=site(name,'camera_rows'),reason='The producer propagates the clip count, but whole-scene selection requires the exact sealed goal-scene exclusions absent from this lane. The per-row producer and pose adapter are tested without bypassing that admission gate.')
  elif row['line']<25 or 118<=row['line']<=125:
   r.update(status='documentation',reason='This describes the legacy source layout; the adapter accepts either supported visible-frame count.',evidence=site(name,'from_pose_row'))
  else:
   r.update(status='closed locally',reason='The pose encoder, pose-row adapter, shape checks, generated question and plan binding derive their dimension from the clip. The real per-row producer and tiny model are tested at both supported counts.',evidence=site(name,'_row' if row['line']>=340 else 'from_pose_row' if row['line']>=116 and row['line']<163 else '_validate' if row['line']>=227 else '_encode'))
 else:
  r.update(status='blocked',blocker='FRAME64_ALL_READERS_UNQUALIFIED',reason='The production reader input and full model/processor qualification remain absent.',evidence=name+':'+str(row['line']))
 result.append(r)
result.append(dict(file='student_pilot/carrier_c1_sweep.py',status='blocked',blocker='FRAME64_DENSE_POSE_ADMISSION_UNQUALIFIED',evidence=site('student_pilot/carrier_c1_sweep.py','dense_pose_row'),reason='The legacy dense-pose admission contract requires all_frames32 and fixed target shapes. Qualifying the longer clip needs an admitted dense source manifest and its target contract; this build leaves that production admission unchanged.',source='work/tree_r1/student_pilot/carrier_c1_sweep.py'))
(P/'FRAME64_SITE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'FRAME64_REMAINING_SITES.json').write_text(json.dumps([r for r in result if r['status']=='blocked'],indent=2)+'\n')
