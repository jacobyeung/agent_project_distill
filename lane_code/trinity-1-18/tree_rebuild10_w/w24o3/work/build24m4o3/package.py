from pathlib import Path
import os,sys,json,hashlib,stat,tarfile,io,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4o3'
def load(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
validation=load(D/'VALIDATION.json');assert validation['status']=='PASS'
excluded={'work/build24m4o3/PACKAGE_MANIFEST.json','work/build24m4o3/PACKAGE_CHECK.json',
          'out/DELIVERY_24M4O3.json'}
files={};paths={};hashes={}
for root in ('out','work','attic'):
    for directory,dirs,names in os.walk(L/root,followlinks=False):
        for name in dirs+names:
            p=Path(directory)/name;st=p.lstat()
            if stat.S_ISDIR(st.st_mode):continue
            rel=str(p.relative_to(L))
            if rel in excluded or rel.startswith('out/tree_rebuild_b24m4o3_'):continue
            if stat.S_ISLNK(st.st_mode):v=dict(type='symlink',target=os.readlink(p),mode=st.st_mode&511)
            else:
                assert stat.S_ISREG(st.st_mode),(rel,st.st_mode)
                key=(st.st_dev,st.st_ino)
                if key not in hashes:hashes[key]=sha(p)
                v=dict(type='file',sha256=hashes[key],bytes=st.st_size,mode=st.st_mode&511)
            files[rel]=v;paths[rel]=p
original=load(L/'work/build24m4o/PACKAGE_MANIFEST.json')['files']
assert not set(original)-set(files)
changed={n for n,v in original.items() if files[n]!=v}
assert changed=={'out/rcj/x.py','out/rcj/pc.py'},changed
for n in changed:assert files['attic/build24m4o3/'+n]==original[n]
assert sum(v.get('bytes',0) for v in files.values())<25_000_000_000
assert shutil.disk_usage(L).free>100*1024**3
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4o3_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
manifest=dict(schema='build24m4o3-package-v1',package_seal=seal,files=files,
    seal_domain='out, work and attic except this manifest, delivery, verification and package files')
up=load(L/'out/UPLOADS_24M4O3.json')
delivery=dict(schema='build24m4o3-delivery-v1',package='out/'+name,package_seal=seal,
    base_archive='tree_rebuild_b24m4o_51715686.tar',base_archive_verification='Lane step 0; not repeated',
    tree_sha256=validation['tree_sha256'],kits=validation['kits'],
    uploads='out/UPLOADS_24M4O3.json',upload_list='out/UPLOADS_24M4O3.list',
    report='out/BUILD24M4O3_REPORT.md',validation='work/build24m4o3/VALIDATION.json',
    local_upload_files=up['total_files'],local_upload_bytes=up['total_bytes'],
    input_members=len(original),unchanged_input_members=len(original)-len(changed),
    preserved_originals={n:'attic/build24m4o3/'+n for n in sorted(changed)},
    archive_compression='xz; tar auto-detects despite .tar suffix',
    GO=False,production_executed=False,uploaded=False,launched=False,
    qualifications=validation['qualifications'])
extra={'work/build24m4o3/PACKAGE_MANIFEST.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode(),
       'out/DELIVERY_24M4O3.json':(json.dumps(delivery,sort_keys=True,indent=2)+'\n').encode()}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),mode=0o644) for n,b in extra.items()}}
print('Packaging',name,'with',len(expected),'members',flush=True)
seen={}
with tarfile.open(target,'w:xz',preset=3) as archive:
    for n,v in sorted(expected.items()):
        m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
        if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];archive.addfile(m);continue
        key=(v['sha256'],v['mode'])
        if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];archive.addfile(m);continue
        seen[key]=n;m.size=v['bytes']
        if n in extra:archive.addfile(m,io.BytesIO(extra[n]))
        else:
            with paths[n].open('rb') as stream:archive.addfile(m,stream)
print('Verifying every archived file, mode and link',flush=True)
actual={}
with tarfile.open(target,'r|*') as archive:
    for m in archive:
        if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
        elif m.islnk():v={**actual[m.linkname],'mode':m.mode}
        else:
            assert m.isfile();h=hashlib.sha256();size=0
            with archive.extractfile(m) as stream:
                for block in iter(lambda:stream.read(1<<20),b''):h.update(block);size+=len(block)
            v=dict(type='file',sha256=h.hexdigest(),bytes=size,mode=m.mode)
        assert m.name not in actual;actual[m.name]=v
assert actual==expected
h=sha(target);size=target.stat().st_size
write(D/'PACKAGE_MANIFEST.json',manifest)
write(L/'out/DELIVERY_24M4O3.json',dict(delivery,sha256=h,bytes=size,verified_members=len(expected)))
write(D/'PACKAGE_CHECK.json',dict(status='PASS',package='out/'+name,sha256=h,bytes=size,
    verified_members=len(expected),all_bytes_modes_links_verified=True,
    no_input_members_removed=True,superseded_bytes_modes_preserved=True))
# This checksum is the final output file written.
target.with_suffix('.tar.sha256').write_text(h+'  '+name+'\n')
print(json.dumps(dict(package='out/'+name,sha256=h,bytes=size,verified_members=len(expected)),indent=2),flush=True)
