"""Read-only local mounts avoid copying trained head checkpoints."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
data=L.parent/'work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook'
out=B/'proofs/eat1/b04';art=out/'reader/artifact';art.mkdir(parents=True,exist_ok=True)
cmd=['bwrap','--die-with-parent','--ro-bind','/','/','--dev-bind','/dev','/dev',
     '--proc','/proc','--bind',str(L),str(L),'--chdir',str(L)]
mounts=[]
for name,folder in (('scale_head','heads/scale/work/run1'),('selector_head','heads/selector/work/run_iso')):
    (art/name).mkdir(exist_ok=True)
    for suffix in ('.json','.safetensors'):
        source=data/folder/(name+suffix);target=art/name/(name+suffix)
        if not target.exists():target.write_bytes(b'')
        cmd+=['--ro-bind',str(source),str(target)]
        mounts.append(dict(source=str(source),target=str(target),sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
(out/'MOUNTS.json').write_text(json.dumps(mounts,indent=2)+'\n')
for script,args in (('b04_artifact10.py',[]),('monitor_eat10.py',['b04'])):
    with (out/(script+'.log')).open('w') as log:
        result=subprocess.run(cmd+[sys.executable,'-I','-s','-B',str(B/script),*args],stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise SystemExit(result.returncode)
