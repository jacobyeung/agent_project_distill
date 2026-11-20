import json,sys,tarfile,os,shutil,fcntl
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write,name_guard
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID']
safe=name_guard(k)
local=r/'o';local.mkdir(parents=True,exist_ok=True)
with (local/'lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if not (local/'o.tar').is_file():
  write(local/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]),GO=False,submitted_by_build=False))
  files=[r/n for n in ('q.log','rooms.log','rooms.json','h.log','t.log','p/q/RESULT.json','p/q/host.json','p/q/f.json') if (r/n).is_file()]
  with tarfile.open(local/'o.tar.part','w:gz') as t:
   for p in files:t.add(p,arcname=safe(str(p.relative_to(r))),recursive=False)
   t.add(local/'RESULT.json',arcname='RESULT.json',recursive=False)
  os.replace(local/'o.tar.part',local/'o.tar')
try:
 out.mkdir(parents=True,exist_ok=True)
 for name in ('o.tar','RESULT.json'):
  shutil.copyfile(local/name,out/(name+'.part'))
  os.replace(out/(name+'.part'),out/name)
except OSError as error:
 with (local/'retry.log').open('a') as stream:stream.write('E'+str(error.errno)+'\n')
