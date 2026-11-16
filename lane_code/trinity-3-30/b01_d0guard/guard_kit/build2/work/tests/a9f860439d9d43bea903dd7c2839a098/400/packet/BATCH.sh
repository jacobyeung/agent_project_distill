#!/bin/bash
set -euo pipefail
umask 077
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
unset PYTHONPATH
exec /usr/bin/python3 -I -s -B - <<'G2_PY'
PAYLOAD='/project/community/jjyeung/okh7/8c9d2e74/bbbbbbbbbbbbbbbb/p.tar'
EXPECTED='751b1b892c286fdadb65d3b8e299556157ec07c0c274e711ce71c2fd8164bf64'
TOKEN='bbbbbbbbbbbbbbbb'
import hashlib,io,json,os,pathlib,tarfile
job=os.environ.get('SLURM_JOB_ID','')
if not job.isdigit():raise ValueError('Assigned job required')
source=pathlib.Path(PAYLOAD)
if source.is_symlink() or not source.is_file() or source.stat().st_size>33554432:raise ValueError('Payload source differs')
raw=source.read_bytes()
if len(raw)>33554432 or hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Payload differs')
root=pathlib.Path('/tmp')/('g2_'+job+'_'+TOKEN)
root.mkdir(mode=0o700)
p=root/'payload';p.mkdir();seen=set();total=0
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
 for m in tar:
  n=pathlib.PurePosixPath(m.name);total+=m.size
  if not m.isfile() or n.is_absolute() or '..' in n.parts or str(n) in seen or total>33554432:raise ValueError('Unsafe payload')
  seen.add(str(n));target=p/str(n);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as out:out.write(tar.extractfile(m).read())
  target.chmod(m.mode&0o755)
c=json.loads((p/'CONFIG.json').read_text())['closure_object']
source=pathlib.Path(c['path'])
if source.is_symlink() or not source.is_file() or source.stat().st_size!=c['bytes'] or c['bytes']>67108864:raise ValueError('Closure object differs')
h=hashlib.sha256()
with source.open('rb') as inp,(p/'metadata.tar').open('xb') as out:
 for block in iter(lambda:inp.read(1048576),b''):
  h.update(block);out.write(block)
if h.hexdigest()!=c['sha256']:raise ValueError('Closure object digest differs')
os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-s','-B',str(p/'guard_kit/worker.py'),'--root',str(root),'--payload',str(p)])
G2_PY
