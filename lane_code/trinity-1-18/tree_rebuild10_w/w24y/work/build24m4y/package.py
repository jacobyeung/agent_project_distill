from pathlib import Path
import hashlib, io, json, os, shutil, stat, tarfile

L=Path(__file__).resolve().parents[2];D=L/'work/build24m4y'
def load(path):return json.loads(path.read_bytes())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()

validation=load(D/'VALIDATION.json');assert validation['status']=='PASS'
excluded={'work/build24m4y/PACKAGE_MANIFEST.json','work/build24m4y/PACKAGE_CHECK.json','out/DELIVERY_24M4T.json'}
files={};paths={};hashes={}
print('Inventorying delivery bytes',flush=True)
for root in ('out','work','attic'):
    for directory,dirs,names in os.walk(L/root,followlinks=False):
        for name in dirs+names:
            p=Path(directory)/name;st=p.lstat()
            if stat.S_ISDIR(st.st_mode):continue
            rel=str(p.relative_to(L))
            if rel in excluded or rel.startswith('out/tree_rebuild_b24m4t_'):continue
            if stat.S_ISLNK(st.st_mode):v=dict(type='symlink',target=os.readlink(p),mode=st.st_mode&511)
            else:
                assert stat.S_ISREG(st.st_mode),(rel,st.st_mode)
                key=(st.st_dev,st.st_ino)
                if key not in hashes:hashes[key]=sha(p)
                v=dict(type='file',sha256=hashes[key],bytes=st.st_size,mode=st.st_mode&511)
            files[rel]=v;paths[rel]=p
original=load(L/'work/build24m4s/PACKAGE_MANIFEST.json')['files']
assert not set(original)-set(files),sorted(set(original)-set(files))
changed={n for n,v in original.items() if files[n]!=v}
expected_changes={root+'/'+name for root in ('work/build24/kits/q','work/build24/kits/n','out/kit_n_go','out/kit_qd') for name in ('b/pl.py','BUILD.json','SHA256SUMS.txt')}|{'out/rcj/x.py'}
assert changed==expected_changes,sorted(changed ^ expected_changes)
for n in changed:assert files['attic/build24m4y/'+n]==original[n],n
logical_bytes=sum(v.get('bytes',0) for v in files.values())
assert shutil.disk_usage(L).free>100*1024**3
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4t_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
manifest=dict(schema='build24m4y-package-v1',package_seal=seal,files=files,seal_domain='out, work and attic except this manifest, delivery, verification and package files')
up=load(L/'out/UPLOADS_24M4T.json')
delivery=dict(schema='build24m4y-delivery-v1',package='out/'+name,package_seal=seal,base_archive='tree_rebuild_b24m4s_9f4a9c23.tar',base_archive_verification='Lane step 0; not repeated',tree_sha256=validation['tree_sha256'],kits=validation['kits'],uploads='out/UPLOADS_24M4T.json',upload_list='out/UPLOADS_24M4T.list',optional_uploads='out/UPLOADS_24M4T_GO.json',candidate_uploads='out/UPLOADS_24M4T_CANDIDATE.json',report='out/BUILD24M4T_REPORT.md',validation='work/build24m4y/VALIDATION.json',validation_status='PASS',local_upload_files=up['total_files'],local_upload_bytes=up['total_bytes'],input_members=len(original),unchanged_input_members=len(original)-len(changed),preserved_originals={n:'attic/build24m4y/'+n for n in sorted(changed)},archive_compression='xz; tar auto-detects despite .tar suffix',logical_member_bytes=logical_bytes,GO=False,production_executed=False,uploaded=False,launched=False,bwrap=validation['bwrap'])
extra={'work/build24m4y/PACKAGE_MANIFEST.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode(),'out/DELIVERY_24M4T.json':(json.dumps(delivery,sort_keys=True,indent=2)+'\n').encode()}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),mode=0o644) for n,b in extra.items()}}
print('Packaging '+name+'; '+str(len(expected))+' members; '+str(logical_bytes)+' logical bytes',flush=True)
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
print('Verifying archived bytes, modes and links',flush=True)
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
# Keep the external delivery document identical to the archived document.
(L/'out/DELIVERY_24M4T.json').write_bytes(extra['out/DELIVERY_24M4T.json'])
write(D/'PACKAGE_CHECK.json',dict(status='PASS',package='out/'+name,sha256=h,bytes=size,verified_members=len(expected),all_bytes_modes_links_verified=True,no_input_members_removed=True,superseded_bytes_modes_preserved=True))
# The checksum is the final filesystem write of this build.
target.with_suffix('.tar.sha256').write_text(h+'  '+name+'\n')
print(json.dumps(dict(package='out/'+name,sha256=h,bytes=size,verified_members=len(expected)),indent=2),flush=True)
