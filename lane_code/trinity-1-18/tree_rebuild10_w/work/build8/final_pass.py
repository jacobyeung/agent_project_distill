"""Sequential final validation, with durable package-group receipts."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
state=json.loads((B/'FINAL_PASS.json').read_text()) if (B/'FINAL_PASS.json').exists() else []
def run(name,command):
 record=dict(step=name,command=command,started=time.time(),status='running')
 state.append(record);save()
 with (B/('final_'+name+'.log')).open('w') as log:
  result=subprocess.run(command,cwd=L,stdout=log,stderr=subprocess.STDOUT,env=os.environ)
 record.update(returncode=result.returncode,finished=time.time(),status='complete' if result.returncode==0 else 'failed')
 save()
 if result.returncode<0: raise RuntimeError('A process was killed; stop without retry')
 return result.returncode
def save():
 (B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
 with (B/'STATUS.md').open('a') as f:
  f.write('\nFinal validation: '+state[-1]['step']+' '+state[-1]['status']+'; evidence `work/build8/FINAL_PASS.json`.\n')
py=[sys.executable,'-I','-s','-B']
# The initial staging diagnosed input closure. Preserve it and restage final bytes from empty.
if os.environ.get('B8_KEEP_FINAL_KITS')!='1' and not (B/'kits_diagnostic').exists() and (B/'kits').exists(): (B/'kits').rename(B/'kits_diagnostic')
names=['seal','make_delivery']
if not (B/'kits/RESULTS.json').exists():names.insert(0,'build_kits')
else:
 sys.path.insert(0,str(L/'work/tree_r1'))
 from launch_r2.build import verify
 from student_pilot.source_seal import inventory
 from student_pilot.p3_provenance import digest,load
 for arm in ('a2','a0'):
  root=B/'kits'/arm;verify(root)
  assert load(root/'k/launch.json')['source_revision']=='sha256:'+digest(inventory(L/'work/tree_r1'))
for name in names:
 if run(name,py+[str(B/(name+'.py'))]): raise SystemExit('Packaging prerequisite failed: '+name)
run('packet',['bash',str(B/'PACKET_TEST.sh')])
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])])
run('supplemental',py+[str(B/'targeted.py')])
run('guards',py+[str(B/'legacy_guard_proof.py')])
run('compare',py+[str(B/'compare.py')])
run('coverage',py+[str(B/'coverage_all.py')])
for mode in ('scan','c8r','gf1'):
 run('eat1_'+mode,py+[str(B/'proofs/eat1/run_eat1.py'),mode])
