
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

<<HEX 0>>
"""Reserve cumulative package metadata writes before forwarding each write."""
import builtins
import fcntl
import io
import os

LIMIT=2_000_000
TOKEN='TOKEN'
PREFIX='/project/community/jjyeung/'+TOKEN+'/'
_original=builtins.open


def charge(size):
    # Fixed-width accounting includes its own writes; failed writes stay charged.
    with _original(os.open(PREFIX+'a/18',os.O_RDWR|os.O_CREAT,0o600), 'r+b', buffering=0) as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        lock.seek(0); raw=lock.read(32);used=int(raw or b'0')
        cost=size+32
        if used+cost>LIMIT:raise OSError('E70')
        lock.seek(0);lock.write(('%032d'%(used+cost)).encode());os.fsync(lock.fileno())


class Writer:
    def __init__(self,stream):self.stream=stream
    def write(self,data):
        charge(len(data.encode(self.stream.encoding or 'utf-8')) if isinstance(data,str) else len(data))
        return self.stream.write(data)
    def writelines(self,lines):
        for line in lines:self.write(line)
    def __getattr__(self,name):return getattr(self.stream,name)
    def __enter__(self):return self
    def __exit__(self,*args):return self.stream.__exit__(*args)


def install():
    if getattr(builtins.open,'_a18',False):return
    io_open=io.open
    def wrap(original):
        def opened(file,mode='r',*args,**kwargs):
            path=os.path.abspath(os.fspath(file)) if not isinstance(file,int) else ''
            watched=path.startswith(PREFIX) and not path.startswith(PREFIX+'a/f/') and any(x in mode for x in 'wax+')
            if watched:charge(0)
            stream=original(file,mode,*args,**kwargs)
            return Writer(stream) if watched else stream
        opened._a18=True
        return opened
    builtins.open=wrap(_original);io.open=wrap(io_open)

