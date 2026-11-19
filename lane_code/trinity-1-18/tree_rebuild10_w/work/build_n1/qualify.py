"""Run the final source qualification sequentially; preserve every completed receipt."""
import json,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build_n1';records=[]
def run(name,args):
    row=dict(step=name,started=time.time(),status='running',command=list(map(str,args)));records.append(row)
    (B/'QUALIFICATION.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Starting '+name,flush=True)
    code=subprocess.run(list(map(str,args)),cwd=L).returncode
    row.update(status='complete' if code==0 else 'failed',returncode=code,finished=time.time())
    (B/'QUALIFICATION.json').write_text(json.dumps(records,indent=2)+'\n')
    if code<0:raise SystemExit('Process was killed; no retry is authorized')
    if code:raise SystemExit(code)
py=[sys.executable,'-I','-s','-B']
run('targeted',py+[B/'phase.py','targeted'])
run('packet',py+[B/'phase.py','packet'])
run('delivery',py+[B/'make_delivery.py'])
delivery=json.loads((B/'DELIVERY.json').read_text())
run('frozen_package',['bash',B/'PACKAGE_TEST.sh',L/delivery['path']])
run('final_receipts',py+[B/'finalize.py'])
