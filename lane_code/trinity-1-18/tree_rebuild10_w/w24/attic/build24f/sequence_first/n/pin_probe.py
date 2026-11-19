from pathlib import Path
import sys,json
assert all(not Path(p).exists() for p in ('/scratch/jjyeung','/data','/data2','/data3','/home'))
sys.path.insert(0,'/tmp/q_22c714e1/p/s')
from student_pilot.p3_provenance import load
from student_pilot.r1_persisted import scope
from student_pilot.r1_rooms import Rooms,verify_audit
cfg=load('/tmp/fixture/own.json');old=load('/tmp/fixture/oldcfg.json');request=load('/tmp/fixture/request.json');paths=request['_paths']
h='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'
before={k:v for k,v in paths.items() if k!=h}
with scope(before):
 try:Rooms(old['r1_training']['room_authority'])
 except ValueError as e:assert h in str(e);failure=str(e)
 else:raise AssertionError('baseline unexpectedly resolved reserve')
with scope(paths):
 Rooms(cfg['r1_training']['room_authority']);verify_audit(cfg,request['room_audit'])
bad=Path('/tmp/q_22c714e1/bad_reserve');bad.write_bytes(b'changed')
with scope({**paths,h:str(bad)}):
 try:Rooms(cfg['r1_training']['room_authority'])
 except ValueError as e:assert 'Missing or changed pinned input' in str(e);mutation=str(e)
 else:raise AssertionError('changed reserve accepted')
print(json.dumps(dict(status='PASS',before=failure,after='Rooms and verify_audit PASS',mutation=mutation)))
