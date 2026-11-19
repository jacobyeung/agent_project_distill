from pathlib import Path
import datetime,json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build23c';B=L/'work/build21';A=L/'attic/build23c';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
sizes={}
for p in L.rglob('*'):
 if p.is_file() and not p.is_symlink():
  key='/'.join(p.relative_to(L).parts[:3]);sizes[key]=sizes.get(key,0)+p.stat().st_size
tree=inventory(L/'work/tree_r1');seal=digest(tree)
assert seal=='5b349b1819bc7dca1010feb81da2e7b1326f9992aff913416981b932cdd58c6c'
assert J.seal(K)=='67ce92f6f7e96af1bd706fe020cef0c989c947149b7327fdde92138d67268a6c'
value=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),tree_seal=seal,tree=tree,
 kit={str(p.relative_to(K)):J.sha(p) for p in K.rglob('*') if p.is_file()},
 packages={str(p.relative_to(L)):dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in (L/'out').glob('*.tar')},
 workspace_bytes=sum(sizes.values()),largest=sorted(sizes.items(),key=lambda x:-x[1])[:20],free=shutil.disk_usage('/scratch').free)
J.write(D/'START.json',value)
for name in ('UPLOADS.json','PACKAGE_MANIFEST.json','FINAL_KITS.json','DELIVERY.json'):
 p=B/name
 if p.exists():shutil.copyfile(p,A/name)
print(json.dumps({k:v for k,v in value.items() if k not in ('tree','kit')},indent=2))
