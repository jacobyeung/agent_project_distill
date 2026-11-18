"""Complete qualification and bind final harness bytes without rerunning unchanged groups."""
from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
py=[sys.executable,'-I','-s','-B']
def run(name,args):
    (B/'STATUS.md').write_text('Build n1fix2: '+name+' is running. Source and CPU finding proofs are complete; final delivery checks are pending. GO=false.\n')
    with (B/(name+'.log')).open('w') as log:code=subprocess.run(args,cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    if code<0:raise SystemExit('A process was killed; stop without retry: '+name)
    if code:raise SystemExit(name+' failed: '+str(code))
    print(name+': complete',flush=True)
assert (B/'proofs/package/ARCHIVE.json').is_file(),'The initial frozen suite must finish first'
run('comparison',py+[str(B/'compare.py')])
run('coverage',py+[str(B/'coverage_current.py')])
assert not json.loads((B/'GAPS.json').read_text())
comparison=json.loads((B/'SUITE_COMPARISON.json').read_text())
assert comparison['r2_failures']==0
assert all(r['preexisting'] or 'BF16' in r['cause'] for r in comparison['failures'])
run('delivery_final',py+[str(B/'make_delivery.py')])
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package_final',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])])
run('integrity_final',py+[str(B/'final_checks.py')])
run('report',py+[str(B/'write_report_final.py')])
