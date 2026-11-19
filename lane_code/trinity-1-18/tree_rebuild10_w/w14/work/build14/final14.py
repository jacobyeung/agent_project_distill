"""Seal, stage and qualify one final source with bounded retained outputs."""
from pathlib import Path
import subprocess,sys,json,time,os
L=Path(__file__).resolve().parents[2];B=L/'work/build14';runs=[]
resume=sys.argv[1] if len(sys.argv)>1 else None
if resume:
    old=json.loads((B/'FINAL_RUNS.json').read_text())
    for item in old:
        if item['name']==resume:break
        assert item['returncode']==0
        runs.append(item)
def run(name,script,*args):
    global resume
    if resume:
        if resume!=name:return
        resume=None
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    start=time.time();print('Starting',name,flush=True)
    env=dict(os.environ,B14_PROOF=name)
    with (out/'console.log').open('w') as f:r=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],env=env,stdout=f,stderr=subprocess.STDOUT)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    runs.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'FINAL_RUNS.json').write_text(json.dumps(runs,indent=2));print(name,r.returncode,flush=True)
    (B/'STATUS.md').write_text('# Build 14 status\n\nGO=false. A/C admission remains blocked by the compared routing opener policy. Last final check: '+name+', exit '+str(r.returncode)+'. See FINAL_RUNS.json.\n')
    if r.returncode:raise SystemExit('Stopped after failed check; no automatic retry: '+name)
run('final_focused',B/'test14.py','tests.test_r1_build14','tests.test_r2_build_n1','tests.test_r2_n1fix','tests.test_r2_n1fix3','tests.test_r2_build12','tests.test_r1_build13')
run('real',B/'real14.py')
run('seal',L/'work/n1fix2/seal.py')
run('kits',B/'kits14.py')
run('packet_inputs',B/'packet_inputs14.py')
run('final/packet',B/'packet14.py','integrated','packet','contract')
run('delivery',B/'delivery14.py')
delivery=json.loads((B/'DELIVERY.json').read_text())
run('final/package',B/'package14.py',str(L/delivery['path']))
run('comparison',B/'compare14.py')
run('coverage',B/'coverage14.py')
run('storage',B/'storage14.py')
