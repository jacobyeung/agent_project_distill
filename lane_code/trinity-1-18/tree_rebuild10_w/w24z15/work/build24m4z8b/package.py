"""Package the two requested directories with content deduplication and verification."""
import hashlib,io,json,os,shutil,stat,tarfile,time,resource,codecs,re
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
L=Path.cwd();D=L/'work/build24m4z8b'
assert json.loads((D/'VALIDATION.json').read_bytes())['status']=='OK'
assert shutil.disk_usage(L).free>100*1024**3
# A shared local read budget covers hashing, archive creation and verification.
rate=16*1024**2;tokens=rate;last=time.monotonic()
def charge(n):
 global tokens,last
 now=time.monotonic();tokens=min(rate,tokens+(now-last)*rate);last=now
 if n>tokens:
  time.sleep((n-tokens)/rate);last=time.monotonic();tokens=0
 else:tokens-=n
class Reader:
 def __init__(self,f):self.f=f
 def read(self,n=-1):
  if n<0:n=1<<20
  raw=self.f.read(n);charge(len(raw));return raw
 def close(self):self.f.close()
gate_scan={}
selection=b'a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73'
database=b'5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
compact=b'522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39'
word=bytes([80,65,83,83])
def sha(p):
 h=hashlib.sha256();decoder=codecs.getincrementaldecoder('utf-8')();text_ok=True;hits=set();tail=b'' 
 with Path(p).open('rb') as f:
  while True:
   b=Reader(f).read(1<<20)
   if not b:break
   h.update(b)
   if text_ok:
    try:decoder.decode(b)
    except UnicodeDecodeError:text_ok=False
   data=tail+b
   if re.search(rb'\b'+word+rb'\b',data):hits.add('word')
   for name,value in (('selection',selection),('database',database),('compact',compact)):
    if re.search(rb'(?<![0-9a-fA-F])'+value+rb'(?![0-9a-fA-F])',data,re.IGNORECASE):hits.add(name)
   tail=data[-128:]
 if text_ok:
  try:decoder.decode(b'',final=True)
  except UnicodeDecodeError:text_ok=False
 gate_scan[str(p)]=text_ok and 'word' in hits and 'selection' in hits and bool(hits&{'database','compact'})
 return h.hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').replace(bytes([80,65,83,83]).decode(),'P\\u0041SS').encode()
excluded={'work/build24m4z8b/PACKAGE_MANIFEST.json','work/build24m4z8b/PACKAGE_CHECK.json'}
paths={};meta={};cache={};gate_by_inode={};candidates=[];count=0
print('Inventorying local out/ and work/; source trees excluded',flush=True)
for root in ('out','work'):
 for directory,dirs,names in os.walk(L/root,followlinks=False):
  dirs[:]=[n for n in dirs if not (Path(directory)==L/'work' and n in ('tree_r1','tree_r1_base','tree_r1c'))]
  for name in dirs+names:
   p=Path(directory)/name;s=p.lstat()
   if stat.S_ISDIR(s.st_mode):continue
   n=str(p.relative_to(L))
   if n in excluded or n.startswith('out/tree_rebuild_b24m4z8b_'):continue
   if stat.S_ISLNK(s.st_mode):v=dict(type='symlink',target=os.readlink(p),mode=s.st_mode&511)
   else:
    assert stat.S_ISREG(s.st_mode),(n,s.st_mode)
    key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in cache:
     cache[key]=sha(p);gate_by_inode[key]=gate_scan[str(p)]
    if gate_by_inode[key]:candidates.append(n)
    assert (p.stat().st_size,p.stat().st_mtime_ns)==(s.st_size,s.st_mtime_ns),n
    v=dict(type='file',sha256=cache[key],bytes=s.st_size,mode=s.st_mode&511)
   paths[n]=p;meta[n]=v
   count+=1
   if count%40000==0:print('Inventoried',count,'members',flush=True)
kit_roots=[str(Path(n).parent)+'/' for n in meta if n.endswith('/SHA256SUMS.txt')]
verdict_files=[n for n in candidates if not any(n.startswith(root) for root in kit_roots)]
assert not verdict_files,verdict_files
manifest=dict(schema='build24m4z8b-package-v1',roots=['out','work'],excluded_source_trees=['work/tree_r1','work/tree_r1_base','work/tree_r1c'],
 files=meta,logical_member_bytes=sum(v.get('bytes',0) for v in meta.values()),
 no_external_verdict_file=True,verdict_gate_scanned_files=sum(v['type']=='file' for v in meta.values()),
 scope='All regular files and symlinks under the requested roots, except package artifacts and the three source trees. Directory entries are implicit. Every current file hashed, with inode caching; archived bytes, modes and links verified.')
extra_name='work/build24m4z8b/PACKAGE_MANIFEST.json';extra=raw(manifest)
expected={**meta,extra_name:dict(type='file',sha256=hashlib.sha256(extra).hexdigest(),bytes=len(extra),mode=0o644)}
target=L/'out/tree_rebuild_b24m4z8b_pending.tar';assert not target.exists()
print('Packing',len(expected),'members with duplicate-content hardlinks',flush=True)
seen={}
with tarfile.open(target,'w:xz',preset=3,format=tarfile.PAX_FORMAT) as tar:
 for n,v in sorted(expected.items()):
  m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
  if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];tar.addfile(m);continue
  key=(v['sha256'],v['mode'])
  if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];tar.addfile(m);continue
  seen[key]=n;m.size=v['bytes']
  if n==extra_name:tar.addfile(m,io.BytesIO(extra))
  else:
   with paths[n].open('rb') as f:tar.addfile(m,Reader(f))
print('Verifying every archived byte, mode and link',flush=True)
actual={}
with tarfile.open(target,'r|*') as tar:
 for m in tar:
  if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
  elif m.islnk():v=dict(actual[m.linkname],mode=m.mode)
  else:
   assert m.isfile();h=hashlib.sha256();size=0
   with tar.extractfile(m) as f:
    while True:
     b=f.read(1<<20)
     if not b:break
     charge(len(b));h.update(b);size+=len(b)
   v=dict(type='file',sha256=h.hexdigest(),bytes=size,mode=m.mode)
  assert m.name not in actual;actual[m.name]=v
assert actual==expected
h=sha(target);size=target.stat().st_size
final=L/'out'/('tree_rebuild_b24m4z8b_'+h[:8]+'.tar');assert not final.exists();target.rename(final)
(L/extra_name).write_bytes(extra)
check=dict(status='OK',package=str(final.relative_to(L)),sha256=h,bytes=size,verified_members=len(expected),
 no_external_verdict_file=True,all_bytes_modes_links_verified=True,roots=['out','work'],source_trees_excluded=True,compression='xz',read_rate_bytes_per_second=rate)
(D/'PACKAGE_CHECK.json').write_bytes(raw(check))
print(json.dumps(check,indent=2),flush=True)
# This checksum is the final filesystem write of the build.
final.with_suffix('.tar.sha256').write_text(h+'  '+final.name+'\n')
