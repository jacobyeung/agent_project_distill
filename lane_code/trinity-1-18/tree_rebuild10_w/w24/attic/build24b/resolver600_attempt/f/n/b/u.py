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
with scope(cfg['r1_training']['persisted_files']):
 admit(cfg)
 train(cfg)
