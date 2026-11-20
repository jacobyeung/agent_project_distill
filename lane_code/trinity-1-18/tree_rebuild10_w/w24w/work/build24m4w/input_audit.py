from pathlib import Path
import os,stat,hashlib,json,shutil
L=Path.cwd();D=L/"work/build24m4w";V=L.parent/"w24v"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as s:
  for b in iter(lambda:s.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
base=json.loads((L/"work/build24m4u/PACKAGE_MANIFEST.json").read_text())["files"]
allowed={"out/rcj/ch.py","out/TREE_SEAL.json","out/TREE_FILES.sha256"}
allowed|={"work/tree_r1c/"+n for n in json.loads((D/"SEALS_FINAL.json").read_text())["changed_tree_files"]}
allowed|={v["file"] for v in json.loads((D/"MERGE.json").read_text())["kit_files"]}
cache={};changes=[];unexpected=[];missing=[]
for n,v in base.items():
 p=L/n
 try:s=p.lstat()
 except FileNotFoundError:missing.append(n);continue
 if v["type"]=="symlink":same=p.is_symlink() and os.readlink(p)==v["target"] and s.st_mode&511==v["mode"]
 else:
  key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
  if key not in cache:cache[key]=sha(p)
  same=dict(type="file",sha256=cache[key],bytes=s.st_size,mode=s.st_mode&511)==v
 if not same:(changes if n in allowed else unexpected).append(n)
assert not missing,missing
restored=[]
if unexpected:
 manifests=[(L,base),(V,json.loads((V/"work/build24m4v/PACKAGE_MANIFEST.json").read_text())["files"])]
 for n in unexpected:
  v=base[n];candidates=[V/n]
  for root,m in manifests:candidates.extend(root/r for r,record in m.items() if record.get("sha256")==v.get("sha256") and (root/r)!=L/n)
  source=next((p for p in candidates if p.is_file() and sha(p)==v["sha256"]),None)
  assert source is not None,("Original unavailable",n)
  p=L/n;saved=L/"attic/build24m4w/fixture_aliases"/n;saved.parent.mkdir(parents=True,exist_ok=True);p.rename(saved)
  shutil.copyfile(source,p);p.chmod(v["mode"]);restored.append(dict(path=n,source=str(source),sha256=v["sha256"]))
for n in changes:
 saved=L/"attic/build24m4v_apply"/n;v=base[n]
 assert saved.is_file() and sha(saved)==v["sha256"] and saved.stat().st_mode&511==v["mode"],n
assert set(changes)==allowed,(sorted(set(changes)-allowed),sorted(allowed-set(changes)))
write(D/"INPUT_AUDIT.json",dict(status="PASS",original_members=len(base),changed_members=changes,restored_fixture_aliases=restored,no_input_members_removed=True,superseded_bytes_modes_preserved=True))
print("INPUT AUDIT PASS",len(base),len(changes),"restored",len(restored),flush=True)
