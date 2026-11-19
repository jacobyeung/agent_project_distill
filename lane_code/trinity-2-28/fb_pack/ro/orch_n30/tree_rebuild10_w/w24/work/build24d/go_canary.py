from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
args=J.load(D/'GO_VIEW.json');k=L/'out/kit_n_go';ns='/tmp/q_22c714e1'
cmd=args+[sys.executable,'-B',str(D/'boundary.py'),str(k/'b/a.py'),'q',ns+'/p',ns+'/r.json']
with (D/'go/canary.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
record=dict(stage='a.py q',returncode=r.returncode)
result=D/'go/p/q/RESULT.json'
if result.exists():record['result']=J.load(result)
J.write(D/'GO_CANARY.json',record);print(json.dumps(record,indent=2))
