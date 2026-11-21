
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
"""Authenticate return provenance before copying any return; Python 3.6 stdlib."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_exit(receipt, archive, plan, token):
    if receipt.get('plan_sha256') != plan:
        raise ValueError('Return plan differs')
    if receipt.get('token') != token:
        raise ValueError('Return token differs')
    if receipt.get('synthetic') is not False:
        raise ValueError('Synthetic return refused')
    size = receipt.get('archive_bytes')
    if type(size) is not int or not 0 < size < 90000000 or Path(archive).stat().st_size != size:
        raise ValueError('Return byte count differs')
    if receipt.get('archive_sha256') != digest(archive):
        raise ValueError('Return archive digest differs')
    if type(receipt.get('complete')) is not bool or receipt.get('status') != ('COMPLETE' if receipt['complete'] else 'FAILED'):
        raise ValueError('Return completion status differs')


def validate_receipt(receipt, exit_value, exit_path, archive, plan, token):
    if receipt.get('plan_sha256') != plan or receipt.get('token') != token:
        raise ValueError('Return receipt provenance differs')
    if receipt.get('job') != exit_value.get('job') or receipt.get('returned') is not True:
        raise ValueError('Return receipt job/status differs')
    pool = receipt.get('channels', {}).get('pool', {})
    if pool.get('verified') is not True:
        raise ValueError('Return pool is unverified')
    for name, path in [('EXIT.json', exit_path), ('result.tar.gz', archive)]:
        pin = pool.get('files', {}).get(name, {})
        if pin.get('sha256') != digest(path) or pin.get('bytes') != Path(path).stat().st_size:
            raise ValueError('Return receipt file differs: '+name)

