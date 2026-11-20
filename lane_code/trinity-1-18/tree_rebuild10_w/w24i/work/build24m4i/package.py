import sys,os,stat,tarfile,hashlib,json,io,datetime,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from launch_r1.build import verify
LIMIT=25_000_000_000
validation=J.load(D/'VALIDATION.json');assert validation['status']=='PASS'
seals={n:verify(kit(n)) for n in NAMES};assert seals==validation['kits']
source=W/'w24h/out/tree_rebuild_b24m4h_0eed8bc7.tar'
assert J.sha(source)=='3411b0e8b3818554f13f1193871ed2eec707af7fe8c2bc2af27a17a48a60d107'
excluded={'work/build24m4i/package.log','work/build24m4i/PACKAGE_MANIFEST.json','work/build24m4i/PACKAGE_CHECK.json','work/build24m4i/STORAGE_FINAL.json','out/DELIVERY_24M4I.json'}
files={};paths={};allocated=0;seen_inodes=set();hashes={}
for directory,dirs,names in os.walk(L,followlinks=False):
 for name in dirs+names:
  p=Path(directory)/name;st=p.lstat();key=(st.st_dev,st.st_ino)
  if key not in seen_inodes:allocated+=st.st_blocks*512;seen_inodes.add(key)
  if stat.S_ISDIR(st.st_mode):continue
  rel=str(p.relative_to(L))
  if rel in excluded or rel.startswith('out/tree_rebuild_b24m4i_'):continue
  if stat.S_ISLNK(st.st_mode):files[rel]=dict(type='symlink',target=os.readlink(p),mode=st.st_mode&511)
  else:
   assert stat.S_ISREG(st.st_mode),(rel,st.st_mode)
   if key not in hashes:hashes[key]=J.sha(p)
   files[rel]=dict(type='file',sha256=hashes[key],bytes=st.st_size,mode=st.st_mode&511)
  paths[rel]=p
assert allocated<LIMIT
original={}
with tarfile.open(source,'r|*') as t:
 for m in t:
  if m.islnk():h=original[m.linkname]['sha256']
  else:
   assert m.isfile(),(m.name,m.type)
   f=t.extractfile(m);h0=hashlib.sha256()
   for block in iter(lambda:f.read(1<<20),b''):h0.update(block)
   h=h0.hexdigest()
  original[m.name]=dict(sha256=h,mode=m.mode)
assert not set(original)-set(files),sorted(set(original)-set(files))
attic={}
for n,v in files.items():
 if n.startswith('attic/') and v['type']=='file':attic.setdefault((v['sha256'],v['mode']),[]).append(n)
preserved={};same=0
for n,v in original.items():
 now=files[n]
 if now['type']=='file' and (now['sha256'],now['mode'])==(v['sha256'],v['mode']):same+=1
 else:
  candidates=attic.get((v['sha256'],v['mode']),[]);assert candidates,(n,'original bytes/mode not retained')
  preferred='attic/build24m4i/'+n;preserved[n]=preferred if preferred in candidates else candidates[0]
