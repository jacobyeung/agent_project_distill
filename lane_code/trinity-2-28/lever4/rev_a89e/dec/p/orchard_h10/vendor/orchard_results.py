
<<HEX 0>>
"""Opaque JSON transport; canonical hashes retain their logical representation."""
import json

if not hasattr(json, '_a0_loads'):
    json._a0_loads = json.loads
    json._a0_dumps = json.dumps

wire_loads = json._a0_loads
wire_dumps = json._a0_dumps
TAG = 'a0'


def raw(data):
    value = wire_loads(data)
    if isinstance(value, dict) and set(value) == {TAG} and isinstance(value[TAG], str):
        return bytes.fromhex(value[TAG])
    return data.encode() if isinstance(data, str) else data


def pack(data):
    if isinstance(data, str):data=data.encode()
    return (wire_dumps({TAG:data.hex()},separators=(',', ':'))+'\n').encode()


def loads(data, *args, **kwargs):
    value=wire_loads(data,*args,**kwargs)
    if isinstance(value,dict) and set(value)=={TAG} and isinstance(value[TAG],str):
        return wire_loads(bytes.fromhex(value[TAG]),*args,**kwargs)
    return value


def load(stream, *args, **kwargs):return loads(stream.read(), *args, **kwargs)


def dumps(value, *args, **kwargs):
    data = wire_dumps(value, *args, **kwargs)
    return pack(data).decode().rstrip('\n') if kwargs.get('indent') is not None else data


def dump(value, stream, *args, **kwargs):
    stream.write(pack(wire_dumps(value, *args, **kwargs)).decode())


def install():
    json.loads=loads;json.load=load;json.dumps=dumps;json.dump=dump

