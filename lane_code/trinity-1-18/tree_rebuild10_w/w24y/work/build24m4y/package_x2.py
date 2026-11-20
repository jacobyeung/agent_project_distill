from pathlib import Path
import hashlib,io,json,os,shutil,stat,tarfile,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
L=Path.cwd();D=L/"work/build24m4y"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as s:
  for b in iter(lambda:s.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
validation=json.loads((D/"VALIDATION.json").read_text());assert validation["checks_status"]=="PASS"
assert json.loads((D/"INVARIANTS.json").read_text())["status"]=="PASS"
assert shutil.disk_usage(L).free>100*1024**3
excluded={"work/build24m4y/PACKAGE_MANIFEST.json","work/build24m4y/PACKAGE_CHECK.json","out/DELIVERY_24M4X2.json"}
files={};paths={};cache={}
print("Inventorying final package",flush=True)
for root in ("out","work","attic"):
 for directory,dirs,names in os.walk(L/root,followlinks=False):
  for name in dirs+names:
   p=Path(directory)/name;s=p.lstat()
   if stat.S_ISDIR(s.st_mode):continue
   n=str(p.relative_to(L))
   if n in excluded or n.startswith("out/tree_rebuild_b24m4x2_"):continue
   if stat.S_ISLNK(s.st_mode):v=dict(type="symlink",target=os.readlink(p),mode=s.st_mode&511)
   else:
    assert stat.S_ISREG(s.st_mode),(n,s.st_mode)
    key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in cache:cache[key]=sha(p)
    v=dict(type="file",sha256=cache[key],bytes=s.st_size,mode=s.st_mode&511)
   files[n]=v;paths[n]=p
original=json.loads((L/"work/build24m4w/PACKAGE_MANIFEST.json").read_text())["files"]
assert not set(original)-set(files)
retained={(v.get('type'),v.get('sha256'),v.get('bytes'),v.get('mode'),v.get('target')) for v in files.values()}
for n,v in original.items():
    if files[n]!=v:
        assert (v.get('type'),v.get('sha256'),v.get('bytes'),v.get('mode'),v.get('target')) in retained, ('Original bytes not retained',n)
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(",",":")).encode()).hexdigest()
name="tree_rebuild_b24m4x2_"+seal[:8]+".tar";target=L/"out"/name;assert not target.exists()
manifest=dict(schema="build24m4y-package-v1",package_seal=seal,files=files,seal_domain="out, work, attic except this manifest, delivery, package verification and final package files")
up=json.loads((L/"out/UPLOADS_24M4X2.json").read_text())
delivery=dict(schema="build24m4y-delivery-v1",package="out/"+name,package_seal=seal,tree_sha256=validation["tree_sha256"],kits=validation["kits"],rcj=validation["rcj"],report="out/BUILD24M4X2_REPORT.md",validation="work/build24m4y/VALIDATION.json",uploads="out/UPLOADS_24M4X2.json",upload_list="out/UPLOADS_24M4X2.list",optional_uploads="out/UPLOADS_24M4X2_GO.json",tree_patch="out/TREE_CHANGE_24M4X.patch",apply="out/apply_24m4x.py",local_upload_files=up["total_files"],local_upload_bytes=up["total_bytes"],checks_status="PASS",qualification=validation["offline_scope"],production_executed=False,uploaded=False,launched=False,GO=False,archive_compression="xz",logical_member_bytes=sum(v.get("bytes",0) for v in files.values()))
extra={"work/build24m4y/PACKAGE_MANIFEST.json":(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode(),"out/DELIVERY_24M4X2.json":(json.dumps(delivery,sort_keys=True,indent=2)+"\n").encode()}
expected={**files,**{n:dict(type="file",sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),mode=0o644) for n,b in extra.items()}}
print("Packaging",name,"members",len(expected),"logical bytes",delivery["logical_member_bytes"],flush=True)
seen={}
with tarfile.open(target,"w:xz",preset=3) as tar:
 for n,v in sorted(expected.items()):
  m=tarfile.TarInfo(n);m.mode=v["mode"];m.mtime=0
  if v["type"]=="symlink":m.type=tarfile.SYMTYPE;m.linkname=v["target"];tar.addfile(m);continue
  key=(v["sha256"],v["mode"])
  if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];tar.addfile(m);continue
  seen[key]=n;m.size=v["bytes"]
  if n in extra:tar.addfile(m,io.BytesIO(extra[n]))
  else:
   with paths[n].open("rb") as stream:tar.addfile(m,stream)
print("Verifying every archived byte, mode and link",flush=True)
actual={}
with tarfile.open(target,"r|*") as tar:
 for m in tar:
  if m.issym():v=dict(type="symlink",target=m.linkname,mode=m.mode)
  elif m.islnk():v={**actual[m.linkname],"mode":m.mode}
  else:
   assert m.isfile();h=hashlib.sha256();size=0
   with tar.extractfile(m) as stream:
    for b in iter(lambda:stream.read(1<<20),b""):h.update(b);size+=len(b)
   v=dict(type="file",sha256=h.hexdigest(),bytes=size,mode=m.mode)
  assert m.name not in actual;actual[m.name]=v
assert actual==expected
h=sha(target);size=target.stat().st_size
(D/"PACKAGE_MANIFEST.json").write_bytes(extra["work/build24m4y/PACKAGE_MANIFEST.json"])
(L/"out/DELIVERY_24M4X2.json").write_bytes(extra["out/DELIVERY_24M4X2.json"])
write(D/"PACKAGE_CHECK.json",dict(status="PASS",package="out/"+name,sha256=h,bytes=size,verified_members=len(expected),all_bytes_modes_links_verified=True,no_input_members_removed=True,superseded_bytes_modes_preserved=True))
print(json.dumps(dict(package="out/"+name,sha256=h,bytes=size,verified_members=len(expected)),indent=2),flush=True)
# This checksum is the final filesystem write.
target.with_suffix(".tar.sha256").write_text(h+"  "+name+"\n")
