import json,sys,tarfile,os,shutil,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write,name_guard,screen
from pc import CAP,LOG_CAP,put,masked
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID']
safe=name_guard(k)
local=r/'o';local.mkdir(parents=True,exist_ok=True)
# The launch records real return codes before the shell finalizer rebuilds the archive.
frozen=(r/'live_spool/state/o_frozen.json').exists()
if not frozen and ('--final' not in sys.argv or not (local/'RESULT.json').exists()):
 put(local/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]) if '--final' not in sys.argv else None,GO=False,submitted_by_build=False))
if not frozen and ('--final' in sys.argv or not (local/'o.tar').exists()):
 logs=[r/n for n in ('q.log','rooms.log','h.log','t.log','j2.log','j2.err') if (r/n).is_file() and not (r/n).is_symlink()]
 if (r/'live_spool/upload.log').is_file():logs.append(r/'live_spool/upload.log')
 metadata=[local/'RESULT.json']+[r/n for n in ('rooms.json','p/q/RESULT.json','p/q/host.json','p/q/f.json') if (r/n).is_file() and not (r/n).is_symlink()]
 metadata += [p for p in (r/'live_spool/state').glob('UPLOAD_*.json') if p.is_file()]
 pending=[];remaining=LOG_CAP
 for i,p in enumerate(logs):
  allowance=remaining//(len(logs)-i)
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-allowance));raw=f.read(allowance)
  raw=screen(masked(raw.decode('utf-8','replace')),load(k/'k/g.json'),load(k/'b/wh.json')).encode()[-allowance:]
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
 with partial.open('rb') as f:os.fsync(f.fileno())
 os.replace(partial,local/'o.tar')
if '--local' not in sys.argv:
 try:
  out.mkdir(parents=True,exist_ok=True)
  for name in ('o.tar','RESULT.json'):
   shutil.copyfile(local/name,out/(name+'.part'))
   os.replace(out/(name+'.part'),out/name)
 except OSError as error:
  with (local/'retry.log').open('a') as stream:stream.write('E'+str(error.errno)+'\n')
