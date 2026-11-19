"""Repeat acceptance reads after supplemental proofs, then refresh the report."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
state=json.loads((B/'FINAL_PASS.json').read_text())
commands=[('eat1_final_'+mode,[str(B/'proofs/eat1/run_eat1.py'),mode]) for mode in ('scan','c8r','gf1')]
commands.append(('report',[str(B/'report.py')]))
for name,args in commands:
 record=dict(step=name,started=time.time(),status='running');state.append(record)
 (B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
 with (B/(name+'.log')).open('w') as log:
  result=subprocess.run([sys.executable,'-I','-s','-B',*args],cwd=L,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
 record.update(returncode=result.returncode,finished=time.time(),status='complete' if result.returncode==0 else 'failed')
 (B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
 if result.returncode<0:raise RuntimeError('Acceptance process was killed; no retry')
 if name=='report' and result.returncode:raise SystemExit(result.returncode)
 print(json.dumps(record),flush=True)
