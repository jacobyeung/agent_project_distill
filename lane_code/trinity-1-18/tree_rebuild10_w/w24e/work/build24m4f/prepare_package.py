from common import *
import tarfile
C=L.parent/"w24c/out/tree_rebuild_b24m4c_b7be125e.tar"
E=L/"out/tree_rebuild_b24m4e_737062d4.tar"
def content(path):
 with tarfile.open(path) as t:
  result={}
  for m in t:
   assert m.isfile() or m.islnk(),(m.name,m.type)
   assert not Path(m.name).is_absolute() and ".." not in Path(m.name).parts
   raw=t.extractfile(m).read();result[m.name]=(raw,m.mode)
  return result
c=content(C);e=content(E);missing=sorted(set(c)-set(e));restored=[];existing=[]
# Restore only absent historical members. Existing bytes are never overwritten.
for name in missing:
 raw,mode=c[name];p=L/name
 if p.exists():
  existing.append(dict(name=name,package_bytes_match_workspace=p.read_bytes()==raw,package_mode_matches_workspace=p.stat().st_mode&511==mode))
  continue
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(raw)
 p.chmod(mode);restored.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),mode=format(mode,"04o")))
J.write(D/"RESTORED_MEMBERS.json",dict(status="PASS",source=str(C),source_sha256=J.sha(C),members_omitted_by_24m4e=missing,restored_to_workspace=restored,existing_workspace_members=existing,all_omitted_members_in_new_package=True))
base=J.load(L/"out/DELIVERY_24M4E.json");kits={}
from launch_r1.build import verify
for name in ("q","n","n_go","qd"):
 k=kit(name);seal=verify(k);assert seal==base["kits"][name];kits[name]=seal
 prefix=str(k.relative_to(L))+"/"
 a={n:(hashlib.sha256(raw).hexdigest(),mode) for n,(raw,mode) in e.items() if n.startswith(prefix)}
 b={str(p.relative_to(L)):(J.sha(p),p.stat().st_mode&511) for p in k.rglob("*") if p.is_file()}
 assert a==b,(name,"kit changed")
 assert not (k/"arm_routing.py").exists()
tree={n:(hashlib.sha256(raw).hexdigest(),mode) for n,(raw,mode) in e.items() if n.startswith("work/tree_r1/")}
actual={str(p.relative_to(L)):(J.sha(p),p.stat().st_mode&511) for p in (L/"work/tree_r1").rglob("*") if p.is_file()}
assert tree==actual and len(tree)==944
original=J.load(D/"ORIGINAL_FILES.json");relocated={"out/arm_routing.py":"attic/build24m4f/out/arm_routing.py","out/ARM_ROUTING_USAGE.md":"attic/build24m4f/out/ARM_ROUTING_USAGE.md"}
for name,s in original.items():
 p=L/relocated.get(name,name);now=p.stat()
 assert (now.st_ino,now.st_dev,now.st_size,now.st_mode&511,now.st_mtime_ns)==(s["inode"],s["device"],s["size"],s["mode"],s["mtime_ns"]),(name,"original changed")
for name,new in relocated.items():assert (L/new).read_bytes()==e[name][0]
J.write(D/"INVARIANTS.json",dict(status="PASS",tree_sha256=base["tree_sha256"],tree_files=len(tree),kits=kits,kit_bytes_and_modes_unchanged=True,arm_routing_inside_kit=False,original_files_verified=len(original),preserved_originals=relocated,unchanged=["Tree C","All four kit files, modes and seals","rv.py, census, admission, legality, removals, pins and b/pc.py","Every original source/archive byte and mode"]))
print("Restored",len(restored),"missing workspace members; package restores",len(missing),"members")
print("All four kit seals and tree bytes/modes unchanged; originals preserved",len(original))
