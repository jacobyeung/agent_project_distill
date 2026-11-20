from pathlib import Path
import os,stat,json,hashlib,tarfile,io,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z2';O=J/'out'
assert json.loads((D/'VALIDATION.json').read_text())['artifact_checks']=='PASS'
assert __import__('shutil').disk_usage(J).free>100*1024**3
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
exclude={'work/tree_r1','work/tree_r1c','work/tree_r1_base','work/build24m4z2/PACKAGE_MANIFEST.json','work/build24m4z2/PACKAGE_CHECK.json'}
files={};paths={};cache={}
print('Inventorying out and work; canonical trees excluded',flush=True)
for root in ('out','work'):
 for directory,dirs,names in os.walk(J/root,followlinks=False):
  dirs[:]=sorted(n for n in dirs if str((Path(directory)/n).relative_to(J)) not in exclude)
  for name in dirs+names:
   p=Path(directory)/name;n=str(p.relative_to(J));s=p.lstat()
   if stat.S_ISDIR(s.st_mode):continue
   if n in exclude or n.startswith('out/tree_rebuild_b24m4z2_') or n=='out/package_24m4z2.part':continue
   if stat.S_ISLNK(s.st_mode):v=dict(type='symlink',target=os.readlink(p),mode=s.st_mode&511)
   else:
    assert stat.S_ISREG(s.st_mode),(n,s.st_mode)
    key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in cache:cache[key]=sha(p)
    v=dict(type='file',sha256=cache[key],bytes=s.st_size,mode=s.st_mode&511)
   files[n]=v;paths[n]=p
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest=dict(schema='24m4z2-package-v1',inventory_sha256=seal,files=files,excluded=sorted(exclude),enospc_gate='FAIL',reason='Adopted kit has no GCS exit-archive route')
raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(D/'PACKAGE_MANIFEST.json').write_bytes(raw)
extra='work/build24m4z2/PACKAGE_MANIFEST.json'
expected={**files,extra:dict(type='file',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),mode=(D/'PACKAGE_MANIFEST.json').stat().st_mode&511)}
target=O/'package_24m4z2.part';assert not target.exists()
seen={}
print('Packing',len(expected),'members',flush=True)
with tarfile.open(target,'w:xz',preset=1) as t:
 for n,v in sorted(expected.items()):
  m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
  if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];t.addfile(m);continue
  key=(v['sha256'],v['mode'])
  if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];t.addfile(m);continue
  seen[key]=n;m.size=v['bytes']
  if n==extra:t.addfile(m,io.BytesIO(raw))
  else:
   with paths[n].open('rb') as f:t.addfile(m,f)
print('Verifying every archived member',flush=True)
actual={}
with tarfile.open(target,'r|*') as t:
 for m in t:
  if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
  elif m.islnk():v=dict(actual[m.linkname],mode=m.mode)
  else:
   h=hashlib.sha256()
   with t.extractfile(m) as f:
    for b in iter(lambda:f.read(1<<20),b''):h.update(b)
   v=dict(type='file',sha256=h.hexdigest(),bytes=m.size,mode=m.mode)
  actual[m.name]=v
assert actual==expected
h=sha(target);final=O/('tree_rebuild_b24m4z2_'+h[:8]+'.tar');assert not final.exists();target.rename(final)
check=dict(status='PASS',package=str(final.relative_to(J)),sha256=h,bytes=final.stat().st_size,members=len(actual),inventory_sha256=seal,canonical_trees_excluded=True,all_bytes_modes_links_verified=True,compression='xz',enospc_gate='FAIL')
(D/'PACKAGE_CHECK.json').write_text(json.dumps(check,sort_keys=True,indent=2)+'\n')
# This is deliberately the build's last filesystem write.
Path(str(final)+'.sha256').write_text(h+'  '+final.name+'\n')
print(json.dumps(check),flush=True)
