"""Final source freeze, fresh kits, packet and frozen suites."""
from pathlib import Path
import json,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/build13';runs=[]
prior=B/'retained_kits13b';assert not prior.exists();(B/'kits').rename(prior)
def run(name,script,*args):
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    start=time.time();print('Starting',name,flush=True)
    with (out/'console.log').open('w') as f:r=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],stdout=f,stderr=subprocess.STDOUT)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    runs.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'FINAL_RUNS.json').write_text(json.dumps(runs,indent=2));print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit('Stopped after failed check; no automatic retry: '+name)
run('seal',L/'work/n1fix2/seal.py')
run('kits',B/'kits13.py')
run('final/packet',B/'packet13.py','integrated','packet','contract')
run('delivery',B/'delivery13.py')
delivery=json.loads((B/'DELIVERY.json').read_text())
run('final/package',B/'package13.py',str(L/delivery['path']))
run('comparison',B/'compare13.py')
run('mutations',B/'mutations13.py')
run('edges',B/'edges13.py')
run('coverage',B/'coverage13.py')
run('storage',B/'storage13.py')
