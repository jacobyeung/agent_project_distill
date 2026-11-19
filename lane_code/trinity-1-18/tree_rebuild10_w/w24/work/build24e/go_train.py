from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24e';root=D/'go';k=L/'out/kit_n_go';ns='/tmp/q_22c714e1'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
args=J.load(D/'GO_VIEW.json');records=[]
steps=[('room audit',[sys.executable,'-B',str(k/'b/d.py'),ns+'/p2/s',ns+'/r2.json',ns+'/n.json',ns+'/rooms.json']),
 ('h.py writes v.json',[sys.executable,'-B',str(k/'b/h.py'),ns+'/p2',ns+'/v.json']),
 ('fixture frame-host and review evidence',[sys.executable,'-B',str(D/'fixture_gates.py')]),
 ('t.py / u.py / native train',[sys.executable,'-B',str(D/'boundary.py'),str(k/'b/t.py'),ns+'/p2',ns+'/v.json'])]
for i,(stage,cmd) in enumerate(steps):
 with (root/('stage'+str(i)+'.log')).open('w') as log:r=subprocess.run(args+cmd,stdout=log,stderr=subprocess.STDOUT)
 if i==2 and r.returncode==0:J.write(D/'GO_GATES.json',J.load(root/'gates.json'))
 records.append(dict(stage=stage,returncode=r.returncode,log=str(root/('stage'+str(i)+'.log'))));J.write(D/'GO_TRAIN.json',records);print(stage,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
