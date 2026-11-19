import copy,csv,hashlib,json,math,re,sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path('/scratch/jjyeung/orch_n30/sb_rowB')
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
TREE=W/'w19/work/tree_r1'
sys.path.insert(0,str(TREE))
from student_pilot import trace_grammar,r2_adapters,r2_contract
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
from inventory import sha, classify, wording,FAMILIES

def load(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(l) for l in Path(p).open() if l.strip()]
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
def jsonl(p,values):Path(p).write_text(''.join(json.dumps(v,sort_keys=True,allow_nan=False)+'\n' for v in values))
def canonical_hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',str(s).strip().lower().replace('_',' '))
def native_validate(row):
 packed=r2_adapters.normalize(row)
 r2_contract.validate(packed,'vqa',require_frames=False)
 errors=trace_grammar.validate_row(row)
 if errors:raise ValueError(','.join(sorted({e.rule_id for e in errors})))
 return packed

def kit_pins():
 seal=load(W/'w19/out/TREE_SEAL.json'); pins={str(W/'w19/out/TREE_SEAL.json'):sha(W/'w19/out/TREE_SEAL.json')}
 for name in ['student_pilot/trace_grammar.py','student_pilot/r2_grammar.py','student_pilot/r2_adapters.py','student_pilot/r2_contract.py','student_pilot/r1_rooms.py','student_pilot/row_removals.py','generator/derivgen_v7/derivgen/ground_v312_quality.py']:
  h=sha(TREE/name);assert seal['files'][name]==h; pins[str(TREE/name)]=h
 return pins

class RoomRule:
 def __init__(self):
  self.paths={
   'split':ROOT/'inputs/K1SPLIT_R0.json','visits':ROOT/'inputs/arkit_3dod_metadata.csv',
   'r0':W/'inputs/rooms/R0_ROOMS.txt','withheld':W/'w19/fixtures/work/shared/WITHHELD_ROOMS_80.json',
   'dev':W/'w19/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json',
   'benchmark':W/'w19/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'}
  self.pins={str(p):sha(p) for p in self.paths.values()}
  for key,prefix in [('split','27126674'),('visits','657020f2'),('r0','bdb5d402'),('withheld','634820b4'),('dev','969cdb56'),('benchmark','3119aa4a')]:assert self.pins[str(self.paths[key])].startswith(prefix),(key,self.pins)
  split=load(self.paths['split']);assert split['teacher_k1']['sha256'].startswith('4d4736cf')
  self.k1={c['room'] for c in split['teacher_k1']['captures'] if c['k1_split']=='heldout'}
  self.r0=set(self.paths['r0'].read_text().splitlines())|{c['room'] for c in split['r0_scenes']['captures'].values()}
  self.visits={r['video_id']:r['visit_id'] for r in csv.DictReader(self.paths['visits'].open())}
  wh=load(self.paths['withheld']);self.wh=set(wh['rooms'])|{a for v in wh['aliases'].values() for a in v}
  dev=load(self.paths['dev']);dn=[a for f in ('natives','rooms','physical_groups') for a in dev[f]]
  for f in ('canonical','aliases'):
   for k,v in dev[f].items():dn.extend([k,*v])
  ben=load(self.paths['benchmark']);bn=ben['scenes']+ben['physical_groups']+['/'.join(p) for p in ben['rung1_tokens']]
  bn += [c+'/'+s for c,ss in ben.get('other_corpora',{}).items() for s in ss]
  self.dev={self.key(v) for v in dn};self.ben={self.key(v) for v in bn};self.wh={self.key(v) for v in self.wh}
 def key(self,v):
  ds,sc=v.split('/',1);ds={'d1':'scannet','d2':'scannetpp','scannetppv2':'scannetpp','scannet++':'scannetpp','d3':'arkitscenes'}.get(ds,ds)
  return ds+'/'+sc
 def room(self,c):
  c=self.key(c);ds,sc=c.split('/',1)
  if ds=='scannet':return ds+'/'+re.match(r'scene\d+',sc).group()
  if ds=='scannetpp':return c
  if ds=='arkitscenes':
   visit=self.visits.get(sc)
   return ds+('/venue'+visit if visit and visit!='NA' else '/capture'+sc)
  raise ValueError('unresolved room '+c)
 def reasons(self,r):
  canonical=r['provenance']['canonical'];room=self.room(canonical)
  names={self.key(canonical),self.key(room),self.key(r['dataset']+'/'+r['scene'])}
  return sorted(k for k,s in [('k1_heldout',self.k1),('r0',self.r0),('withheld80',self.wh),('dev_s1',self.dev),('benchmark_v2',self.ben)] if names&s)

