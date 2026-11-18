from pathlib import Path
import hashlib,json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
name=sys.argv[1];out=L/'work/build12/proofs/eat1'/name;out.mkdir(parents=True,exist_ok=True)
os.environ['EAT1_TMP']=str(L/'work/tmp')
from eat1 import run
if name=='b04':
    sys.path.insert(0,str(B/'b04_stage'))
    from eat1_adapter import b04_tiny as adapter
    spec='eat1_adapter.b04_tiny:make_reader'
    kwargs=dict(workdir=str(out/'reader'))
    extras=['--pythonpath',str(B/'b04_stage'),'--code-root',str(B/'b04_stage')]
else:
    from importlib import import_module
    adapter=import_module('eat1.adapters.'+name+'_tiny')
    spec='eat1.adapters.'+name+'_tiny:make_reader'
    kwargs=dict(tree=str(T),workdir=str(out/'reader'))
    extras=[]
adapter.write_items(out/'items.jsonl',out/'frames')
result=run.main(['--reader',spec,'--reader-kwargs',json.dumps(kwargs),'--items',str(out/'items.jsonl'),
    '--out',str(out/'run'),'--code-root',str(T),'--pythonpath',str(B),'--perturb','--sandbox',*extras])
sys.exit(result)
