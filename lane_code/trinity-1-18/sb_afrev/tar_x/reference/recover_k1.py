import hashlib,json,tarfile
from pathlib import Path
base=Path(__file__).resolve().parent.parent
p=Path('/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar');h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
member='manifests/TEACHER_K1.json'
with tarfile.open(p) as t:b=t.extractfile(member).read()
sha=hashlib.sha256(b).hexdigest();assert sha.startswith('4d4736cf'),sha
out=base/'work/TEACHER_K1.raw';out.write_bytes(b)
res=dict(command='python work/recover_k1.py',inputs={str(p):dict(sha256=h.hexdigest(),bytes=p.stat().st_size),str(Path(__file__).resolve()):dict(sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())},member=member,source_archive=str(p),recovered=dict(path=str(out),sha256=sha,bytes=len(b)))
(base/'work/K1_RECOVERY.json').write_text(json.dumps(res,indent=2)+'\n')
d=json.loads(b);print('sha',sha,'keys',list(d)[:30]);print(str(d)[:3500])
