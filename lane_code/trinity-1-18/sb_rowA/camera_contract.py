"""Pinned N camera admission, native packing, and independent geometry checks."""
import copy, gzip, hashlib, json, math, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
BASE=Path('/scratch/jjyeung/orch_n30')
TREE=BASE/'tree_rebuild10_w/w19/work/tree_r1'
W19=TREE.parents[1]
SRC=BASE/'sb_evidence/aws_sources/ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__routing__rows.camera_rows.jsonl.gz'
TYPES=('camera_displacement','camera_rotation','camera_movement_direction')
INPUTS={}
sys.path.insert(0,str(TREE))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,expected=None):
 p=Path(p).resolve();h=sha(p)
 assert expected is None or h==expected,(str(p),h,expected)
 INPUTS[str(p)]=h
 return {'path':str(p),'sha256':h}
def load(p,expected=None):pin(p,expected);return json.loads(Path(p).read_text())
def save(p,d):Path(p).write_text(json.dumps({**d,'input_sha256':dict(INPUTS)},ensure_ascii=False,indent=2)+'\n')
def enc(d):return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def dh(d):return hashlib.sha256(enc(d).encode()).hexdigest()
def frozen():
 d=load(OUT/'HELDOUT_FREEZE.json')
 for p,h in d['input_sha256'].items():pin(p,h)
def bind_code():
 seal=load(W19/'out/TREE_SEAL.json')
 for module in list(sys.modules.values()):
  file=getattr(module,'__file__',None)
  if file and Path(file).is_relative_to(TREE) and file.endswith('.py'):
   rel=str(Path(file).relative_to(TREE));pin(file,seal['files'][rel])
 return seal['tree_sha256']
class Admission:
 def __init__(self):
  from student_pilot.r1_rooms import Rooms
  from student_pilot.row_removals import Removals
  from student_pilot.s1_exclusions import Exclusions
  self.cfg=load(W19/'work/build19/inputs/config.json')
  for p in self.cfg['r1_training']['room_authority'].values():pin(p['path'],p['sha256'])
  self.rooms=Rooms(self.cfg['r1_training']['room_authority'])
  lists=copy.deepcopy(self.cfg['remove_files'])
  lists.append(pin(BASE/'sb_k1list/out/u_union.json'))
  for p in lists:pin(p['path'],p['sha256'])
  self.removals=Removals(lists)
  self.alias=load(BASE/'sb_alias2/out/TIERED_ALIAS_MAP.json')['aliases']
  audit=load(BASE/'sb_alias2/out/ROOM_AUDIT_TIERED.json')
  self.roomsets={'R0':self.rooms.r0,'K1':self.rooms.k1}
  for name,rec in audit['list_checks'].items():
   p=rec['pin'];pin(p['path'],p['sha256'])
   if name in ('BENCH v2','dev-S1','withheld-80'):
    d=json.loads(Path(p['path']).read_text());self.roomsets[name]=set(d['rooms' if name=='withheld-80' else 'physical_groups'])
  for key in ('dev_scene_exclusions','benchmark_scene_exclusions'):
   p=self.cfg[key];pin(p['path'],p['sha256'])
  self.scenes=Exclusions(self.cfg['dev_scene_exclusions'],self.cfg['benchmark_scene_exclusions'])
  self.manifest=load(SRC.with_name(SRC.name.replace('.jsonl.gz','.MANIFEST.json')))
  pin(SRC,'9e6aa2bd618588a4054a71dc183bc31821fcb5a2bc7bb1952bbebe15559e7c6b')
  assert self.manifest['out']['sha256']==INPUTS[str(SRC)]
  assert self.manifest['source']['pin_ok'] and self.manifest['source']['sha256']=='c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53'
 def resolve(self,r):
  from student_pilot.carrier_c1_routing import alias_of
  token=r['dataset']+'/'+r['scene'];record=self.alias.get(token)
  own=r['routing'].get('canonical')
  if record:
   canonical=record['canonical'];how='tier_'+record['tier']
   assert own is None or self.rooms.room(own)==self.rooms.room(canonical)
  elif own and alias_of(own)==token:canonical=own;how='row_canonical_verified_mint'
  else:raise ValueError('MISSING proven scene mapping: '+token)
  assert alias_of(canonical)==token or record is not None
  room=self.rooms.room(canonical)
  if own:assert self.rooms.room(own)==room
  assert r['routing'].get('physical_group') in (None,room,canonical,own)
  return canonical,room,how
 def reasons(self,r):
  canonical,room,how=self.resolve(r)
  hits=['remove:'+Path(self.removals.files[i]['path']).name for i in self.removals.match(r)]
  hits += ['room:'+name for name,rooms in self.roomsets.items() if room in rooms]
  hits += ['N_scene:'+name for name,yes in self.scenes.matches(r).items() if yes]
  status,_,_=self.rooms.status(dict(r,canonical=canonical))
  if status!='ok':assert 'room:R0' in hits or 'room:K1' in hits
  return hits,canonical,room,how
 def scan(self):
  with gzip.open(SRC,'rt') as f:
   for line in f:
    x=json.loads(line);r=json.loads(x['row']);assert r['routing']['question_type'] in TYPES
    yield x,r

