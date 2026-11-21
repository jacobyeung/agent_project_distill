
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
import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
import sys
if len(sys.argv)>1 and sys.argv[1] in ('check','submit'):
    for flag,value in (('--gpus','1'),('--time','00:50:00')):
        matches=[i for i,x in enumerate(sys.argv) if x==flag or x.startswith(flag+'=')]
        if not matches:sys.argv.extend([flag,value]);continue
        if len(matches)!=1:raise ValueError('duplicate '+flag)
        i=matches[0];got=sys.argv[i].split('=',1)[1] if '=' in sys.argv[i] else sys.argv[i+1]
        if got!=value:raise ValueError('requires '+flag+' '+value)
with tarfile.open(p/'0.tgz') as t:
    try:exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
    except Exception as e:
        print('E41:'+type(e).__name__.encode().hex())
        raise SystemExit(1)
