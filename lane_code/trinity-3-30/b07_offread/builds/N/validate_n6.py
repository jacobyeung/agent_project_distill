"""CPU-only final gates with fresh RAM outputs and bounded local fixtures."""
from pathlib import Path
import json,os,subprocess,sys
N=Path(__file__).resolve().parent;R=N.parent/'R'
RAM=Path(json.loads((N/'out/N6_WORKSPACE.json').read_text())['ram'])
ENV=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
kind=sys.argv[1];label=sys.argv[2]
records=[]
def run(name,args,cwd=N,env=ENV):
    with (RAM/(name+'.log')).open('x') as log:
        p=subprocess.run([PY,'-B',*map(str,args)],cwd=cwd,env=env,stdout=log,stderr=log)
    row=dict(name=name,returncode=p.returncode);records.append(row)
    print(json.dumps(row),flush=True)
    return row
if kind=='n_suite':
    run(label,['-m','pytest','-p','no:cacheprovider','kit/tests','--basetemp='+str(RAM/label),'-q'])
elif kind=='r_suite':
    gate=N/'work'/('nonshm_'+label);gate.mkdir();fd=os.open(gate,os.O_RDONLY|os.O_DIRECTORY)
    env=dict(ENV,ROFF2_ROOT=f'/proc/{os.getpid()}/fd/{fd}')
    run(label,['-m','pytest','-p','no:cacheprovider','tests','--basetemp='+str(RAM/label),'-q'],R,env)
elif kind=='n_fixtures':
    for i,(benchmark,reader) in enumerate((b,r) for b in ('revsi999t32','vsibench5130') for r in ('harness','e2e')):
        name=label+str(i)
        row=run(name,['-m','offnative.census',RAM/name,reader,RAM/(name+'.json'),benchmark])
        row.update(benchmark=benchmark,reader=reader)
elif kind=='r_fixtures':
    for i,(key,done) in enumerate((k,d) for k in ('vsi','revsi') for d in (False,True)):
        name=label+str(i)
        row=run(name,['tests/rehearse.py',key,RAM/name,*(['--done'] if done else [])],R)
        row.update(benchmark=key,done=done)
else:raise ValueError(kind)
(RAM/(label+'_index.json')).write_text(json.dumps(records,indent=2)+'\n')