<</HEX>>
"""Standalone package checker and explicit operator-only submit/fetch commands."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import types


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load_helpers(package):
    # Load three small pinned modules in memory; never expand the code tree on login.
    public=json.loads((package/'0.json').read_text())
    if digest(package/'0.tgz')!=public['payload_sha256']:raise ValueError('Code archive differs')
    mod=types.ModuleType('orchard_h10');mod.__path__=[];sys.modules['orchard_h10']=mod
    with tarfile.open(package/'0.tgz') as archive:
        cfg={**json.load(archive.extractfile('9.json')),**public}
        for name in ('common','export_pins','job'):
            path='orchard_h10/'+name+'.py';raw=archive.extractfile(path).read()
            if hashlib.sha256(raw).hexdigest()!=cfg['payload_pins'][path]['sha256']:raise ValueError('Helper differs')
            m=types.ModuleType('orchard_h10.'+name);m.__file__=path;sys.modules[m.__name__]=m
            exec(compile(raw,path,'exec'),m.__dict__)
    from orchard_h10.job import verify_config
    verify_config(cfg)
    return cfg


def check(package, gpus, walltime):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque, submit_argv
    from orchard_h10.job import check_inputs
    receipt=json.loads((package/'PACKAGE.json').read_text())
    for name,h in receipt['files'].items():
        if digest(package/name)!=h:raise ValueError('Package changed: '+name)
    if package!=Path('/project/community/jjyeung')/cfg['token']:
        raise ValueError('Stage the package under /project/community/jjyeung/'+cfg['token'])
    private=package/'a';private.mkdir(mode=0o700,exist_ok=True)
    if private.stat().st_mode & 0o077:raise ValueError('Private input directory must be 0700')
    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg,package=package)
    opaque([str(package),str(package/'1.json'),str(package/'2.json')])
    for a in inputs['archives']:
        for part in a['parts']:
            opaque([part['path']])
            if Path(part['path']).stat().st_size!=part['bytes']:raise ValueError('Staged input size differs')
    # This is a metadata CPU check. Full hashes, imports, restore, and frame admission
    # execute on the allocated node after archive extraction, before a model decode.
    argv=submit_argv(cfg['token'],gpus,walltime)
    value=dict(passed=True,plan=cfg['plan_sha256'],inputs=digest(package/'a/1.json'),
               package=digest(package/'PACKAGE.json'),gpus=gpus,time=walltime,argv=argv,
               scope=0)
    (package/'2.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return value


def submit(package,gpus,walltime,test_only=False,cpu_only=False):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque, submit_argv, seconds
    cpu=json.loads((package/'2.json').read_text())
    if (cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=digest(package/'a/1.json') or
            cpu.get('package')!=digest(package/'PACKAGE.json') or cpu.get('gpus')!=gpus or cpu.get('time')!=walltime):
        raise ValueError('Run the CPU check for these exact inputs, card count and time first')
    from orchard_h10.job import check_inputs
    check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
    argv=submit_argv(cfg['token'],gpus,walltime)
    if cpu_only:argv=[a for a in argv if not a.startswith('--gres=')]
    opaque(argv)
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':os.environ['HOME'],'USER':os.environ['USER']}
    opaque([f'{k}={v}' for k,v in env.items()])
    body=(package/'BATCH.sh').read_bytes()
    # Check retained package pins again; no implicit check+submit retry chain.
    pins=json.loads((package/'PACKAGE.json').read_text())['files']
    if any(digest(package/n)!=h for n,h in pins.items()):raise ValueError('Package changed after check')
    import runpy
    bounded_submit=runpy.run_path(str(package/'a/27.py'))['submit']
    result=bounded_submit(package/'a',argv+(['--test-only'] if test_only else []),input=body,env=env,cwd='/tmp',capture_output=True)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    with (package/'LEDGER.jsonl').open('a') as f:
        f.write(json.dumps(dict(action='test-only' if test_only else 'submit',returncode=result.returncode,
                  stdout=result.stdout.decode(),stderr=result.stderr.decode(),argv=argv,plan=cfg['plan_sha256']))+'\n')
        f.flush();os.fsync(f.fileno())
    return result.returncode


def fetch(package,token,destination):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque
    import re
    if not re.fullmatch(re.escape(cfg['token'])+'[0-9a-f]{8}',token):raise ValueError('Return token differs')
    source=Path(cfg['pool'])/token;destination=Path(destination).resolve()
    opaque([token,str(destination)])
    destination.mkdir(parents=True,exist_ok=False)
    # Reuse the template's framed stream locally on Orchard. An operator can pipe
    # this same emit command through the governed transport to Trinity instead.
    with tarfile.open(package/'0.tgz') as archive:
        raw=archive.extractfile('orchard_h10/vendor/stdout_transfer.py').read()
    m=types.ModuleType('stdout_transfer');exec(compile(raw,'stdout_transfer.py','exec'),m.__dict__)
    exit_value=json.loads((source/'EXIT.json').read_text())
    result=source/'result.tar.gz'
    if digest(result)!=exit_value['archive_sha256']:raise ValueError('Returned archive differs')
    # The return limit is 90 MB, so the stream stays bounded. Do not load it in memory.
    if result.stat().st_size>5_900_000:raise ValueError('E71')
    if sum((source/n).stat().st_size for n in ('EXIT.json','RETURN_RECEIPT.json'))>100_000:raise ValueError('E71')
    # One-shot destination: framing + archive + receipts fit the 20 MB slot.
    transfer=destination/'0.stream'
    with transfer.open('xb') as out:m.emit(result,out,cfg['plan_sha256'],'complete' if exit_value['complete'] else 'failed')
    with transfer.open('rb') as stream,(destination/'0.log').open('wb') as log:
        m.receive(stream,destination/'0.tgz',cfg['plan_sha256'],log)
    for name in ('EXIT.json','RETURN_RECEIPT.json'):
        (destination/name).write_bytes((source/name).read_bytes())
    print(json.dumps(dict(destination=str(destination),complete=exit_value['complete'],sha256=digest(destination/'0.tgz'))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('check','submit','fetch'))
    p.add_argument('--gpus',type=int,default=4);p.add_argument('--time');p.add_argument('--test-only',action='store_true')
    p.add_argument('--cpu-only',action='store_true');p.add_argument('--return-token');p.add_argument('--out');a=p.parse_args();root=Path(__file__).resolve().parent
    if a.action=='check':print(json.dumps(check(root,a.gpus,a.time),sort_keys=True))
    elif a.action=='submit':raise SystemExit(submit(root,a.gpus,a.time,a.test_only,a.cpu_only))
    else:fetch(root,a.return_token,a.out)
