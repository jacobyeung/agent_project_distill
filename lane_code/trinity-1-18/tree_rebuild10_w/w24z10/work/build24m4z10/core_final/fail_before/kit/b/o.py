import json,sys,tarfile,os,shutil,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write,name_guard
from pc import CAP,LOG_CAP
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID']
safe=name_guard(k)
local=r/'o';local.mkdir(parents=True,exist_ok=True)
# Freeze one bounded archive per allocation; retries must use identical bytes.
if not (local/'o.tar').exists():
 write(local/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]),GO=False,submitted_by_build=False))
 logs=[r/n for n in ('q.log','rooms.log','h.log','t.log') if (r/n).is_file() and not (r/n).is_symlink()]
 metadata=[local/'RESULT.json']+[r/n for n in ('rooms.json','p/q/RESULT.json','p/q/host.json','p/q/f.json') if (r/n).is_file() and not (r/n).is_symlink()]
 pending=[];remaining=LOG_CAP
 for i,p in enumerate(logs):
  allowance=remaining//(len(logs)-i)
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-allowance));raw=f.read(allowance)
  pending.append((safe(str(p.relative_to(r))),raw));remaining-=len(raw)
 remaining=CAP-LOG_CAP-1_000_000
 for p in metadata:
  if p.stat().st_size>remaining:continue
  with p.open('rb') as f:raw=f.read(remaining+1)
  if len(raw)>remaining:continue
  pending.append(('RESULT.json' if p==local/'RESULT.json' else safe(str(p.relative_to(r))),raw));remaining-=len(raw)
 partial=local/'o.tar.part'
 with tarfile.open(partial,'w:gz',format=tarfile.USTAR_FORMAT) as t:
  for name,raw in pending:
   m=tarfile.TarInfo(name);m.size=len(raw);m.mode=0o600;t.addfile(m,io.BytesIO(raw))
 if partial.stat().st_size>CAP:raise ValueError('E103')
 os.replace(partial,local/'o.tar')
if '--local' not in sys.argv:
 try:
  out.mkdir(parents=True,exist_ok=True)
  for name in ('o.tar','RESULT.json'):
   shutil.copyfile(local/name,out/(name+'.part'))
   os.replace(out/(name+'.part'),out/name)
 except OSError as error:
  with (local/'retry.log').open('a') as stream:stream.write('E'+str(error.errno)+'\n')
