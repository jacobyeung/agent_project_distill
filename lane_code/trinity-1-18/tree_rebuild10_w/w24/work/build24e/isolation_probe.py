from pathlib import Path
import sys,json,subprocess
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
records={}
for name in ("q","n"):
 root=D/"sequence"/name;args=J.load(root/"view.json")
 script=root/"room_probe.py";script.write_text("""from pathlib import Path
import sys,json
hidden=[\x27/scratch/jjyeung\x27,\x27/home\x27,\x27/data\x27,\x27/data2\x27,\x27/data3\x27]
assert all(not Path(p).exists() for p in hidden),hidden
sys.path.insert(0,\x27/tmp/q_22c714e1/p/s\x27)
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import load
from student_pilot.r1_rooms import Rooms,verify_audit
from launch_r1.production_proof import run
request=load(\x27/tmp/fixture/request.json\x27);cfg=load(\x27/tmp/fixture/own.json\x27)
with scope(request.pop(\x27_paths\x27)):
 room=Rooms(cfg[\x27r1_training\x27][\x27room_authority\x27]);assert len(room.reserve)==372
 audit=verify_audit(cfg,request[\x27room_audit\x27])
 result=run(request,\x27/tmp/q_22c714e1/room_probe\x27)
 assert result[\x27refusal\x27]==\x27ValueError:R1_PROOF_FRAME_HOST_REQUIRED\x27,result
 print(json.dumps(dict(hidden_roots=hidden,room_reserve=372,room_authority=\x27PASS\x27,native_room_audit=\x27PASS\x27,refusal=result[\x27refusal\x27])))
""")
 p=subprocess.run(args+["/opt/py/bin/python3.12","-B","/tmp/fixture/room_probe.py"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (root/"room_probe.log").write_text(p.stdout);records[name]=dict(returncode=p.returncode,output=p.stdout)
 print(name,p.returncode,p.stdout[-600:]);assert p.returncode==0
J.write(D/"ISOLATED_ROOMS.json",records)
