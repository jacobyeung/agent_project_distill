"""Freeze one source snapshot and run the packet and package suites sequentially."""
from pathlib import Path
import json,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';steps=[]
def run(name,args):
    row=dict(step=name,status='running',command=[str(a) for a in args]);steps.append(row)
    (B/'QUALIFICATION9.json').write_text(json.dumps(steps,indent=2)+'\n')
    (B/'STATUS.md').write_text('# Build 9fix status\n\nFinal qualification is running: '+name+'. GO=false. See QUALIFICATION9.json.\n\nF1–F5 implementations and focused proofs are complete. The F1 original units intake count differs from the prompt; the existing exclusions are unchanged. F6 list/division and bounded native producer checks pass; full VQA census remains unrun under the heavy-IO approval rule.\n')
    print('Starting '+name,flush=True)
    code=subprocess.run([str(a) for a in args],cwd=L).returncode
    row.update(status='complete' if code==0 else 'failed',returncode=code)
    (B/'QUALIFICATION9.json').write_text(json.dumps(steps,indent=2)+'\n')
    if code<0:raise SystemExit('A process was killed. Stop; no retry authorized.')
    if code:raise SystemExit(code)
py=[sys.executable,'-I','-s','-B']
run('seal',py+[B/'seal.py'])
target=B/'kits';retained=B/'proofs/kits/pre_native_source'
assert not retained.exists();target.rename(retained)
run('kits',py+[B/'stage9.py'])
run('packet',['bash',B/'PACKET_TEST.sh'])
run('delivery',py+[B/'make_delivery.py'])
delivery=json.loads((B/'DELIVERY.json').read_text())
run('frozen_package',['bash',B/'PACKAGE_TEST.sh',L/delivery['path']])
print('Frozen suite finished',flush=True)
