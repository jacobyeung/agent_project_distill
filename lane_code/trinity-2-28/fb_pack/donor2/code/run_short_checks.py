from pathlib import Path
import subprocess,sys,os,json,hashlib,time
W=Path(__file__).resolve().parents[1];os.chdir(W);out=[]
for script,args in [('environment.py',[]),('base_negative.py',[]),('run_focused.py',['base']),('run_focused.py',['new']),('run_focused.py',['live_base']),('run_focused.py',['live'])]:
 cmd=[sys.executable,'-B','code/'+script,*args];label=script.removesuffix('.py')+('_'+args[0] if args else '')
 t=time.time()
 with (W/'out'/f'{label}.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 out.append(dict(command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 '+' '.join(cmd),returncode=r.returncode,seconds=time.time()-t))
 print(label,r.returncode,flush=True)
 inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (W/'code').glob('*.py')}
 (W/'out/SHORT_CHECK_RUNS.json').write_text(json.dumps(dict(input_sha256=inputs,runs=out),indent=2)+'\n')
 if r.returncode:sys.exit(r.returncode)
