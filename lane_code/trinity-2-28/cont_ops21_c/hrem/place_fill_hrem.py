"""Place a fresh H remainder and reuse authenticated export parts by hardlink only."""
import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from build_support import read_tar, bundle_of
from return_tools_h import package_info, read, require, canonical
from fetch_validation import digest

HERE=Path(__file__).resolve().parent

def identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)

def link_parts(source,destination,binding):
    source=Path(source);destination=Path(destination)
    fields=[binding['object'],str(binding['archive_bytes']),binding['archive_sha256']]
    require((source/'5').read_text().split()==fields,'Export marker differs')
    require(sum(p['bytes'] for p in binding['parts'])==binding['archive_bytes'],'Part sizes differ')
    handles=[];identities=[];whole=hashlib.sha256()
    try:
        for i,pin in enumerate(binding['parts']):
            fd=os.open(str(source/str(i)),os.O_RDONLY|os.O_NOFOLLOW)
            f=os.fdopen(fd,'rb');handles.append(f);s=os.fstat(f.fileno())
            require(stat.S_ISREG(s.st_mode) and s.st_size==pin['bytes'],'Part type/size differs')
            before=identity(s);h=hashlib.sha256()
            for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk);whole.update(chunk)
            require(identity(os.fstat(f.fileno()))==before and h.hexdigest()==pin['sha256'],'Part changed or hash differs')
            identities.append(before)
        require(whole.hexdigest()==binding['archive_sha256'],'Concatenated archive differs')
        # Retain open descriptors until every source pathname and destination is verified.
        for i,f in enumerate(handles):
            src=source/str(i);dst=destination/str(i);want=identities[i]
            require(identity(os.fstat(f.fileno()))==want and identity(os.lstat(str(src)))==want,'Part identity changed before link')
            os.link(str(src),str(dst),follow_symlinks=False)
            require(identity(os.lstat(str(dst)))==want and identity(os.fstat(f.fileno()))==want,'Linked identity differs')
        for i,f in enumerate(handles):
            require(identity(os.fstat(f.fileno()))==identities[i] and identity(os.lstat(str(source/str(i))))==identities[i] and identity(os.lstat(str(destination/str(i))))==identities[i],'Part changed during linking')
        require((source/'5').read_text().split()==fields,'Export marker changed')
        return identities
    finally:
        for f in handles:f.close()

def run(stage,parent):
    stage=Path(stage).resolve();parent=Path(parent).resolve();r=read(stage/'BUILD.json')['H'];b=read(stage/'binding.json')
    require(str(parent)==r['parent'],'Parent differs from build')
    pi=package_info(parent)
    require(pi['export_binding']==r['export_binding'] and pi['binding']==b,'Parent binding differs')
    require(digest(stage/'binding.json')==r['binding_sha256'],'Binding changed')
    package=Path(r['package']);delivery=stage/'1.tgz'
    require(str(package).startswith('/project/community/jjyeung/okh7/a15_cot_ap'),'Orchard placement namespace required')
    require(digest(delivery)==r['delivery_sha256'],'Delivery differs')
    package.mkdir(mode=0o700)
    seen=set()
    for m,data in read_tar(delivery.read_bytes()):
        n=Path(m.name)
        require(m.isfile() and not n.is_absolute() and '..' not in n.parts and m.name not in seen,'Unsafe delivery')
        seen.add(m.name);p=package/n;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
        p.chmod(m.mode)
    info=package_info(package)
    require(info['plan']==r['plan_sha256'] and info['items_sha256']==r['items_sha256'],'Placed package differs')
    bundle=dict((m.name,d) for m,d in read_tar(bundle_of((package/'BATCH.sh').read_bytes())[1]))
    require(bundle['0.json']==(package/'0.json').read_bytes() and bundle['7.py']==(package/'a/6.py').read_bytes(),'Batch bundle differs')
    reuse=Path(os.environ['REUSE_PARTS_FROM'])
    require(reuse.resolve()==parent/'a/e','Reuse must be parent/a/e')
    e=package/'a/e';e.mkdir(mode=0o700)
    for key,n in [('config','7'),('receipt','8'),('data_receipt','9')]:
        raw=(reuse/n).read_bytes();require(hashlib.sha256(raw).hexdigest()==b['preparation_sha256'][key],'Preparation differs')
        (e/n).write_bytes(raw)
    identities=link_parts(reuse,e,b);(e/'5').write_bytes((reuse/'5').read_bytes())
    cmd=['/usr/bin/python3','-I','-s','-B',str(package/'a/4.py'),'--parts']+[str(e/str(i)) for i in range(len(b['parts']))]
    cmd+=['--done',str(e/'5'),'--object',b['object'],'--config',str(e/'7'),'--receipt',str(e/'8'),'--data-receipt',str(e/'9'),
          '--lineage',b['lineage'],'--step',str(b['step']),'--out',str(package/'a/export.json'),'--prep-tar',str(package/'a/6'),
          '--base-inputs',str(package/'a/0.json'),'--inputs-out',str(package/'a/1.json')]
    subprocess.run(cmd,check=True)
    for i,want in enumerate(identities):require(identity(os.lstat(str(e/str(i))))==want,'Part changed during fill')
    # Existing dry-run enforces all unchanged model, tower and non-export archives.
    with (stage/'dry_H.json').open('x') as out:
        subprocess.run(['/usr/bin/python3','-I','-s','-B',str(HERE/'dryres_h.py'),str(package/'a/1.json'),str(package/'a/0.json'),digest(package/'a/6')],stdout=out,check=True)
    subprocess.run(['/usr/bin/python3','-I','-s','-B','3.py','check','--gpus','1','--time',r['walltime']],cwd=str(package),env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),check=True)
    (package/'a/10.json').write_text(json.dumps(dict(passed=True,inputs_sha256=digest(package/'a/1.json'),export_sha256=digest(package/'a/export.json')))+'\n')
    (package/'a/1.txt').write_text('0\n')
    print(json.dumps(dict(package=str(package),walltime=r['walltime'],submitted=False)))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',required=True);p.add_argument('--parent',required=True);a=p.parse_args();run(a.stage,a.parent)
