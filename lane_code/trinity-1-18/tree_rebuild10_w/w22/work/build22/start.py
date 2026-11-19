from pathlib import Path
import hashlib,json,tarfile,datetime,sys
L=Path(__file__).resolve().parents[2]; B=L/'work/build22'
B.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
p=L.parent/'w21/out/tree_rebuild_b21g_2f9a23be.tar'
assert sha(p)=='e378b8dcbf26a48d741a189b8f934d8d927e67492b33bd6464805e48780dd390'
checked=0
with tarfile.open(p,'r|gz') as t:
 for m in t:
  assert m.isfile()
  q=L/m.name
  assert q.is_relative_to(L) and q.is_file(),str(q)
  h=hashlib.sha256(t.extractfile(m).read()).hexdigest()
  assert sha(q)==h,str(q)
  checked+=1
record=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),base=str(p),sha256=sha(p),members=checked,workspace_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))
(B/'START.json').write_text(json.dumps(record,indent=2)+'\n')
print(record)
