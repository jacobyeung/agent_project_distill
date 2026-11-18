"""Qualify the final sealed source and then authenticate the report-bearing archive."""
from pathlib import Path
import subprocess,sys,json,time
L=Path(__file__).resolve().parents[2];B=L/'work/build13';runs=[]
def run(name,script,*args):
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    print('Starting',name,flush=True);start=time.time()
    with (out/'console.log').open('w') as f:
        r=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],stdout=f,stderr=subprocess.STDOUT)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    runs.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'FINAL_RUNS.json').write_text(json.dumps(runs,indent=2));print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit('Stopped after failed check; no automatic retry: '+name)
if '--resume' not in sys.argv:
    prior=B/'retained_kits13d';assert not prior.exists();(B/'kits').rename(prior)
    run('seal',L/'work/n1fix2/seal.py')
    run('kits',B/'kits13.py')
    run('final/packet',B/'packet13.py','integrated','packet','contract')
    run('preservation',B/'preserve13.py')
run('report',B/'report13.py')
run('delivery',B/'delivery13.py')
delivery=json.loads((B/'DELIVERY.json').read_text())
run('final/package',B/'package13.py',str(L/delivery['path']))
run('comparison',B/'compare13.py')
run('coverage',B/'coverage13.py')
coverage=json.loads((B/'CHANGED_COVERAGE.json').read_text())
assert coverage['classes'].get('CPU-reachable unresolved',0)==0
comparison=json.loads((B/'SUITE_COMPARISON.json').read_text())
assert comparison['r2_failures']==0
assert all('test_parity_cached_vs_online' in r['test'] for r in comparison['failures'] if not r['preexisting'])
run('report',B/'report13.py')
run('delivery',B/'delivery13.py')
delivery=json.loads((B/'DELIVERY.json').read_text())
run('final/package',B/'package13.py',str(L/delivery['path']))
run('storage',B/'storage13.py')
run('integrity',B/'integrity13.py')
