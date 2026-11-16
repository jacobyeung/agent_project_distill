"""Bounded publication with readback; local transport is the rehearsal substitute."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
from guard_core import read, sha, write, verify_archive

LIMIT = 300_000_000

def regular_tar(path, limit=32*1024*1024):
    path=Path(path)
    if path.stat().st_size>limit: raise ValueError('Archive byte limit exceeded')
    names=set(); total=0
    with tarfile.open(path,'r:*') as archive:
        for m in archive:
            p=PurePosixPath(m.name);total+=m.size
            if (not m.isfile() or p.is_absolute() or '..' in p.parts or not p.parts
                    or str(p) in names or total>limit or len(names)>=10000):
                raise ValueError('Archive needs bounded unique relative regular members; no links')
            names.add(str(p))
    return True

def extract(path,destination,limit=32*1024*1024):
    regular_tar(path,limit);destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    with tarfile.open(path,'r:*') as archive:
        for m in archive:
            target=destination/m.name;target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(m) as inp,target.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
            target.chmod(m.mode&0o755)

def copy_verified(source,dest):
    source,dest=Path(source),Path(dest)
    if source.is_symlink() or not source.is_file():raise ValueError('Source must be regular')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as inp,dest.open('xb') as out:
        shutil.copyfileobj(inp,out,1024*1024);out.flush();os.fsync(out.fileno())
    if dest.stat().st_size!=source.stat().st_size or sha(dest)!=sha(source):raise ValueError('Transport readback differs')
    return dict(bytes=dest.stat().st_size,sha256=sha(dest))

class Publisher:
    def __init__(self,config,token,work):
        if not re.fullmatch('[a-f0-9]{16}',token):raise ValueError('Invalid publication token')
        self.config,self.token,self.work=config,token,Path(work)
        self.work.mkdir(parents=True,exist_ok=True)
    def __call__(self,path):
        path=Path(path)
        if path.stat().st_size>LIMIT:raise ValueError('Publication exceeds return limit')
        if path.name not in ('PROOF.json','CANARY.json','result.tar.gz','EXIT.json','FAILED.json'):
            raise ValueError('Unregistered publication member')
        if self.config['kind']=='local':
            dest=Path(self.config['root'])/self.token/path.name
            value=copy_verified(path,dest);value.update(uri=str(dest),verified=True)
        elif self.config['kind']=='gcs':
            prefix=self.config['prefix']
            if not re.fullmatch(r'gs://cmu-gpucloud-jjyeung/q8/[a-f0-9]+',prefix):raise ValueError('Invalid return prefix')
            uri=prefix+'/'+self.token+'/'+path.name
            env=dict(os.environ,CLOUDSDK_CONFIG=self.config['credentials'])
            subprocess.run(['/usr/bin/gcloud','storage','cp',str(path),uri,'--if-generation-match=0'],env=env,check=True,timeout=180,capture_output=True)
            result=subprocess.run(['/usr/bin/gcloud','storage','objects','describe',uri,'--format=json'],env=env,check=True,timeout=60,capture_output=True,text=True)
            meta=json.loads(result.stdout);generation=str(meta.get('generation',''))
            if not generation.isdigit() or int(meta.get('size',-1))!=path.stat().st_size:raise ValueError('Published object metadata differs')
            target=self.work/(path.name+'.readback')
            with target.open('xb') as output:
                subprocess.run(['/usr/bin/gcloud','storage','cat',uri+'#'+generation],env=env,check=True,timeout=180,stdout=output,stderr=subprocess.PIPE)
            if sha(target)!=sha(path) or target.stat().st_size!=path.stat().st_size:raise ValueError('Published object readback differs')
            value=dict(uri=uri,generation=generation,sha256=sha(path),bytes=path.stat().st_size,verified=True)
        else:raise ValueError('Unknown publication transport')
        write(self.work/(path.name+'.published.json'),value)
        return value

def archive_result(source,output,plan,fixture=False,error=None):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=False)
    total=0
    with tarfile.open(output/'result.tar.gz','w:gz',dereference=True) as archive:
        for p in sorted(source.rglob('*')):
            if p.is_symlink():raise ValueError('Return contains a link')
            if not p.is_file() or p.suffix in ('.pt','.safetensors','.png','.jpg','.npz'):continue
            total+=p.stat().st_size
            if total>LIMIT:raise ValueError('Return expansion exceeds limit')
            m=archive.gettarinfo(str(p),arcname=str(p.relative_to(source)))
            m.uid=m.gid=m.mtime=0;m.uname=m.gname=''
            with p.open('rb') as inp:archive.addfile(m,inp)
    path=output/'result.tar.gz';regular_tar(path,LIMIT)
    receipt=dict(schema='g2-return-v1',plan_sha256=plan,fixture=fixture,status='FAIL' if error else 'PASS',error=error,
                 archive=dict(bytes=path.stat().st_size,sha256=sha(path)))
    write(output/'EXIT.json',receipt);return receipt

def verify_return(receipt,archive,plan,allow_fixture=False):
    if (receipt.get('schema')!='g2-return-v1' or receipt.get('plan_sha256')!=plan
            or receipt.get('status')!='PASS' or (receipt.get('fixture') is not False and not allow_fixture)):
        raise ValueError('Return identity, status or authority differs')
    verify_archive(archive,receipt['archive']);regular_tar(archive,LIMIT)
    with tarfile.open(archive) as tar:
        names=set(tar.getnames())
        if not {'COMPLETE.json','PROOF.json','CANARY.json','R1.json','IN_JOB_ADMISSION.json'}<=names or 'FAILED.json' in names:
            raise ValueError('Return is missing terminal evidence')
        for name in ('PROOF.json','CANARY.json','IN_JOB_ADMISSION.json'):
            if json.load(tar.extractfile(name)).get('status')!='PASS':raise ValueError('Return phase did not pass')
        marker=json.load(tar.extractfile('COMPLETE.json'))
        if marker.get('plan_sha256')!=plan:raise ValueError('Return completion plan differs')
    return receipt
