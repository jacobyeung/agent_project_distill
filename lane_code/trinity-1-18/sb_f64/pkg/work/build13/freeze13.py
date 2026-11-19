from pathlib import Path
import subprocess,sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
prior=B/'retained_kits13c'
assert not prior.exists();(B/'kits').rename(prior)
for name,script,args in [('seal',L/'work/n1fix2/seal.py',[]),('kits',B/'kits13.py',[]),('final/packet',B/'packet13.py',['integrated','packet','contract'])]:
    folder=B/'proofs'/name;folder.mkdir(parents=True,exist_ok=True)
    with (folder/'console.log').open('w') as f:
        r=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],stdout=f,stderr=subprocess.STDOUT)
    print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
