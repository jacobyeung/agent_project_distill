import json,sys,tarfile,os,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write,name_guard
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID'];out.mkdir(parents=True,exist_ok=True)
safe=name_guard(k)
files=[r/n for n in ('q.log','rooms.log','rooms.json','h.log','t.log','p/q/RESULT.json','p/q/f.json') if (r/n).is_file()]
local=r/'o';local.mkdir(parents=True,exist_ok=True)
with tarfile.open(local/'o.tar','w:gz') as t:
 for p in files:t.add(p,arcname=safe(str(p.relative_to(r))),recursive=False)
shutil.copyfile(local/'o.tar',out/'o.tar')
write(local/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]),GO=False,submitted_by_build=False))
shutil.copyfile(local/'RESULT.json',out/'RESULT.json')
