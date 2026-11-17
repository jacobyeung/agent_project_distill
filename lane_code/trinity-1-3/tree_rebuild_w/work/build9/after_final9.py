"""Complete supplemental coverage, enforce the local gate, and write the review delivery."""
import json,os,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';py=[sys.executable,'-I','-s','-B']
state=json.loads((B/'FINAL_PASS.json').read_text())
assert not any(r['status']=='running' for r in state)
def run(name,command):
    row=dict(step=name,command=command,status='running',started=time.time());state.append(row)
    def save():
        (B/'FINAL_PASS.json').write_text(json.dumps(state,indent=2)+'\n')
        with (B/'STATUS.md').open('a') as f:f.write('\nFinal validation: '+name+' '+row['status']+'; `work/build9/FINAL_PASS.json`.\n')
    save()
    with (B/('final_'+name+'.log')).open('w') as f:
        result=subprocess.run(command,cwd=L,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
    row.update(returncode=result.returncode,finished=time.time(),status='complete' if result.returncode==0 else 'failed');save()
    if result.returncode<0:raise SystemExit('Process was killed; stop without retry: '+name)
    if result.returncode:raise SystemExit('Inspect failed step: '+name)
run('weighted_cpu',['bash',str(B/'RUN_TEST.sh'),str(B/'proofs/cpu_weighted'),'weighted_cpu'])
run('coverage_final',py+[str(B/'coverage_all.py')])
run('local_gate',py+[str(B/'finish_gate.py')])
run('storage_audit',py+[str(B/'storage_audit9.py')])
run('verify_delivery',py+[str(B/'verify_delivery.py')])
run('report9',py+[str(B/'report9.py')])
run('verify_report_storage',py+[str(B/'verify_delivery.py')])
run('report9_final',py+[str(B/'report9.py')])
comparison=json.loads((B/'SUITE_COMPARISON.json').read_text())
final=dict(go=False,local_gate='PASS',delivery=json.loads((B/'DELIVERY.json').read_text()),
    suite={k:comparison[k] for k in ('run','passed','preexisting','regressions','r2_failures')},
    report='out/BUILD9_REPORT.md',remaining='Production inputs, sealed-slice scene exclusions, independent review and carried acceptance blockers.')
(B/'FINAL_STATE.json').write_text(json.dumps(final,indent=2)+'\n')
print(json.dumps(final))
