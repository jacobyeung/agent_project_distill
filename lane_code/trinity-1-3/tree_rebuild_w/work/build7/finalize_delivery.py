"""Verify the frozen artifacts and publish the final, explicitly blocked status."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

L=Path(__file__).resolve().parents[2]
B=L/'work/build7'
state=json.loads((B/'FINAL_PASS.json').read_text())
if state[-1]['step']!='report' or state[-1]['status']!='complete':
    raise SystemExit('The final validation driver has not completed its report step')
for name in ('verify_delivery','report'):
    subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'.py'))],check=True)
def read(name):return json.loads((B/name).read_text())
comparison=read('SUITE_COMPARISON.json')
coverage=read('CHANGED_COVERAGE.json')
focused=read('proofs/final_targeted/results.json')
packet=read('proofs/packet/results.json')
verification=read('FINAL_VERIFICATION.json')
record=dict(status='BLOCKED',go=False,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            tree_seal=verification['tree_seal'],
            packet=dict(run=len(packet),passed=sum(v['outcome']=='passed' for v in packet.values())),
            package={k:comparison[k] for k in ('run','passed','preexisting','regressions','r2_failures','skipped')},
            supplemental=dict(run=focused['tests'],passed=len(focused['passed']),
                              errors=len(focused['errors']),failures=len(focused['failures'])),
            coverage=coverage['classes'],report='out/BUILD7_REPORT.md')
(B/'FINAL_STATE.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['# Build 7 status','',
       'The final validation and artifact verification are complete. Acceptance remains BLOCKED; both kits remain GO=false. No launch or remote call was made.','',
       'Packet results: '+json.dumps(record['packet'])+' (`work/build7/proofs/packet/results.json`).','',
       'Package comparison: '+json.dumps(record['package'])+' (`work/build7/SUITE_COMPARISON.json`).','',
       'Supplemental results: '+json.dumps(record['supplemental'])+' (`work/build7/proofs/final_targeted/results.json`).','',
       'Changed-statement classes: '+json.dumps(record['coverage'])+' (`work/build7/CHANGED_COVERAGE.json`).','',
       'The final tree, archive and kit hashes passed verification (`work/build7/FINAL_VERIFICATION.json`).','',
       'Open inputs and implementation gaps are itemized in `out/BUILD7_REPORT.md`. The report records every unresolved test, coverage, long-frame, response-forward, portrait, cache-precision and distributed-stop qualification.','',
       'Build-6 regressions and gaps have individual dispositions in `work/build7/BUILD6_DISPOSITION.json`. EAT reports remain in `work/build7/proofs/eat1/`.','',
       'The prelaunch card is `out/PRELAUNCH_CARD.md`; the design record includes its Build 7 section. No independent review was performed because this build forbids another agent.','']
(B/'STATUS.md').write_text('\n'.join(lines))
print(json.dumps(record))