def frames(r):
 events=r['routing']['events'];ds=[e for e in events if e['kind']=='decision'];assert len(ds)==1
 b=ds[0]['binding'];i,j,n=b['i'],b['j'],b['M']
 assert all(type(x) is int for x in (i,j,n)) and 1<=i<j<=n==32
 assert n==len(r['student_input']['frames'])==len(r['student_input']['frame_indices'])==len(r['routing']['gt_pose9'])
 calls=[e for e in events if e['kind']=='tool_call'];assert len(calls)==1
 name='turn' if r['routing']['question_type']=='camera_rotation' else 'move'
 assert calls[0]['arguments']=={'from':i,'to':j} and calls[0]['token']==f'<{name} from={i} to={j}>'
 return i,j,n

def candidate(r):
 from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
 si=r['student_input'];raw=r['routing']
 return candidate_identity(dict(qid=r['qid'],scene=r['scene'],frame_indices=si['frame_indices'],type=raw['question_type'],question=si['question'],options=si['options'],trace_revision=raw['trace_revision']))

def native_validate(r):
 from student_pilot.carrier_c1_routing import c1_row,check_row
 from student_pilot.r1_training import row_check
 from student_pilot.r2_contract import frame_metadata
 raw=copy.deepcopy(r['routing']);si=r['student_input'];frames(r)
 # Reconstruct only the native pack envelope; evidence and targets remain source bytes.
 raw.update(schema='derivgen-row-v2',infrastructure_only=False,target=r['target'],question=si['question'],options=si['options'],
  provenance=dict(canonical=raw['canonical'],physical_group=raw['physical_group'],alias=r['dataset']+'/'+r['scene'],frame_indices=si['frame_indices'],source_row_sha256=raw['source_row_sha256']))
 rgb=dict(si,frames=[dict(p,source_index=i) for p,i in zip(si['frames'],si['frame_indices'],strict=True)])
 p=c1_row(raw,rgb)
 for k in r:assert p[k]==r[k],('pack differs',k,r['qid'])
 check_row(raw);row_check(r,'routing');frame_metadata(si)
 return p

def geometry(r):
 """Recompute camera centers, level axes and decisions without generator geometry code."""
 import numpy as np
 from scipy.spatial.transform import Rotation
 i,j,_=frames(r);raw=r['routing'];p=np.asarray(raw['gt_pose9'],dtype=float)
 up=np.asarray(raw['gt_up'],dtype=float);assert np.isfinite(p).all() and np.isfinite(up).all()
 down=-up/np.linalg.norm(up)
 def basis(rot):
  forward=rot[:,2]-np.dot(rot[:,2],down)*down
  assert np.linalg.norm(forward)>1e-6
  forward/=np.linalg.norm(forward)
  return np.stack((np.cross(down,forward),down,forward),axis=1)
 transform=np.diag([1.,-1.,1.]) @ basis(np.eye(3)).T
 def pose(k):
  rot=Rotation.from_quat(p[k-1,3:7]).as_matrix().T
  center=-rot@p[k-1,:3]
  if k==1:rot,center=np.eye(3),np.zeros(3)
  # Native readout quantizes operands to eight decimal places before arithmetic.
  t=np.array([round(float(x),8) for x in transform@center])
  b=np.array([[round(float(x),8) for x in row] for row in transform@basis(rot)])
  return t,b
 ti,ri=pose(i);tj,rj=pose(j)
 delta=ri.T@(tj-ti);distance=round(float(np.linalg.norm(delta)),2)+0.
 delta[1]*=-1;dx,dy,dz=[round(float(x),2)+0. for x in delta]
 a,b=ri[[0,2],2],rj[[0,2],2]
 angle=round(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0],float(a@b))))
 turn=(angle+180)%360-180 if (angle+180)%360 else 180
 kind=raw['question_type'];resp=[e for e in raw['events'] if e['kind']=='tool_response'];assert len(resp)==1
 if kind=='camera_rotation':
  answer=str(turn);printed=f'turn = {turn:+d} deg';values={'c1.turn':{'value':turn,'unit':'degree'}}
 else:
  printed=f'dx = {dx:+.2f} m, dy = {dy:+.2f} m, dz = {dz:+.2f} m, distance = {distance:.2f} m'
  values={'c1.delta':{'value':[dx,dy,dz],'unit':'m'},'c1.distance':{'value':distance,'unit':'m'}}
  if kind=='camera_displacement':answer=f'{distance:.2f}'
  else:
   scores={'left':-dx,'right':dx,'forward':dz,'backward':-dz}
   opts={o.split('. ',1)[0]:scores[o.split('. ',1)[1].lower()] for o in r['student_input']['options']}
   answer=max(opts,key=opts.get);assert list(opts.values()).count(opts[answer])==1
 assert resp[0]['text']==printed,(r['qid'],'geometry response',resp[0]['text'],printed)
 assert resp[0]['values']==values
 assert raw['answer']==raw['gt_answer']==answer,(r['qid'],'geometry answer')
 assert r['target'].endswith('\n\n'+answer)
 return dict(answer=answer,dx=dx,dy=dy,dz=dz,distance=distance,turn=turn)
