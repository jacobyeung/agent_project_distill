
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
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
with tarfile.open(p/'0.tgz') as archive:
    sizes=__import__('re').findall(r'(?m)^WRITE_TEST_BYTES = (\d+)$',archive.extractfile('orchard_h10/vendor/return_io.py').read().decode())
assert len(sizes)==1,dict(check='Sealed write-test size',expected=1,found=sizes)
assert type(w['bytes']) is int and w['bytes']==int(sizes[0]),dict(check='Write-test receipt differs',expected=int(sizes[0]),found=w['bytes'])
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
import runpy
op=runpy.run_path(str(p/'a/6.py'))
assert op['COUNTS']==(0,0,0,150,0) and op['SCHEDULE']==((0,3),)
assert m==op['memory_bound']()
u=c['real_unit']
assert c['real_unit_passed'] is True and u['passed'] is True and u['mode']=='cpu' and u['status']=='complete',dict(check='CPU real unit',status=u.get('status'),error=u.get('error'))
assert [x['name'] for x in u['stages']]==['bind','first_model','load','prefill','record'],dict(check='CPU real unit stages',found=[x['name'] for x in u['stages']])
assert u['stages'][2]['step']==544 and 'torch.bfloat16' in u['stages'][2]['dtypes'] and u['stages'][2]['locations']==['cpu']
k=u['checks']
assert k['clean'] is True and k['grid']['shape']==[32,51,51] and k['grid']['dtype']=='float16' and k['grid']['finite'] is True
assert k['scale']['finite'] is True and k['scale']['value']>0 and k['K']['finite'] is True and k['prefills']==1 and k['decode_steps']==0
assert u['failure'] is None and u['completed']==1 and u['admission']['reason'] in ('first_unit','time_guard','over_budget')
assert u['environment']['threads']==u['unit']['threads']>=1 and u['environment']['cuda_visible']==''
r=u['process']
assert r['returncode']==0 and r['stopped'] is None and r['memory']['over'] is False and r['action']==3
print('All CPU receipt checks passed')