import sys,os,stat,tarfile,hashlib,json,io,datetime,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from launch_r1.build import verify
LIMIT=25_000_000_000
validation=J.load(D/'VALIDATION.json');assert validation['status']=='PASS'
seals={n:verify(kit(n)) for n in NAMES};assert seals==validation['kits']
source_archive=W/'w24e/out/tree_rebuild_b24m4f_26fb868d.tar'
assert J.sha(source_archive)=='3cc9b8e7185dc808426e61c244f402d988e6f49c4ed279aaaec2da15d38d33aa'
excluded={'work/build24m4h/package.log','work/build24m4h/PACKAGE_MANIFEST.json','work/build24m4h/PACKAGE_CHECK.json','work/build24m4h/STORAGE_FINAL.json','out/DELIVERY_24M4H.json'}
def gather():
 files={};paths={};seen=set();allocated=0
 for directory,dirs,names in os.walk(L,followlinks=False):
  for name in dirs+names:
   p=Path(directory)/name;st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:allocated+=st.st_blocks*512;seen.add(key)
   if stat.S_ISDIR(st.st_mode):continue
   rel=str(p.relative_to(L))
   if rel in excluded or rel.startswith('out/tree_rebuild_b24m4h_'):continue
   if stat.S_ISLNK(st.st_mode):files[rel]=dict(type='symlink',target=os.readlink(p),mode=st.st_mode&511)
   else:
    assert stat.S_ISREG(st.st_mode),(rel,st.st_mode)
    files[rel]=dict(type='file',sha256=J.sha(p),bytes=st.st_size,mode=st.st_mode&511)
   paths[rel]=p
 return files,paths,allocated
files,paths,allocated=gather();assert allocated<LIMIT
# Verify every input-package member survives, or its exact bytes/mode remain in attic.
original={}
with tarfile.open(source_archive,'r|*') as t:
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
  candidates=attic.get((v['sha256'],v['mode']),[]);assert candidates,(n,'original not retained')
  preferred='attic/build24m4h/'+n
  preserved[n]=preferred if preferred in candidates else candidates[0]
J.write(D/'ORIGINAL_MEMBERS_CHECK.json',dict(status='PASS',input_members=len(original),unchanged_members=same,preserved_originals=preserved,no_input_member_removed=True))
# Include the verification record in the package seal.
p=D/'ORIGINAL_MEMBERS_CHECK.json';rel=str(p.relative_to(L));paths[rel]=p;files[rel]=dict(type='file',sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511)
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4h_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
up=J.load(L/'out/UPLOADS_24M4H.json');iv=J.load(D/'INVARIANTS.json')
inner=dict(schema='build24m4h-delivery-v1',status='LOCAL_CHECKS_PASS_PRODUCTION_UNTESTED',package='out/'+name,package_seal=seal,base_archive=dict(path=str(source_archive),sha256=J.sha(source_archive)),tree_sha256=iv['tree_sha256'],kits=seals,validation='work/build24m4h/VALIDATION.json',report='out/BUILD24M4H_REPORT.md',evidence='out/BUILD24M4H_EVIDENCE.md',uploads='out/UPLOADS_24M4H.json',local_upload_list='out/UPLOADS_24M4H_LOCAL.list',orchard_copies='out/ORCHARD_COPIES_24M4H.json',GO_delta='out/UPLOADS_24M4H_GO.json',GO=False,GO_template='out/kit_n_go',GO_template_uploaded=False,uploaded=False,launched=False,local_upload_files=up['local_upload_files'],local_upload_bytes=up['local_upload_bytes'],orchard_copy_bytes=up['orchard_copy_bytes'],config_identities=iv['config_identities'],original_members=len(original),original_members_unchanged=same,original_members_preserved=preserved,write_boundary_incident='work/build24m4h/WRITE_BOUNDARY_INCIDENT.json',rule_compliance='Three files outside H were rewritten by an inherited test import; incident is disclosed. Later tests ran in a filesystem view allowing writes only under H.',production_not_exercised=validation['production_not_exercised'],routing_row_count=dict(P=47898,N=None,N_status='Requires production native preparation and materialization'),archive_compression='xz; tar auto-detects despite .tar suffix',archive_hash_record='External delivery adds archive SHA256, byte count and member verification; embedded delivery precedes archive hashing',disk_cap_bytes=LIMIT)
manifest=dict(schema='build24m4h-package-v1',package_seal=seal,files=files,seal_domain='All workspace files except live package log, package manifest, delivery and post-package verification records; archive excludes itself')
extra={'work/build24m4h/PACKAGE_MANIFEST.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode(),'out/DELIVERY_24M4H.json':(json.dumps(inner,sort_keys=True,indent=2)+'\n').encode()}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),mode=0o644) for n,raw in extra.items()}}
apparent=sum(v.get('bytes',0) for v in files.values());assert apparent<LIMIT
assert shutil.disk_usage(L).free>100*1024**3,'Scratch reserve below 100 GiB'
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
actual={}
with tarfile.open(target,'r|*') as t:
 for m in t:
  if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
  elif m.islnk():v={**actual[m.linkname], 'mode':m.mode}
  else:
   assert m.isfile();f=t.extractfile(m);h=hashlib.sha256();nbytes=0
   for block in iter(lambda:f.read(1<<20),b''):h.update(block);nbytes+=len(block)
   v=dict(type='file',sha256=h.hexdigest(),bytes=nbytes,mode=m.mode)
  assert m.name not in actual;actual[m.name]=v
assert actual==expected,'Package member verification differs'
h=J.sha(target);size=target.stat().st_size
J.write(D/'PACKAGE_MANIFEST.json',manifest)
storage=dict(workspace_apparent_bytes_before_archive=apparent,archive_bytes=size,allocated_bytes_before_archive=allocated,cap_bytes=LIMIT,conservative_apparent_bound_bytes=apparent+size+10_000_000)
assert storage['conservative_apparent_bound_bytes']<LIMIT
J.write(D/'STORAGE_FINAL.json',storage)
delivery=dict(inner,sha256=h,bytes=size,verified_members=len(expected),member_bytes_and_modes_verified=True,storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M4H.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',package=inner['package'],sha256=h,bytes=size,members=len(expected),all_member_bytes_modes_and_links_verified=True,no_input_members_removed=True,original_bytes_modes_preserved=True,kits=seals))
(target.with_suffix('.tar.sha256')).write_text(h+'  '+name+'\n')
print(json.dumps(dict(package=inner['package'],sha256=h,bytes=size,members=len(expected),original_members=len(original),storage=storage),indent=2),flush=True)
