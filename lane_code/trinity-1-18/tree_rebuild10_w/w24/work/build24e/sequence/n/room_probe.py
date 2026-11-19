from pathlib import Path
import sys,json
hidden=['/scratch/jjyeung','/home','/data','/data2','/data3']
assert all(not Path(p).exists() for p in hidden),hidden
sys.path.insert(0,'/tmp/q_22c714e1/p/s')
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import load
from student_pilot.r1_rooms import Rooms,verify_audit
from launch_r1.production_proof import run
request=load('/tmp/fixture/request.json');cfg=load('/tmp/fixture/own.json')
with scope(request.pop('_paths')):
 room=Rooms(cfg['r1_training']['room_authority']);assert len(room.reserve)==372
 audit=verify_audit(cfg,request['room_audit'])
 result=run(request,'/tmp/q_22c714e1/room_probe')
 assert result['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED',result
 print(json.dumps(dict(hidden_roots=hidden,room_reserve=372,room_authority='PASS',native_room_audit='PASS',refusal=result['refusal'])))
