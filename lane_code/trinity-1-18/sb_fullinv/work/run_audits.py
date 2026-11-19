import os, sys, subprocess, json, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
CHECK=Path('/scratch/jjyeung/orch_n30/sb_auditfix2')
source=BASE/'w21/work/build21/inputs/row_sources.json'
specs=json.loads(source.read_text())
results={}
for name in ('recovery','absolute_distance','units','coverage_distance','coverage_units'):
    cmd=[sys.executable,'-B',str(CHECK/'store_room_audit.py'),'--store',specs[name]['source']['path'],'--tree',str(BASE/'w21/work/tree_r1'),'--lists',str(CHECK/'inputs/lists'),'--out',str(ROOT/'work/audits_native'/name)]
    start=time.monotonic()
    run=subprocess.run(cmd,cwd=ROOT, text=True,capture_output=True)
    results[name]={'command':cmd,'returncode':run.returncode,'seconds':time.monotonic()-start,'stdout':run.stdout,'stderr':run.stderr}
    print(name,results[name],flush=True)
results['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,CHECK/'store_room_audit.py',Path(__file__))}
(ROOT/'work/AUDIT_RUN.json').write_text(json.dumps(results,indent=2)+'\n')
