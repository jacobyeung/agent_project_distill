"""Run the shipped diagnostic once against the generated fixture database."""
from pathlib import Path
import os,sys,json,runpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k6 import R
selection=R/'p2/q/selection'
target=R/'dbb/p/q/selection';target.mkdir(parents=True)
databases=list(selection.glob('*.sqlite'))
assert len(databases)==1,databases
source=databases[0];os.link(source,target/source.name)
import hashlib
digest=hashlib.sha256(source.read_bytes()).hexdigest()
os.environ['DBB_TARGET']=digest
script=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/out/dbb2.py')
sys.argv=[str(script),str(R/'dbb'),str(R/'dbb')]
runpy.run_path(str(script),run_name='__main__')
(R/'DBB_STEP.json').write_text(json.dumps(dict(helper=str(script),sha256=hashlib.sha256(script.read_bytes()).hexdigest(),fixture_target=digest,evidence=str(R/'dbb/db_bytes.json')),indent=2)+'\n')
