
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
"""Authenticate code early and materialize only the current capture's RGB."""
import hashlib
import json
from pathlib import Path, PurePosixPath


def preflight(package):
    # This runs before copying any environment, model or RGB archive.
    package=Path(package)
    mapping=json.loads((package/'l.json').read_text())
    entries=[(bytes.fromhex(name).decode(),package/physical)
             for view in mapping['views'].values() for physical,name in view.items()]
    digest=hashlib.sha256()
    for name,path in sorted(entries):
        raw=path.read_bytes()
        compile(raw,str(path),'exec')
        digest.update(f'{name}\0{hashlib.sha256(raw).hexdigest()}\n'.encode())
    if len(entries)!=26 or digest.hexdigest()!='df1ea59a73b0ad08b51670bfa37da84eace99b9d0c45c8d270f7052b42e98701':
        raise ValueError('E54')


def extract(S, stream, destination, limit, roots, archive, index):
    offsets={}
    result=S.extract_stream(stream,destination,None,limit,links=True,
                            retain_roots=roots,frame_offsets=offsets)
    for name,value in offsets.items():
        if name in index:raise ValueError('E55')
        index[name]=dict(archive=str(archive),**value)
    return result


def materialize(index, members, destination):
    destination=Path(destination).resolve()
    for spec in members:
        name=spec['path'];entry=index[name];relative=PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('E56')
        target=destination/name
        if not target.resolve().is_relative_to(destination):raise ValueError('E56')
        if target.exists():
            with target.open('rb') as source:actual=hashlib.file_digest(source,'sha256').hexdigest()
            if actual!=spec['sha256']:raise ValueError('E57')
            continue
        # Archives are authenticated once by stage(). Seek directly to this PNG.
        with open(entry['archive'],'rb') as source:
            source.seek(entry['offset']);raw=source.read(entry['bytes'])
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=spec['sha256']:
            raise ValueError('E57')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as output:output.write(raw)


def stage_capture(settings, capture):
    path=settings.get('capture_index')
    if path is None:return
    data=json.loads(Path(path).read_text())
    materialize(data['index'],data['captures'][capture],Path(settings['frames_root']).parent)