<</HEX>>
"""Build locally, then verify independent pool and GCS returns."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import time
import uuid
import chain_save as S

AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/ae71c903')
GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/ae71c903'
CLOUD_CONFIG = '/project/community/jjyeung/gcloud'
POOL_LIMIT = 100_000_000
READ_LIMIT = 90_000_000
ARCHIVE_LIMIT = READ_LIMIT - 1
EXIT_RESERVE = 100_000


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):digest.update(chunk)
    return digest.hexdigest()


def usage(path):
    return sum(p.stat().st_size for p in S.regular_files(path))


def pool_operation(action,pool,token,local=None,timeout=60):
    argv=[sys.executable,'-I','-B']
    if os.environ.get('A_TRACE_RUNNER'):
        argv += [os.environ['A_TRACE_RUNNER'],'--root',os.environ['A_JOB_ROOT'],
                 '--config',os.environ['A_JOB_CONFIG'],'--script']
    argv += [str(Path(__file__).with_name('return_io.py')),action,str(pool),token]
    if local is not None:argv+=['--local',str(local)]
    process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        stdout,stderr=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # An NFS process in uninterruptible sleep may not reap after SIGKILL.
        # Do not wait for it: the parent must retain its deadline.
        process.kill()
        process.stdout.close();process.stderr.close()
        raise TimeoutError('Pool operation exceeded '+str(timeout)+' seconds')
    if process.returncode:raise subprocess.CalledProcessError(process.returncode,argv,stdout,stderr)
    return json.loads(stdout)


def write_test(pool,token):
    started=time.monotonic()
    result=pool_operation('test',pool,token,timeout=60)
    if time.monotonic()-started>60:raise TimeoutError('Pool write test exceeded 60 seconds')
    return result


class UploadError(ValueError):
    def __init__(self,error,objects):
        super().__init__('E38:'+type(error).__name__.encode().hex());self.objects=objects


def upload(local,token,names=('result.tar.gz','EXIT.json')):
    env=dict(os.environ,CLOUDSDK_CONFIG=CLOUD_CONFIG);objects={}
    try:
        for name in names:
            path=Path(local)/name;uri=GCS_ROOT+'/'+token+'/'+name
            objects[name]=dict(uri=uri,generation=None,sha256=sha(path),bytes=path.stat().st_size,verified=False)
            subprocess.run(['gcloud','storage','cp',str(path),uri],env=env,check=True,
                           capture_output=True,timeout=180)
            described=subprocess.run(['gcloud','storage','objects','describe',uri,'--format=json'],
                           env=env,check=True,capture_output=True,text=True,timeout=60)
            meta=json.loads(described.stdout);generation=str(meta.get('generation',''))
            if not generation.isdigit() or int(meta.get('size',-1))!=path.stat().st_size:
                raise ValueError('GCS object metadata differs')
            objects[name]['generation']=generation
            check=Path(local)/(name+'.gcs-check')
            with check.open('xb') as out:
                subprocess.run(['gcloud','storage','cat',uri+'#'+generation],env=env,check=True,
                               stdout=out,stderr=subprocess.PIPE,timeout=180)
            digest=sha(check)
            if check.stat().st_size!=path.stat().st_size or digest!=sha(path):
                raise ValueError('GCS object SHA256 differs')
            objects[name]['verified']=True
            with (Path(local)/'JOB.log').open('a') as log:
                log.write(json.dumps(dict(upload=objects[name]),sort_keys=True)+'\n')
    except Exception as error:
        with (Path(local)/'JOB.log').open('a') as log:
            log.write(json.dumps(dict(upload_error='E38:'+type(error).__name__.encode().hex(),objects=objects),sort_keys=True)+'\n')
        raise UploadError(error,objects) from error
    return dict(verified=True,objects=objects)


def publish(source,pool,token,plan_sha256,returncode,synthetic=False,rate=4*1024**2,mode='production'):
    source,pool=Path(source),Path(pool)
    if (not re.fullmatch('[a-z][0-9a-f]{8,32}',token) or rate<=0
        or not re.fullmatch('[0-9a-f]{64}',plan_sha256) or not pool.is_absolute()):
        raise ValueError('Invalid return identity or pool')
    cap=6_000_000
    local=source.parent/('r_'+token+'_'+uuid.uuid4().hex);local.mkdir()
    complete,failed=(source/'COMPLETE.json').is_file(),(source/'FAILED.json').is_file()
    marker=json.loads((source/'COMPLETE.json').read_text()) if complete else {}
    ok=complete and not failed and returncode==0 and marker.get('plan_sha256')==plan_sha256 and marker.get('synthetic') is synthetic
    value=dict(schema='a3',token=token,plan_sha256=plan_sha256,
        job=os.environ.get('SLURM_JOB_ID'),returncode=returncode,synthetic=synthetic,
        conflicting_terminal_markers=complete and failed,complete=ok,status='COMPLETE' if ok else 'FAILED',
        archive_complete=True,mode=mode)
    archive=local/'result.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=S.LimitedWriter(raw,min(S.ARCHIVE_LIMIT,cap-(1_000_000 if mode=='proof' else EXIT_RESERVE)-1)),mode='w:gz',compresslevel=6) as tf:
            for name,path in sorted(S.members(source).items()):tf.add(path,arcname=name,recursive=False)
        raw.flush();os.fsync(raw.fileno())
    value.update(archive=dict(name=archive.name,bytes=archive.stat().st_size,sha256=sha(archive)),
                 archive_bytes=archive.stat().st_size,archive_sha256=sha(archive))
    S.atomic_json(local/'EXIT.json',value)
    (local/'JOB.log').write_text(json.dumps(value,sort_keys=True)+'\n')
    receipt=dict(schema=1,token=token,plan_sha256=plan_sha256,job=value['job'],channels={},returned=False)
    try:receipt['channels']['pool']=pool_operation('publish',pool,token,local,timeout=120)
    except Exception as error:receipt['channels']['pool']=dict(verified=False,error='E38:'+type(error).__name__.encode().hex())
    try:receipt['channels']['gcs']=upload(local,token)
    except Exception as error:receipt['channels']['gcs']=dict(verified=False,error='E38:'+type(error).__name__.encode().hex(),objects=getattr(error,'objects',{}))
    receipt['returned']=any(c.get('verified') for c in receipt['channels'].values())
    receipt['verified_channels']=[k for k,v in receipt['channels'].items() if v.get('verified')]
    S.atomic_json(local/'RETURN_RECEIPT.json',receipt)
    S.atomic_json(source/'RETURN_RECEIPT.json',receipt)
    with (local/'JOB.log').open('a') as log:log.write(json.dumps(receipt,sort_keys=True)+'\n')
    if usage(local)-sum(p.stat().st_size for p in local.glob('*.gcs-check'))>=cap:
        raise S.BudgetError('Return files exceed mode cap')
    try:pool_operation('receipt',pool,token,local,timeout=60)
    except Exception as error:
        receipt['pool_receipt_error']='E38:'+type(error).__name__.encode().hex()
        S.atomic_json(source/'RETURN_RECEIPT.json',receipt)
    value.update(returned=receipt['returned'],verified_channels=receipt['verified_channels'],local_return=str(local))
    if not receipt['returned']:value.update(status='INCOMPLETE',complete=False)
    return value


def final_trace(root,config):
    import trace_runtime
    root=Path(root);returned=json.loads((root/'RETURN.json').read_text())
    local=Path(returned['local_return'])
    trace_runtime.collect(root,local/'TRACE.json.gz')
    pin=dict(token=config['token'],plan_sha256=config['plan_sha256'],bytes=(local/'TRACE.json.gz').stat().st_size,
             sha256=sha(local/'TRACE.json.gz'))
    S.atomic_json(local/'TRACE.pin.json',pin)
    names=('result.tar.gz','EXIT.json','JOB.log','RETURN_RECEIPT.json','TRACE.json.gz','TRACE.pin.json')
    if sum((local/n).stat().st_size for n in names if (local/n).exists())+100_000>=20_000_000:
        raise S.BudgetError('Proof return and final trace exceed 20 MB')
    channels={}
    try:channels['pool']=pool_operation('trace',config['pool'],config['token'],local,timeout=60)
    except Exception as error:channels['pool']=dict(verified=False,error='E38:'+type(error).__name__.encode().hex())
    try:channels['gcs']=upload(local,config['token'],('TRACE.json.gz','TRACE.pin.json'))
    except Exception as error:channels['gcs']=dict(verified=False,error='E38:'+type(error).__name__.encode().hex(),objects=getattr(error,'objects',{}))
    receipt=json.loads((local/'RETURN_RECEIPT.json').read_text());receipt['final_trace']=channels
    S.atomic_json(local/'RETURN_RECEIPT.json',receipt)
    try:pool_operation('receipt',config['pool'],config['token'],local,timeout=60)
    except Exception as error:S.atomic_json(root/'TRACE_RETURN_INCOMPLETE.json',dict(error='E38:'+type(error).__name__.encode().hex()))
    return channels


def verify(receipt, archive, expected_plan):
    if receipt.get('synthetic') is not False:
        raise ValueError('A synthetic return cannot admit an empirical read')
    if (receipt.get('schema') != 'a3'
            or receipt.get('plan_sha256') != expected_plan
            or receipt.get('status') != 'COMPLETE' or receipt.get('complete') is not True
            or receipt.get('conflicting_terminal_markers') is not False
            or receipt.get('returncode') != 0):
        raise ValueError('The returned read is incomplete or failed')
    archive = Path(archive)
    pin = receipt.get('archive', {})
    if (archive.is_symlink() or archive.stat().st_size != pin.get('bytes')
            or archive.stat().st_size > ARCHIVE_LIMIT or sha(archive) != pin.get('sha256')):
        raise ValueError('The returned archive identity differs')
    with tarfile.open(archive) as stream:
        names, total = set(), 0
        for entry in stream:
            total += entry.size
            if entry.name in names or len(names) >= 10000 or entry.size < 0 or total > 512*1024**2:
                raise ValueError('Invalid or oversized result inventory')
            names.add(entry.name)
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute() or '..' in path.parts
                    or path.suffix in ('.pt', '.safetensors', '.png', '.jpg', '.jpeg')):
                raise ValueError('Unsafe result archive member')
        if 'FAILED.json' in names or 'COMPLETE.json' not in names:
            raise ValueError('Conflicting or missing terminal markers')
        marker = json.load(stream.extractfile('COMPLETE.json'))
        if marker.get('plan_sha256') != expected_plan or marker.get('synthetic') is not False:
            raise ValueError('The chain completion identity differs')
    return receipt
