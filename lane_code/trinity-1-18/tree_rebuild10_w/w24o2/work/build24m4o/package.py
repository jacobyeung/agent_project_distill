import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import stat, tarfile, io, datetime, shutil

LIMIT=25_000_000_000
validation=z.load(D/'VALIDATION.json');assert validation['status']=='PASS'
excluded={'work/build24m4o/PACKAGE_MANIFEST.json','work/build24m4o/PACKAGE_CHECK.json',
          'work/build24m4o/STORAGE_FINAL.json','out/DELIVERY_24M4O.json'}
files={};paths={};allocated=0;seen_inodes=set();hashes={}
for root in ('out','work','attic'):
    for directory,dirs,names in os.walk(L/root,followlinks=False):
        for name in dirs+names:
            p=Path(directory)/name;st=p.lstat();key=(st.st_dev,st.st_ino)
            if key not in seen_inodes:allocated+=st.st_blocks*512;seen_inodes.add(key)
            if stat.S_ISDIR(st.st_mode):continue
            rel=str(p.relative_to(L))
            if rel in excluded or rel.startswith('out/tree_rebuild_b24m4o_'):continue
            if stat.S_ISLNK(st.st_mode):files[rel]=dict(type='symlink',target=os.readlink(p),mode=st.st_mode&511)
            else:
                assert stat.S_ISREG(st.st_mode),(rel,st.st_mode)
                if key not in hashes:hashes[key]=z.sha(p)
                files[rel]=dict(type='file',sha256=hashes[key],bytes=st.st_size,mode=st.st_mode&511)
            paths[rel]=p
assert allocated<LIMIT
print('Inventoried',len(files),'members;',allocated,'allocated bytes',flush=True)
# Step 0 already authenticated and extracted the input archive. Recheck all
# inventoried input members without rereading or unpacking that archive.
incoming=z.load(L/'work/build24m4n/PACKAGE_MANIFEST.json')
original=incoming['files'];assert not set(original)-set(files)
attic={}
for n,v in files.items():
    if n.startswith('attic/') and v['type']=='file':attic.setdefault((v['sha256'],v['mode']),[]).append(n)
preserved={};same=0
for n,v in original.items():
    if files[n]==v:same+=1
    else:
        assert v['type']=='file',(n,'changed input symlink')
        candidates=attic.get((v['sha256'],v['mode']),[]);assert candidates,(n,'input bytes/mode not preserved')
        preferred='attic/build24m4o/'+n
        preserved[n]=preferred if preferred in candidates else candidates[0]
assert set(preserved)=={'out/kit_qd/b/f0.py','out/kit_qd/BUILD.json','out/kit_qd/SHA256SUMS.txt','out/rcj/x.py'},preserved
p=D/'ORIGINAL_MEMBERS_CHECK.json'
write(p,dict(status='PASS',basis='Supplied authenticated input inventory; archive verification/extraction completed by lane step 0',
    input_inventoried_members=len(original),unchanged_members=same,preserved_originals=preserved,no_inventoried_input_member_removed=True,
    input_manifest_sha256=z.sha(L/'work/build24m4n/PACKAGE_MANIFEST.json')))
rel=str(p.relative_to(L));paths[rel]=p;files[rel]=dict(type='file',sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511)
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4o_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
up=z.load(L/'out/UPLOADS_24M4O.json')
inner=dict(schema='build24m4o-delivery-v1',status='LOCAL_PUBLICATION_AND_FIXTURES_PASS',
    package='out/'+name,package_seal=seal,
    base_archive=dict(path='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24n2/out/tree_rebuild_b24m4n_b1e55d2a.tar',
        sha256='7c8e19da8f00b5b443889fd3647eaf97833d44543cbd3c40076cff4e33b94120',verification='Lane step 0; not repeated'),
    tree_sha256=validation['tree_sha256'],kits=validation['kits'],validation='work/build24m4o/VALIDATION.json',
    diagnosis='out/DIAG_173680.md',routes='out/ROUTES_24M4O.md',report='out/BUILD24M4O_REPORT.md',
    uploads='out/UPLOADS_24M4O.json',upload_list='out/UPLOADS_24M4O.list',
    GO=False,production_executed=False,uploaded=False,launched=False,route_changed=False,
    local_upload_files=up['total_files'],local_upload_bytes=up['total_bytes'],
    input_inventoried_members=len(original),input_members_unchanged=same,preserved_originals=preserved,
    archive_compression='xz; tar auto-detects despite .tar suffix',
    archive_hash_record='External delivery adds archive checksum, verified member count and final storage.',disk_cap_bytes=LIMIT,
    limitations=validation['qualifications'])
manifest=dict(schema='build24m4o-package-v1',package_seal=seal,files=files,
    seal_domain='out, work and attic payload files except package manifest, delivery and post-package verification; excludes archive/checksum and managed hidden directories')
extra={'work/build24m4o/PACKAGE_MANIFEST.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode(),
       'out/DELIVERY_24M4O.json':(json.dumps(inner,sort_keys=True,indent=2)+'\n').encode()}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),mode=0o644) for n,raw in extra.items()}}
apparent=sum(v.get('bytes',0) for v in files.values());assert apparent<LIMIT
assert shutil.disk_usage(L).free>100*1024**3,'Scratch reserve below 100 GiB'
print('Packaging',name,'members',len(expected),'apparent bytes',apparent,flush=True)
seen={}
with tarfile.open(target,'w:xz',preset=3) as t:
    for n,v in sorted(expected.items()):
        m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
        if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];t.addfile(m);continue
        key=(v['sha256'],v['mode'])
        if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];t.addfile(m);continue
        seen[key]=n;m.size=v['bytes']
        if n in extra:t.addfile(m,io.BytesIO(extra[n]))
        else:
            with paths[n].open('rb') as f:t.addfile(m,f)
print('Verifying archive member bytes, modes and links',flush=True)
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
h=z.sha(target);size=target.stat().st_size
write(D/'PACKAGE_MANIFEST.json',manifest)
storage=dict(workspace_apparent_bytes_before_archive=apparent,archive_bytes=size,
    allocated_bytes_before_archive=allocated,cap_bytes=LIMIT,conservative_apparent_bound_bytes=apparent+size+30_000_000)
assert storage['conservative_apparent_bound_bytes']<LIMIT
write(D/'STORAGE_FINAL.json',storage)
write(L/'out/DELIVERY_24M4O.json',dict(inner,sha256=h,bytes=size,verified_members=len(expected),
    member_bytes_and_modes_verified=True,storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
write(D/'PACKAGE_CHECK.json',dict(status='PASS',package=inner['package'],sha256=h,bytes=size,members=len(expected),
    all_member_bytes_modes_and_links_verified=True,no_inventoried_input_members_removed=True,
    original_bytes_modes_preserved=True,kits=validation['kits']))
# The checksum is deliberately the final output file written.
target.with_suffix('.tar.sha256').write_text(h+'  '+name+'\n')
print(json.dumps(dict(package=inner['package'],sha256=h,bytes=size,members=len(expected),storage=storage),indent=2),flush=True)
