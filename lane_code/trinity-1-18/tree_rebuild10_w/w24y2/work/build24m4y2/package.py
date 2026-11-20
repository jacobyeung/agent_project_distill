from pathlib import Path
import hashlib, io, json, os, resource, shutil, stat, tarfile
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
L=Path.cwd();D=L/'work/build24m4y2'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
validation=json.loads((D/'VALIDATION.json').read_bytes());assert validation['status']=='PASS'
assert shutil.disk_usage(L).free>100*1024**3
excluded={'work/build24m4y2/PACKAGE_MANIFEST.json','work/build24m4y2/PACKAGE_CHECK.json','out/DELIVERY_24M4Y2.json'}
files={};paths={};cache={}
print('Inventorying package',flush=True)
for root in ('out','work','attic'):
    for directory,dirs,names in os.walk(L/root,followlinks=False):
        for name in dirs+names:
            p=Path(directory)/name;s=p.lstat()
            if stat.S_ISDIR(s.st_mode):continue
            n=str(p.relative_to(L))
            if n in excluded or n.startswith('out/tree_rebuild_b24m4y2_'):continue
            if stat.S_ISLNK(s.st_mode):v=dict(type='symlink',target=os.readlink(p),mode=s.st_mode&511)
            else:
                assert stat.S_ISREG(s.st_mode),(n,s.st_mode)
                key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
                if key not in cache:cache[key]=sha(p)
                v=dict(type='file',sha256=cache[key],bytes=s.st_size,mode=s.st_mode&511)
            files[n]=v;paths[n]=p
original=json.loads((L/'work/build24m4x2/PACKAGE_MANIFEST.json').read_bytes())['files']
assert not set(original)-set(files)
changed=[n for n,v in original.items() if files[n]!=v]
assert set(changed)=={'out/rcj/'+n for n in ('x.py','nd.py','ch.py','f.json')},changed
for n in changed:assert files['attic/build24m4y2/'+n]==original[n]
seal=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
name='tree_rebuild_b24m4y2_'+seal[:8]+'.tar';target=L/'out'/name;assert not target.exists()
manifest=dict(schema='build24m4y2-package-v1',package_seal=seal,files=files,
    seal_domain='out, work, attic except final package files, this manifest, delivery and package check')
delivery=dict(schema='build24m4y2-delivery-v1',package='out/'+name,package_seal=seal,
    tree_sha256=validation['tree_sha256'],kits=validation['kits'],rcj=validation['rcj'],
    uploads='out/UPLOADS_24M4Y2.json',optional_uploads='out/UPLOADS_24M4Y2_GO.json',
    report='out/BUILD24M4Y2_REPORT.md',validation='work/build24m4y2/VALIDATION.json',
    checks_status='PASS',production_executed=False,uploaded=False,launched=False,GO=False,
    archive_compression='xz',logical_member_bytes=sum(v.get('bytes',0) for v in files.values()))
extra={'work/build24m4y2/PACKAGE_MANIFEST.json':raw(manifest),'out/DELIVERY_24M4Y2.json':raw(delivery)}
expected={**files,**{n:dict(type='file',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),mode=0o644) for n,b in extra.items()}}
print('Packing',name,'members',len(expected),'unique bytes',sum(v['bytes'] for v in { (v.get('sha256'),v['mode']):v for v in files.values() if v['type']=='file'}.values()),flush=True)
seen={}
with tarfile.open(target,'w:xz',preset=3) as tar:
    for n,v in sorted(expected.items()):
        m=tarfile.TarInfo(n);m.mode=v['mode'];m.mtime=0
        if v['type']=='symlink':m.type=tarfile.SYMTYPE;m.linkname=v['target'];tar.addfile(m);continue
        key=(v['sha256'],v['mode'])
        if key in seen:m.type=tarfile.LNKTYPE;m.linkname=seen[key];tar.addfile(m);continue
        seen[key]=n;m.size=v['bytes']
        if n in extra:tar.addfile(m,io.BytesIO(extra[n]))
        else:
            with paths[n].open('rb') as f:tar.addfile(m,f)
print('Verifying every archived byte, mode and link',flush=True)
actual={}
with tarfile.open(target,'r|*') as tar:
    for m in tar:
        if m.issym():v=dict(type='symlink',target=m.linkname,mode=m.mode)
        elif m.islnk():v=dict(actual[m.linkname],mode=m.mode)
        else:
            assert m.isfile();h=hashlib.sha256();size=0
            with tar.extractfile(m) as f:
                for b in iter(lambda:f.read(1<<20),b''):h.update(b);size+=len(b)
            v=dict(type='file',sha256=h.hexdigest(),bytes=size,mode=m.mode)
        assert m.name not in actual;actual[m.name]=v
assert actual==expected
for n,b in extra.items():(L/n).write_bytes(b)
h=sha(target);size=target.stat().st_size
(D/'PACKAGE_CHECK.json').write_bytes(raw(dict(status='PASS',package='out/'+name,sha256=h,bytes=size,
    verified_members=len(expected),all_bytes_modes_links_verified=True,no_input_members_removed=True,
    changed_inherited_members=changed,superseded_helpers_preserved=True)))
print(json.dumps(dict(package='out/'+name,sha256=h,bytes=size,verified_members=len(expected)),indent=2),flush=True)
# The checksum is deliberately the final filesystem write.
target.with_suffix('.tar.sha256').write_text(h+'  '+name+'\n')
