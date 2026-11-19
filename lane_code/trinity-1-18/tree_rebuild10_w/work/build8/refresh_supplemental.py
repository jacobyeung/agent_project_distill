"""Preserve prior fixture products within the proof folder, then rerun unchanged checks."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';P=B/'proofs/final_targeted'
state=json.loads((B/'FINAL_PASS.json').read_text())
if any(r['status']=='running' for r in state):raise SystemExit('Wait for active validation')
prior=P/'prior_fixture_products'
if prior.exists():raise SystemExit('Fixture preservation already performed; inspect receipts')
prior.mkdir()
retained=[]
for name in ('faithful','stop_fallback'):
 path=P/name
 if path.exists():path.rename(prior/name);retained.append(name)
(prior/'results.json').write_bytes((P/'results.json').read_bytes())
repair=dict(retained=retained,storage_scope='All prior and refreshed products remain inside proofs/final_targeted.',
 reason='Native exclusive writers refused diagnostic-run products; only fixture directories moved. Assertions and all source bytes remain unchanged.')
(B/'SUPPLEMENTAL_REPAIR.json').write_text(json.dumps(repair,indent=2)+'\n')
record=dict(step='supplemental',status='running',started=time.time(),
 command=[sys.executable,'-I','-s','-B',str(B/'targeted.py')],
 repair='work/build8/SUPPLEMENTAL_REPAIR.json')
state.append(record);(B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
result=subprocess.run(record['command'],cwd=L,env=os.environ)
record.update(status='complete' if result.returncode==0 else 'failed',returncode=result.returncode,finished=time.time())
(B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
if result.returncode<0:raise SystemExit('Supplemental proof was killed; stop without retry')
if result.returncode:raise SystemExit('Supplemental proof failed; inspect targeted.log')
subprocess.run([sys.executable,'-I','-s','-B',str(B/'coverage_all.py')],cwd=L,check=True)
