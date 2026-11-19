from pathlib import Path
import json,hashlib,shutil,datetime
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c';C.mkdir(exist_ok=True)
A=L/'attic/build21c';A.mkdir(parents=True,exist_ok=True)
names=['naming21.py','joblib.py','kit.py','test21.py','OPERATOR.md','UPLOADS.json','FINAL_KITS.json','PACKAGE_MANIFEST.json','DELIVERY.json']
for name in names:
    p=B/name;q=A/name
    if not q.exists():shutil.copyfile(p,q)
for name in ('k/p.json','k/n.json','BUILD.json','SHA256SUMS.txt'):
    q=A/'kit'/name;q.parent.mkdir(parents=True,exist_ok=True)
    if not q.exists():shutil.copyfile(B/'kits/q'/name,q)
base=L/'out/tree_rebuild_b21_b262e7a7.tar'
h=hashlib.sha256()
with base.open('rb') as f:
    for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
assert h.hexdigest().startswith('fb9de190')
value=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace_bytes=4662437095,
    base=dict(path=str(base.relative_to(L)),sha256=h.hexdigest(),bytes=base.stat().st_size),
    tree=json.loads((L/'out/TREE_SEAL.json').read_text()))
(C/'START.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
