from pathlib import Path
import subprocess,sys,json,time
L=Path(__file__).resolve().parents[2];B=L/'work/build13';runs=[]
for name,args in [('composition',['recompose13.py']),('census',['census13.py','--resume']),('tests',['test13.py'])]:
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    start=time.time()
    with (out/'console.log').open('w') as f:r=subprocess.run([sys.executable,'-I','-s','-B',str(B/args[0]),*args[1:]],stdout=f,stderr=subprocess.STDOUT)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    runs.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'ACCEPT_RUNS.json').write_text(json.dumps(runs,indent=2))
    print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit('Proof failed; no automatic retry: '+name)