p=D/'ORIGINAL_MEMBERS_CHECK.json';J.write(p,dict(status='PASS',input_members=len(original),unchanged_members=same,preserved_originals=preserved,no_input_member_removed=True))
rel=str(p.relative_to(L));paths[rel]=p;files[rel]=dict(type='file',sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511)
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4i_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
up=J.load(L/'out/UPLOADS_24M4I.json')
inner=dict(schema='build24m4i-delivery-v1',status='LOCAL_CHECKS_PASS_PRODUCTION_UNTESTED',package='out/'+name,package_seal=seal,base_archive=dict(path=str(source),sha256='3411b0e8b3818554f13f1193871ed2eec707af7fe8c2bc2af27a17a48a60d107'),case='b',tree_sha256=validation['tree_sha256'],kits=seals,config_identities=J.load(D/'CONFIG_IDENTITIES.json'),validation='work/build24m4i/VALIDATION.json',report='out/BUILD24M4I_REPORT.md',case_evidence='out/CASE_24M4I.md',draw_table='out/DRAW_TABLE_24M4I.md',draw_json='out/DRAW_TABLE_24M4I.json',uploads='out/UPLOADS_24M4I.json',upload_list='out/UPLOADS_24M4I.list',GO_delta='out/UPLOADS_24M4I_GO.json',GO=False,GO_template='out/kit_n_go',uploaded=False,launched=False,local_upload_files=up['total_files'],local_upload_bytes=up['total_bytes'],original_members=len(original),original_members_unchanged=same,original_members_preserved=preserved,production_not_exercised=['Production N preparation and populations','Underlying N routing-family draw rates','Production loader admission and training','Frames and model payloads'],archive_compression='xz; tar auto-detects despite .tar suffix',archive_hash_record='External delivery includes archive checksum and verification; embedded delivery precedes archive hashing.',disk_cap_bytes=LIMIT)
manifest=dict(schema='build24m4i-package-v1',package_seal=seal,files=files,seal_domain='All workspace files except live package log, package manifest, delivery and post-package verification records; archive excludes itself')
extra={'work/build24m4i/PACKAGE_MANIFEST.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode(),'out/DELIVERY_24M4I.json':(json.dumps(inner,sort_keys=True,indent=2)+'\n').encode()}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),mode=0o644) for n,raw in extra.items()}}
apparent=sum(v.get('bytes',0) for v in files.values());assert apparent<LIMIT
assert shutil.disk_usage(L).free>100*1024**3,'Scratch reserve below 100 GiB'
print('PACKAGING',name,'members',len(expected),'apparent_bytes',apparent,flush=True)
seen={}
with tarfile.open(target,'w:xz',preset=6) as t:
 for n,v in sorted(expected.items()):
  m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
  if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];t.addfile(m);continue
  key=(v['sha256'],v['mode'])
  if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];t.addfile(m);continue
  seen[key]=n;m.size=v['bytes']
  if n in extra:t.addfile(m,io.BytesIO(extra[n]))
  else:
   with paths[n].open('rb') as f:t.addfile(m,f)
print('VERIFYING',name,flush=True)
actual={}
with tarfile.open(target,'r|*') as t:
 for m in t:
  if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
  elif m.islnk():v={**actual[m.linkname],'mode':m.mode}
  else:
   assert m.isfile();f=t.extractfile(m);h=hashlib.sha256();nbytes=0
   for block in iter(lambda:f.read(1<<20),b''):h.update(block);nbytes+=len(block)
   v=dict(type='file',sha256=h.hexdigest(),bytes=nbytes,mode=m.mode)
  assert m.name not in actual;actual[m.name]=v
assert actual==expected,'Package member verification differs'
h=J.sha(target);size=target.stat().st_size
J.write(D/'PACKAGE_MANIFEST.json',manifest)
storage=dict(workspace_apparent_bytes_before_archive=apparent,archive_bytes=size,allocated_bytes_before_archive=allocated,cap_bytes=LIMIT,conservative_apparent_bound_bytes=apparent+size+20_000_000)
assert storage['conservative_apparent_bound_bytes']<LIMIT
J.write(D/'STORAGE_FINAL.json',storage)
J.write(L/'out/DELIVERY_24M4I.json',dict(inner,sha256=h,bytes=size,verified_members=len(expected),member_bytes_and_modes_verified=True,storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',package=inner['package'],sha256=h,bytes=size,members=len(expected),all_member_bytes_modes_and_links_verified=True,no_input_members_removed=True,original_bytes_modes_preserved=True,kits=seals))
(target.with_suffix('.tar.sha256')).write_text(h+'  '+name+'\n')
print(json.dumps(dict(package=inner['package'],sha256=h,bytes=size,members=len(expected),storage=storage),indent=2),flush=True)
