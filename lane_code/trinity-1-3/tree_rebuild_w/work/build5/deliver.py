"""Seal, stage, test and publish only after the qualification gates pass."""
import json
from pathlib import Path
import subprocess
import sys

L=Path(__file__).resolve().parents[2]
status=L/'work/build5/STATUS.md'
def run(name):
    status.write_text('# Build 5 status\n\nCurrent step: `work/build5/'+name+'`.\n\n'
        'The current R2/shared proof passed every test (`work/build5/proofs/r2_current/results.json`). '
        'Current-source coverage is recorded in `work/build5/CHANGED_COVERAGE.json`. '
        'Final qualification is pending until the package suite and identity audit complete. '
        'Both kit authorizations remain closed. No remote or GPU work is authorized.\n')
    print(json.dumps(dict(step=name,status='running')),flush=True)
    result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5'/name)])
    if result.returncode:
        with status.open('a') as stream:
            stream.write('\nThis step returned an error. Inspect its receipts before continuing.\n')
        raise SystemExit(result.returncode)
    print(json.dumps(dict(step=name,status='complete')),flush=True)

coverage=json.loads((L/'work/build5/CHANGED_COVERAGE.json').read_text())
assert coverage['classes'].get('CPU-reachable unresolved',0)==0
(L/'work/build5/NEXT.md').write_text('# Remaining build work\n\n'
    'The active delivery driver is `work/build5/deliver.py`. Read `STATUS.md` and its tool output for the current step. '
    'Keep all tests serial and leave source, fixtures and packaged harness unchanged while it runs. '
    'The driver seals source, stages both closed kits, packages them, runs every suite group and same-case base replay, '
    'then checks coverage and identities before writing final documents. An error stops the driver; inspect its receipts '
    'and fix the cause before continuing from that step. No process was killed.\n\n'
    'Use only the prescribed RUN.sh environment and login:false. No Git, SSH, GPU, network, agents, real frame/checkpoint copies '
    'or full-store materialization. Actual frame-host bytes remain unqualified; see out/FRAME_HOST_JOB.md.\n')
for name in ('seal.py','build_kits.py','make_delivery.py','run_delivery.py','compare.py',
             'measure_current.py','fixes.py','static_audit.py','final_audit.py',
             'refresh_card.py','report.py','finish_docs.py'):
    run(name)
# Include the newly written report and design record in the storage census.
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/static_audit.py')],check=True)
