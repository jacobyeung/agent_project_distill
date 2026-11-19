"""Run available retained CPU proofs serially and keep missing-input evidence separate."""
from pathlib import Path
import subprocess,sys,json,os,time,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
def size():return sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
records=json.loads((B/'PROOF_RUNS.json').read_text()) if (B/'PROOF_RUNS.json').exists() else []
for name in sys.argv[1:] or ('opener','text','row_delta','preservation','confusables','packet_inputs','packet'):
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=size();assert before<=200_000_000
    script=B/(name+'15.py');args=['integrated','packet','contract'] if name=='packet' else []
    start=time.time()
    (B/'STATUS.md').write_text('# Build 15 status\n\nA, C and Cprime admit. Running '+name+'; missing external inputs are recorded separately. GO=false.\n')
    with (out/'console.log').open('w') as log:
        r=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],stdout=log,stderr=subprocess.STDOUT)
    after=size();assert after<=200_000_000
    records.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after))
    (B/'PROOF_RUNS.json').write_text(json.dumps(records,indent=2))
    print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit('Proof failed; inspect before further work: '+name)