def calculate(r,gt):
 z=gt['arrays'];p=r['provenance'];k=p['camera_frame'];assert 1<=k<=32
 assert len(z['c2w'])==32 and z['frame_indices']==r['student_input']['frame_indices']
 assert re.search(r'frame '+str(k)+r' of 32',r['student_input']['question'])
 assert z.get('valid',[True]*32)[k-1]
 pose=np.array(z['c2w'][k-1],float);camera=pose[:3,3];rot=pose[:3,:3]
 assert np.isfinite(pose).all() and np.allclose(rot.T@rot,np.eye(3),atol=.02)
 assert p['geometry_audit']['passed'] and gt['raster_sha256']==p['raster_sha256']
 objs=[]
 for inst in p['instances']:
  j=z['ids'].index(inst['id']);assert norm(z['labels'][j])==inst['label']
  center=np.array(z['obb_centroid'][j],float);axes=np.array(z['obb_axes'][j],float).reshape(3,3)
  if p['geometry_audit']['axes_layout']=='columns':axes=axes.T
  half=np.array(z['obb_lengths'][j],float)*p['geometry_audit']['box_half_factor']
  assert (half>0).all() and np.isfinite(half).all() and np.allclose(axes@axes.T,np.eye(3),atol=2e-5)
  local=axes@(camera-center);clipped=np.clip(local,-half,half)
  closest=center+axes.T@clipped
  dist=float(np.linalg.norm(np.maximum(np.abs(local)-half,0)))
  cc=np.linalg.solve(rot,center-camera);pc=np.linalg.solve(rot,closest-camera)
  assert abs(np.linalg.norm(closest-camera)-dist)<1e-4
  objs.append(dict(id=inst['id'],label=inst['label'],center_world=center.tolist(),axes_rows=axes.tolist(),half_extents=half.tolist(),center_camera=cc.tolist(),closest_world=closest.tolist(),closest_camera=pc.tolist(),distance=dist))
 order=sorted(objs,key=lambda o:o['distance'])
 assert all(b['distance']-a['distance']>.299 for a,b in zip(order,order[1:]))
 if r['question_type'].startswith('camera_'):semantic=order[0]['label']
 else:semantic='Near' if objs[0]['distance']<objs[1]['distance'] else 'Far'
 options={s.split('. ',1)[0]:s.split('. ',1)[1] for s in r['student_input']['options']}
 answers=[k for k,v in options.items() if v==semantic];assert len(answers)==1
 return dict(frame=k,camera_world=camera.tolist(),camera_c2w=pose.tolist(),objects=objs,order=[o['label'] for o in order],answer=answers[0],semantic=semantic)

def cid(r):
 return candidate_identity(dict(qid=r['qid'],scene=r['scene'],frame_indices=r['student_input']['frame_indices'],type=r['question_type'],question=r['student_input']['question'],options=r['student_input']['options']))
def vec(v):return '('+', '.join(f'{float(x):.4f}' for x in v)+')'
def render(r,g,numeric):
 k=g['frame'];by={o['label']:o for o in g['objects']}
 obs=[by[s.split('. ',1)[1]] for s in r['student_input']['options']] if r['question_type'].startswith('camera_') else g['objects']
 lines=[f'Step 1: take the camera viewpoint of frame {k}'+(f'; the camera centre is at {vec(g["camera_world"])} m in world coordinates. Camera coordinates use right, down and forward.' if numeric else '. Compare each object with this camera position.')]
 for i,o in enumerate(obs,2):
  if numeric:
   text=f'its centre is at {vec(o["center_camera"])} m in camera coordinates; its closest point is at {vec(o["closest_camera"])} m, giving a camera-to-object distance of {o["distance"]:.4f} m.'
  else:
   x,y,z=o['center_camera'];phrases=['to the right' if x>0 else 'to the left','below' if y>0 else 'above','in front of' if z>0 else 'behind']
   text=f'its centre is {phrases[0]} of the camera, {phrases[1]} it and {phrases[2]} it. Measure distance from the camera centre to the closest point of the object.'
  lines.append(f'Step {i}: locate the {o["label"]} relative to the camera in frame {k}; '+text)
 if r['question_type'].startswith('camera_'):
  lines.append(f'Step {len(lines)+1}: ordered nearest to farthest from the camera viewpoint of frame {k}, the objects are '+', then '.join(g['order'])+'.')
  lines.append(f'So the {g["semantic"]} is closest to that camera viewpoint.')
 else:
  a,b=g['objects'];near,far=g['order']
  lines.append(f'Step {len(lines)+1}: from the camera viewpoint of frame {k}, the {near} has a shorter camera-to-object distance than the {far}.')
  lines.append(f'So the {a["label"]} is {"nearer" if g["semantic"]=="Near" else "farther"} than the {b["label"]} relative to that camera viewpoint.')
 return '<think>\n'+'\n'.join(lines)+'\n</think>\n\n'+g['answer']
