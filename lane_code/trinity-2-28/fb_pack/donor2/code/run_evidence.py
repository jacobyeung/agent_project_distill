from pathlib import Path
import subprocess,os,sys,json,hashlib,time
W=Path(__file__).resolve().parents[1];os.chdir(W)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[]
for script,args,label in [('run_unit.py',[],'unit_final'),('k1_fixture.py',[],'k1'),('run_export_check.py',[],'export_check'),('adversarial_checks.py',[],'adversarial'),('absent_parity.py',['base'],'absent_base'),('absent_parity.py',['new'],'absent_new'),('parity_full.py',['base'],'parity_base'),('parity_full.py',['new'],'parity_new')]:
 command=[sys.executable,'-B','code/'+script,*args];t=time.time()
 with (W/'out'/f'{label}.log').open('w') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 '+' '.join(command),returncode=r.returncode,seconds=time.time()-t,log=str(W/'out'/f'{label}.log')))
 print(label,r.returncode,flush=True)
 inputs={str(p):sha(p) for p in (W/'code').glob('*.py')}
 inputs.update({str(W/'out'/f'{entry["log"].split("/")[-1]}'):sha(entry['log']) for entry in results})
 for p in (W/'work/new').rglob('*.py'):inputs[str(p)]=sha(p)
 (W/'out/EVIDENCE_RUNS.json').write_text(json.dumps(dict(input_sha256=inputs,runs=results),indent=2)+'\n')
 if r.returncode:sys.exit(r.returncode)
