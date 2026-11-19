from pathlib import Path
import hashlib, json, os, shlex, subprocess, sys, time
W=Path(__file__).resolve().parents[1];O=W/'out';PY='/scratch/jjyeung/envs/p1cpu/bin/python'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prefix=['nice','-n','10','env','OMP_NUM_THREADS=16','MKL_NUM_THREADS=16','OPENBLAS_NUM_THREADS=16',PY,'-B']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TMPDIR=str(W/'work'),XDG_CACHE_HOME=str(W/'work/cache'),HF_HOME=str(W/'work/hf'))
inputs={str(Path(__file__).resolve()):sha(__file__),str(O/'FILES_TOUCHED.json'):sha(O/'FILES_TOUCHED.json')}
for label in ('base','new','live_base','live'):
    for p in (W/'work'/label).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:inputs[str(p)]=sha(p)
for name in ('run_unit.py','run_focused.py','parity_full.py'):inputs[str(W/'code'/name)]=sha(W/'code'/name)
runs=[]
jobs=[('unit_'+t,'run_unit.py',[],{'DONOR_TREE':t}) for t in ('new','live')]
jobs += [('parity_'+t,'parity_full.py',[t],{}) for t in ('base','new','live_base','live')]
jobs += [('focused_'+t,'run_focused.py',[t],{}) for t in ('base','new','live_base','live')]
for name,script,args,extra in jobs:
    command=prefix+['code/'+script]+args
    start=time.time()
    with (O/(name+'.log')).open('w') as f:
        p=subprocess.run(command,cwd=W,env={**env,**extra},stdout=f,stderr=subprocess.STDOUT)
    row=dict(name=name,command=('env '+shlex.join([k+'='+v for k,v in extra.items()])+' ' if extra else '')+shlex.join(command),returncode=p.returncode,seconds=time.time()-start,log_sha256=sha(O/(name+'.log')))
    runs.append(row)
    (O/'RUNS.json').write_text(json.dumps(dict(input_sha256=inputs,runs=runs,command=shlex.join(prefix+['code/validate.py'])),indent=2)+'\n')
    (W/'STATUS.md').write_text('Validation completed '+name+' with exit code '+str(p.returncode)+'. Commands and input hashes are recorded in out/RUNS.json. The code delta changes only the runtime test; the reader recipe includes strict visual restoration and freezing before attachment. Remaining checks continue sequentially on CPU.\n')
    print(row,flush=True)
    if p.returncode != 0:
        raise SystemExit('Validation command failed; inspect the retained log before rerunning.')
assert all(sha(p)==h for p,h in inputs.items()),'Validation changed a source input'
print('All validation commands completed; focused results require comparison.',flush=True)
