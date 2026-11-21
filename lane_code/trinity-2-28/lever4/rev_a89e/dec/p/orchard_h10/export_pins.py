
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
"""Authenticate the operator's export identity before staging any archives."""
import hashlib
import json
from pathlib import Path
import re


MEMBERS = dict(artifact='artifact.json', heads='heads.pt',
               full_weights='full_weights/full_weights.json')
PREPARATION = ('config', 'receipt', 'data_receipt')


def relative(value):
    p = Path(value)
    if not value or p.is_absolute() or '..' in p.parts or str(p) != value or value == '.':
        raise ValueError('Export path must be canonical and relative')
    return p


def pin(value):
    if (not isinstance(value, dict) or not isinstance(value.get('sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', value['sha256'])
            or type(value.get('bytes')) is not int or value['bytes'] <= 0):
        raise ValueError('Invalid export pin')


def validate(value):
    if value.get('schema') != 'h1-export-pins-v1':
        raise ValueError('Export pin schema differs')
    relative(value['member_directory'])
    if (value.get('lineage') not in ('SFT', 'RL') or type(value.get('step')) is not int
            or value['step'] < 0):
        raise ValueError('Export requires SFT/RL and nonnegative integer step')
    for name in MEMBERS:
        pin(value[name])
    if set(value['preparation']) != set(PREPARATION):
        raise ValueError('Preparation keys differ')
    paths = []
    for name in PREPARATION:
        item = value['preparation'][name]
        pin(item); paths.append(relative(item['path']))
        source = Path(item['source_path'])
        if not source.is_absolute() or '..' in source.parts or str(source) != item['source_path']:
            raise ValueError('Preparation source path differs')
    if len(set(paths)) != len(paths):
        raise ValueError('Preparation paths must be distinct')
    return value


def load(inputs, package):
    spec = inputs['export_pin']
    pin(spec)
    if spec.get('path') != 'a/export.json':
        raise ValueError('Require a/export.json')
    path = Path(package)/spec['path']
    raw = path.read_bytes()
    if len(raw) != spec['bytes'] or hashlib.sha256(raw).hexdigest() != spec['sha256']:
        raise ValueError('Export pin file differs')
    return validate(json.loads(raw))


def admit(inputs, cfg, export):
    root = Path(cfg['logical'])/'d'/export['member_directory']
    for name, member in MEMBERS.items():
        declared = inputs['files'][name]
        if (type(declared.get('bytes')) is not int
                or any(declared[key] != export[name][key] for key in ('sha256', 'bytes'))):
            raise ValueError('Export pin differs: '+name)
        if declared['path'] != str(root/member):
            raise ValueError('Export member path differs: '+name)
