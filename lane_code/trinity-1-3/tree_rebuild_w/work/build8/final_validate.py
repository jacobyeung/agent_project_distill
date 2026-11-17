"""Freeze and validate the corrected input wiring; package groups execute once."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';py=[sys.executable,'-I','-s','-B']
state=json.loads((B/'FINAL_PASS.json').read_text()) if (B/'FINAL_PASS.json').exists() else []
def run(name,command,required=False):
 record=dict(step=name,command=command,started=time.time(),status='running')
 state.append(record);save()
 with (B/('final_'+name+'.log')).open('w') as log:
  result=subprocess.run(command,cwd=L,stdout=log,stderr=subprocess.STDOUT,env=os.environ)
 record.update(returncode=result.returncode,finished=time.time(),status='complete' if result.returncode==0 else 'failed');save()
 if result.returncode<0:raise RuntimeError('Process killed; no retry')
 if required and result.returncode:raise SystemExit('Validation prerequisite failed: '+name)
 return result.returncode
def save():
 (B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
 with (B/'STATUS.md').open('a') as f:f.write('\n'+state[-1]['step']+': '+state[-1]['status']+' (`work/build8/FINAL_PASS.json`).\n')
if (B/'proofs/packet/results.json').exists():
 (B/'proofs/packet/INITIAL_RESULTS.json').write_bytes((B/'proofs/packet/results.json').read_bytes())
if (B/'kits').exists():
 if (B/'kits_prebinding').exists():raise SystemExit('Final staging already began; resume completed package groups directly')
 (B/'kits').rename(B/'kits_prebinding')
run('staging',py+[str(B/'build_kits.py')],True)
for name in ('review_evidence','audit_code','resolve_resize','legacy_guard_proof','seal','make_delivery'):
 run(name,py+[str(B/(name+'.py'))],True)
run('packet_root',['bash',str(B/'PACKET_TEST.sh')],True)
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])],True)
for name in ('targeted','compare','coverage_all'):
 run(name,py+[str(B/(name+'.py'))])
for mode in ('scan','c8r','gf1'):
 run('eat1_'+mode,py+[str(B/'proofs/eat1/run_eat1.py'),mode])
with (B/'STATUS.md').open('a') as f:f.write('\nFinal checks finished. Review current suite comparison and coverage before issuing the report.\n')
