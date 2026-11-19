"""Publish the report-bearing archive only after qualification passes."""
from pathlib import Path
import json, subprocess, sys

L=Path(__file__).resolve().parents[2]
B=L/'work/build14'
def run(name,*args):
    print('Starting',name,flush=True)
    with (B/(name+'.log')).open('w') as output:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'.py')),*args],
                              stdout=output,stderr=subprocess.STDOUT)
    print(name,result.returncode,flush=True)
    if result.returncode:
        raise SystemExit('Stopped after failed check; no automatic retry: '+name)

run('check_results14','--require')
run('report14')
(B/'STATUS.md').write_text('# Build 14 status\n\nSource and CPU qualification are packaged with GO=false. Real A/C handover acceptance remains blocked by routing_opener_init (reset versus keep). The full parity sweep could not be rerun from the authorized inputs.\n\nScale binding, audited effective comparison, milestone producer/reader proofs, population/routing proofs, fresh kits, both suites, coverage and archive integrity are recorded in out/BUILD14_REPORT.md and work/build14/proofs/integrity/RESULT.json.\n')
run('delivery14')
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package14',str(L/delivery['path']))
run('storage14')
run('integrity14')
