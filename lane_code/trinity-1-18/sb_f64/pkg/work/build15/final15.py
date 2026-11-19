"""Finalize evidence, package the verified source and stream-check its delivery."""
from pathlib import Path
import json,sys,subprocess,time
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
assert json.loads((B/'SUITE_RUNS.json').read_text())['r2']['returncode']==0
for p in B.glob('*.py'):compile(p.read_text(),str(p),'exec')
records=[]
for name in ('preserve','delta_coverage','coverage','storage','report','delivery','integrity'):
    p=B/(name+'15.py');out=B/'proofs'/('final_'+name);out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    start=time.time()
    with (out/'console.log').open('w') as log:
        r=subprocess.run([sys.executable,'-I','-s','-B',str(p)],stdout=log,stderr=subprocess.STDOUT)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    records.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'FINAL_RUNS.json').write_text(json.dumps(records,indent=2));print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit('Final check failed; inspect before continuing: '+name)
