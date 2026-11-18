from pathlib import Path
import json,os,sys
B=Path('/scratch/jjyeung/orch_n30/review_tree11/work/eat/b');T=Path('/scratch/jjyeung/orch_n30/review_tree11/pkg/work/tree_r1')
sys.path[:0]=[str(B),str(T)]
out=Path('/scratch/jjyeung/orch_n30/review_tree11/work/eat/c8r');out.mkdir(parents=True,exist_ok=True)
os.makedirs('/scratch/jjyeung/orch_n30/review_tree11/work/tmp/eat',exist_ok=True);os.environ['EAT1_TMP']='/scratch/jjyeung/orch_n30/review_tree11/work/tmp/eat'
from eat1 import run
from eat1.adapters import c8r_tiny as adapter
adapter.write_items(out/'items.jsonl',out/'frames')
kwargs=dict(tree=str(T),workdir=str(out/'reader'))
sys.exit(run.main(['--reader','eat1.adapters.c8r_tiny:make_reader','--reader-kwargs',json.dumps(kwargs),'--items',str(out/'items.jsonl'),
    '--out',str(out/'run'),'--code-root',str(T),'--pythonpath',str(B),'--perturb','--sandbox']))
