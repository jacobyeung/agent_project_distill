
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
"""Private dispatch. Only this numeric entry and its numeric config reach argv."""
import json
from pathlib import Path
import sys

cfg=json.loads(Path(sys.argv[1]).read_text())
p=Path(cfg['package'])
sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
import l
Path=l.install(p).Path
from orchard_h10.common import install_process_guard
install_process_guard(Path(sys.argv[1]).resolve().parent)
action=cfg['action']
if action==0:
    from orchard_h10.prepare import run
    run(cfg['config'],cfg['inputs'])
elif action==1:
    import os
    from orchard_h10.runner import run
    result=run(cfg['config'],os.environ['CUDA_VISIBLE_DEVICES'].split(','),cfg['end'],prefix=cfg['config']['prefix'])
    raise SystemExit(1 if result['failure'] else 0)
elif action==2:
    from orchard_h10.runner import worker_args
    from h1eval.h10.launch import main
    raise SystemExit(main(worker_args(cfg)))
elif action==3:
    if cfg.get('boot'):
        from orchard_h10.boot import check
        check(cfg)
        raise SystemExit(0)
    from g.w import run
    result=run(cfg['config'],cfg['stop_at'])
    raise SystemExit(1 if result and result['failure'] else 0)
elif action==4:
    from orchard_h10.boot import worker
    worker(cfg)
else:raise ValueError('Invalid dispatch')
