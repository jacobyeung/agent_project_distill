from pathlib import Path
import hashlib,json,os,tarfile
J=Path(__file__).resolve().parent.parent
rows=json.loads((J/'out/UPLOADS_24M4Z9_E3.json').read_text())
for row in rows:
 p=J/'out/e3'/row['destination'].split('/')[-1]
 assert p.stat().st_size==row['bytes']<5_000_000
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
assert len((J/'out/BUILD24M4Z9_REPORT.md').read_text().splitlines())<10
assert not Path('/project').exists()
tmp=J/'package.tmp'
assert not tmp.exists()
with tarfile.open(tmp,'w',format=tarfile.PAX_FORMAT) as t:
 for name in ('out','work'):t.add(J/name,arcname=name)
h=hashlib.sha256()
with tmp.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''):h.update(b)
digest=h.hexdigest();name='tree_rebuild_b24m4z9_'+digest[:8]+'.tar'
dest=J/'out'/name
assert not dest.exists()
os.rename(tmp,dest)
with tarfile.open(dest,'r:') as t:
 members=t.getmembers()
 assert 'out/e3/TRINITY_READY' in {m.name for m in members}
 assert 'work/TRINITY_OFFLINE.json' in {m.name for m in members}
 assert all(m.name.startswith(('out','work')) for m in members)
# This checksum is the final artifact write.
(J/'out'/(name+'.sha256')).write_text(digest+'  '+name+'\n')
print(json.dumps(dict(package=str(dest),bytes=dest.stat().st_size,sha256=digest,members=len(members)),indent=2))
