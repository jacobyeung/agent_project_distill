import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,seal
k=Path(__file__).resolve().parents[1];seal(k)
if load(k/'k/a.json')['GO'] is not True:raise ValueError('E03')
r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
sys.path.insert(0,str(r/'s'))
from student_pilot.p3_provenance import load as read,pinned
from student_pilot.carrier_c1_run import identity,train
from student_pilot.r1_persisted import scope
cfg=read(sys.argv[2]);before=read(pinned(q['config']))
if identity(cfg)!=identity(before) or cfg['world_size']!=4:raise ValueError('E82')
from launch_r1.entry import admit
request=load(r.parent/'r.json')
from launch_r1.production_proof import verify_staging
with scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):
 verify_staging(request)
 admit(cfg)
 # A resume card makes this allocation continue the dead allocation's newest uploaded state, which b/rs.py
 # staged and the tree's latest_resume/restore authenticate; without a card the leg starts fresh as before.
 resume=None
 if (k/'k/rs.json').is_file():
  staged=read(r.parent/'rs_ok.json')
  if staged.get('schema')!='n-resume-stage-v1' or staged.get('binding',{}).get('config_sha256')!=identity(cfg):raise ValueError('E88')
  resume='latest'
 train(cfg,None,resume)
