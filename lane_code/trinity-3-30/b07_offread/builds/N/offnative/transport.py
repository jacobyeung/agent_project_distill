"""Opaque packets and authenticated returns; transfer policy belongs to build R."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import zlib
from .io import dump, load, sha, tar_bytes, extract, owned, digest
from .paths import r_launcher

FORBIDDEN=('trinity','/scratch/jjyeung','/data2/','/data3/','revsi','vsibench','vsi-bench',
           'scannet','scannetpp','arkitscenes','matterport','qwen','sam3','sam 3','g3t',
           'harness','nomdg','leg-s1','e2e_reader','offnative','student_pilot','orch_n30')


def inventory(raw):
    lower=raw.lower()
    found=[word for word in FORBIDDEN if word.encode() in lower]
    if found:raise ValueError('packet names leaked: '+','.join(found))
    return {'passed':True,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
            'checked':list(FORBIDDEN)}


def packet(files, destination, token):
    """Hide internal names in a verified opaque body, as in R's embedded packet."""
    if not re.fullmatch('[a-f][0-9a-f]{23}',token):raise ValueError('invalid opaque token')
    destination=owned(destination)
    raw=tar_bytes(files)
    body=zlib.compress(raw,9).hex().encode()
    checksum=hashlib.sha256(body).hexdigest()
    # All human-readable internal paths reside inside the encoded body.
    boot='''#!/bin/bash
set -euo pipefail
exec python3 -I -s -B - "$0" <<'P0'
import hashlib,io,os,sys,tarfile,zlib
from pathlib import Path,PurePosixPath
p=Path(sys.argv[1]).parent
b=(p/'0').read_bytes()
if hashlib.sha256(b).hexdigest()!=%r: raise ValueError('X0')
r=Path('/tmp')/('a'+%r+'_'+os.environ.get('SLURM_JOB_ID','0'))
r.mkdir(mode=0o700)
n=set();total=0
with tarfile.open(fileobj=io.BytesIO(zlib.decompress(bytes.fromhex(b.decode())))) as a:
 for m in a:
  q=PurePosixPath(m.name);total+=m.size
  if not m.isfile() or q.is_absolute() or '..' in q.parts or m.name in n or total>134217728: raise ValueError('X1')
  n.add(m.name);t=r/m.name;t.parent.mkdir(parents=True,exist_ok=True)
  with t.open('xb') as o:o.write(a.extractfile(m).read())
os.chdir(r)
os.execv(sys.executable,[sys.executable,'-B','0.py'])
P0
'''%(checksum,token)
    packed=tar_bytes({'0':body,'1.sh':boot.encode()})
    check=inventory(packed)
    destination.write_bytes(packed)
    dump(destination.with_suffix('.inventory.json'),check)
    return check


def submission_argv(config, script):
    if not re.fullmatch('a15_cot_ap[0-9a-f]{16}',config['job_name']):raise ValueError('invalid job name')
    return ['sbatch','--parsable','--job-name='+config['job_name'],'--partition=general',
            '--gres=gpu:1','--cpus-per-task=16','--mem=200G','--output=/dev/null',
            '--time='+str((config['job']['time_limit_s']+59)//60),str(script)]


def authenticate(destination, receipt, archive):
    """Match the submitted job, token, config, binding, and whole archive identity."""
    d=Path(destination);config=load(d/'CONFIG.json');submission=load(d/'SUBMISSION.json')
    if (submission.get('status')!='SUBMITTED' or submission.get('config_sha256')!=sha(d/'CONFIG.json') or
            submission.get('packet_sha256')!=sha(d/'packet.tar')):
        raise ValueError('submission identity differs')
    expected={'token':config['token'],'job':submission['job'],'config_sha256':sha(d/'CONFIG.json'),
              'binding_sha256':config['x0'],'packet_sha256':sha(d/'packet.tar')}
    if any(receipt.get(k)!=v for k,v in expected.items()):raise ValueError('return identity differs')
    if receipt.get('status')!='COMPLETE' or receipt.get('synthetic') is not False:
        raise ValueError('return is synthetic or incomplete')
    p=Path(archive);ap=receipt.get('archive',{})
    if p.is_symlink() or p.stat().st_size!=ap.get('bytes') or p.stat().st_size>90_000_000 or sha(p)!=ap.get('sha256'):
        raise ValueError('return archive identity differs')
    # Reuse R's full member and completion validation with our config identity as its plan.
    L=r_launcher().launcher('revsi999t32')
    import orchard_results
    translated=dict(receipt,schema='evalx-orchard-result-return-v1',plan_sha256=expected['config_sha256'],
                    complete=True,conflicting_terminal_markers=False,returncode=0)
    orchard_results.verify(translated,p,expected['config_sha256'])
    return expected


def fetch_remote(destination, *, channel='pool'):
    """No retry or channel failover after a failed governed stream."""
    from .cli import governed_transfer
    d=owned(destination);c=load(d/'CONFIG.json');s=load(d/'SUBMISSION.json')
    if s.get('status')!='SUBMITTED':raise ValueError('missing recorded submission')
    L=r_launcher().launcher('revsi999t32')
    base=c['pool']+'/'+c['token'] if channel=='pool' else c['gcs'].rstrip('/')
    def command(name, cap):
        if channel=='gcs':return ['gcloud','storage','cat',base+'/'+name]
        code="import sys;from pathlib import Path;p=Path(sys.argv[1]);assert not p.is_symlink() and p.stat().st_size<=int(sys.argv[2]);sys.stdout.buffer.write(p.read_bytes())"
        return ['python3','-I','-B','-c',code,base+'/'+name,str(cap)]
    target=d/'incoming';target.mkdir(exist_ok=False)
    for name,cap in [('EXIT.json',16384),('result.tar.gz',90_000_000)]:
        if name!='EXIT.json':
            rec=load(target/'EXIT.json')
            if (rec.get('token')!=c['token'] or rec.get('job')!=s['job'] or
                    rec.get('config_sha256')!=sha(d/'CONFIG.json')):
                raise ValueError('remote receipt names another submission')
            cap=rec.get('archive',{}).get('bytes')
            if type(cap)!=int or not 0<cap<=90_000_000:raise ValueError('unbounded return')
        argv=L.SSH+[shlex.join(command(name,cap))]
        with (target/name).open('xb') as output,(target/(name+'.log')).open('xb') as errors:
            governed_transfer(argv,output,errors,cap,c['token']+('a' if name=='EXIT.json' else 'b'))
        if (target/name).stat().st_size>cap:raise ValueError('remote object exceeds bound')
    authenticate(d,load(target/'EXIT.json'),target/'result.tar.gz')
    extract(target/'result.tar.gz',d/'fetched')
    return {'fetched':str(d/'fetched')}


def publish(config,local):
    """Use R's independently verified pool and generation-pinned GCS channels."""
    r_launcher().launcher('revsi999t32')
    import orchard_results as R
    local=Path(local)
    R.GCS_ROOT=config['gcs'].rstrip('/').rsplit('/',1)[0]
    channels={}
    for name,operation in (
        ('pool',lambda:R.pool_operation('publish',config['pool'],config['token'],local,timeout=120)),
        ('gcs',lambda:R.upload(local,config['token']))):
        try:channels[name]=operation()
        except Exception as exc:channels[name]={'verified':False,'error_hex':str(exc).encode().hex()}
    result={'channels':channels,'returned':any(v.get('verified') for v in channels.values())}
    dump(local/'RETURN_RECEIPT.json',result)
    return result
