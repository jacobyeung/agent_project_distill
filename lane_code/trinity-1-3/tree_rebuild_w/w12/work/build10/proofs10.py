from pathlib import Path
import json,os,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
commands=[('numeric_parity','proof_parity_numeric10.py',[]),('forward','proof_forward9.py',[]),
          ('gf1','run_eat10.py',['gf1']),('c8r','run_eat10.py',['c8r'])]
rows=[]
for name,script,args in commands:
    tmp_before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    if tmp_before>200_000_000:raise RuntimeError('temporary storage cap')
    out=L/'work/build12/proofs'/name;out.mkdir(parents=True,exist_ok=True)
    print('Starting '+name,flush=True)
    with (out/'console.log').open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/script),*args],cwd=L,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode<0:raise RuntimeError('A process was killed; no retry authorized')
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    rows.append(dict(name=name,returncode=result.returncode,tmp_before=tmp_before,tmp_after=after))
    (B/'PROOF_RUNS.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (B/'STATUS.md').open('a') as f:f.write(f'\n{name}: return code {result.returncode}; evidence proofs/{name}/console.log.\n')
    print(json.dumps(rows[-1]),flush=True)
    if after>200_000_000:raise RuntimeError('temporary storage cap')
