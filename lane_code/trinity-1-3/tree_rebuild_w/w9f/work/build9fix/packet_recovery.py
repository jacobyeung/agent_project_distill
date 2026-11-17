"""One diagnosed harness repair before accepting any frozen package group."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix';P=B/'proofs/packet'
prior=json.loads((P/'results.json').read_text())
failed={k:v for k,v in prior.items() if v.get('outcome')!='passed'}
if not failed:raise SystemExit(0)
if (B/'PACKET_RECOVERY.json').exists():raise SystemExit('Packet recovery already attempted; inspect its result before another action')
(P/'INITIAL_RESULTS.json').write_text(json.dumps(prior,indent=2)+'\n')
state=dict(reason='Install missing local input references and use a fresh per-run pytest directory; retained PID-named directories can collide across sandbox process namespaces.',
 initial_failed=len(failed),initial_source='work/build9fix/proofs/packet/INITIAL_RESULTS.json',steps=[])
def save():(B/'PACKET_RECOVERY.json').write_text(json.dumps(state,indent=2)+'\n')
def run(name,command):
 record=dict(name=name,started=time.time(),status='running');state['steps'].append(record);save()
 with (B/('recovery_'+name+'.log')).open('w') as log:
  value=subprocess.run(command,cwd=L,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
 record.update(code=value.returncode,finished=time.time(),status='complete' if value.returncode==0 else 'failed');save()
 if value.returncode<0:raise RuntimeError('Process was killed; stop without retry')
 if value.returncode:raise SystemExit('Recovery step failed: '+name)
py=[sys.executable,'-I','-s','-B']
run('packet',['bash',str(B/'PACKET_TEST.sh')])
run('delivery',py+[str(B/'make_delivery.py')])
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])])
with (B/'STATUS.md').open('a') as f:f.write('\nPacket input references and fresh pytest workspace are installed. The packet and frozen package suites completed; receipts are in proofs/packet and proofs/package. The recovery sequence is recorded in PACKET_RECOVERY.json.\n')
