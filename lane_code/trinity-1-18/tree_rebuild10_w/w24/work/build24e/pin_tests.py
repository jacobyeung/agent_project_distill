from pathlib import Path
import sys,subprocess,json
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
records={}
for name in ("q","n"):
 root=D/"sequence_final"/name;args=J.load(root/"view.json")
 old=L/"attic/build24e/work/build24/kits"/name
 J.write(root/"oldcfg.json",J.load(old/"k/n.json"))
 source="""from pathlib import Path
import sys,json
assert all(not Path(p).exists() for p in (\x27/scratch/jjyeung\x27,\x27/data\x27,\x27/data2\x27,\x27/data3\x27,\x27/home\x27))
sys.path.insert(0,\x27/tmp/q_22c714e1/p/s\x27)
from student_pilot.p3_provenance import load
from student_pilot.r1_persisted import scope
from student_pilot.r1_rooms import Rooms,verify_audit
cfg=load(\x27/tmp/fixture/own.json\x27);old=load(\x27/tmp/fixture/oldcfg.json\x27);request=load(\x27/tmp/fixture/request.json\x27);paths=request[\x27_paths\x27]
h=\x27bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3\x27
before={k:v for k,v in paths.items() if k!=h}
with scope(before):
 try:Rooms(old[\x27r1_training\x27][\x27room_authority\x27])
 except ValueError as e:assert h in str(e);failure=str(e)
 else:raise AssertionError(\x27baseline unexpectedly resolved reserve\x27)
with scope(paths):
 Rooms(cfg[\x27r1_training\x27][\x27room_authority\x27]);verify_audit(cfg,request[\x27room_audit\x27])
bad=Path(\x27/tmp/q_22c714e1/bad_reserve\x27);bad.write_bytes(b\x27changed\x27)
with scope({**paths,h:str(bad)}):
 try:Rooms(cfg[\x27r1_training\x27][\x27room_authority\x27])
 except ValueError as e:assert \x27Missing or changed pinned input\x27 in str(e);mutation=str(e)
 else:raise AssertionError(\x27changed reserve accepted\x27)
print(json.dumps(dict(status=\x27PASS\x27,before=failure,after=\x27Rooms and verify_audit PASS\x27,mutation=mutation)))
"""
 (root/"pin_probe.py").write_text(source)
 p=subprocess.run(args+["/opt/py/bin/python3.12","-B","/tmp/fixture/pin_probe.py"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (root/"pin_probe.log").write_text(p.stdout);assert p.returncode==0,p.stdout
 records[name]=json.loads(p.stdout);print(name,"PASS",flush=True)
J.write(D/"PIN_TESTS.json",dict(status="PASS",records=records))
