"""Run release CPU gates with synthetic secrets and fresh scratch destinations."""
from pathlib import Path
import json,os,secrets,subprocess,sys
N=Path(__file__).resolve().parent;R=N.parent/'R'
RAM=Path(json.loads((N/'out/N7_WORKSPACE.json').read_text())['ram'])
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',A0_BUILD_SECRET_FILE=str(RAM/'fixture_secret'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
kind=sys.argv[1];label=sys.argv[2];rows=[]
def run(name,args,cwd=N,env=ENV):
    log=RAM/(name+'.log')
    with log.open('x') as f:p=subprocess.run([PY,'-B',*map(str,args)],cwd=cwd,env=env,stdout=f,stderr=f)
    row=dict(name=name,returncode=p.returncode,log=str(log));rows.append(row);print(json.dumps(row),flush=True)
    return row
if kind in ('n_suite','r_suite'):
    root='/tmp/a_900000_'+secrets.token_hex(6)
    env=dict(ENV,ROFF2_ROOT=root)
    run(label,['-m','pytest','-p','no:cacheprovider','kit/tests' if kind=='n_suite' else 'tests','--basetemp='+str(RAM/label),'-q'],N if kind=='n_suite' else R,env)
elif kind=='n_fixtures':
    for i,(b,r) in enumerate((b,r) for b in ('revsi999t32','vsibench5130') for r in ('harness','e2e')):
        run(label+str(i),['-m','offnative.census',RAM/(label+str(i)),r,RAM/(label+str(i)+'.json'),b])
elif kind=='r_fixtures':
    for i,(k,d) in enumerate((k,d) for k in ('vsi','revsi') for d in (False,True)):
        run(label+str(i),['tests/rehearse.py',k,RAM/(label+str(i)),*(['--done'] if d else [])],R)
elif kind in ('n_prod','r_prod'):
    root='/tmp/a_900000_'+secrets.token_hex(6)
    env=dict(ENV,A0_FIXTURE_RAM=str(RAM/label))
    if kind=='n_prod':row=run(label,['rehearse_prodroot_n7.py',root],env=env)
    else:row=run(label,['tests/rehearse.py','vsi',root,'--nonshm'],R,env)
    row['root']=root
    row['root_bytes']=sum(p.lstat().st_size for p in Path(root).rglob('*') if p.is_file() or p.is_symlink())
    assert row['root_bytes']<20_000_000,row
else:raise ValueError(kind)
(RAM/(label+'_index.json')).write_text(json.dumps(rows,indent=2)+'\n')
