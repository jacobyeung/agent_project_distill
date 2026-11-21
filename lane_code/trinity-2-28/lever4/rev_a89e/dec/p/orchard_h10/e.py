
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
"""Bounded exception and child-process diagnostics in opaque storage."""
from collections import deque
from contextlib import contextmanager
import os
from pathlib import Path
import threading
import select
import time
import traceback
import j

LIMIT = 200
WIDTH = 2048


def save(path, lines):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    value=dict(lines=list(lines)[-LIMIT:],limit=LIMIT,width=WIDTH)
    raw=j.pack(j.wire_dumps(value))
    while len(raw)>262144:
        value['lines']=value['lines'][1:];raw=j.pack(j.wire_dumps(value))
    with open(path,'wb') as stream:stream.write(raw)


def exception(path, error):
    lines=deque(maxlen=LIMIT)
    for block in traceback.TracebackException.from_exception(error).format(chain=True):
        lines.extend(line[-WIDTH:] for line in block.splitlines())
    save(path,lines)


@contextmanager
def capture(path, mirror=None):
    """Drain a child continuously without retaining raw logs or blocking a pipe."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    durable=path.with_suffix('.0')
    with durable.open('ab'):pass
    read,write=os.pipe();lines=deque(maxlen=LIMIT);errors=[]
    os.set_blocking(read,False)
    stopped=threading.Event()
    def drain():
        pending=b'';deadline=None
        try:
            while True:
                # A policy watcher can inherit stdout after the waited child
                # exits. End capture at the owner's boundary, not its EOF.
                if stopped.is_set() and deadline is None:deadline=time.monotonic()+.5
                if deadline is not None and time.monotonic()>=deadline:break
                ready,_,_=select.select([read],[],[],.05)
                if not ready:
                    if deadline is not None:break
                    continue
                try:block=os.read(read,8192)
                except BlockingIOError:continue
                if not block:break
                for target in (durable, Path(mirror) if mirror else None):
                    if target is None:continue
                    left=max(0,131072-(target.stat().st_size if target.exists() else 0))
                    data=(block.hex()+'\n').encode()[:left]
                    if data:
                        with target.open('ab',buffering=0) as disk:disk.write(data);os.fsync(disk.fileno())
                parts=(pending+block).split(b'\n')
                lines.extend(p[-WIDTH:].decode('utf-8','replace') for p in parts[:-1])
                pending=parts[-1][-WIDTH:]
            if pending:lines.append(pending.decode('utf-8','replace'))
        except Exception as error:errors.append(error)
        finally:os.close(read)
    thread=threading.Thread(target=drain,daemon=True)
    try:thread.start()
    except Exception:
        os.close(read);os.close(write)
        raise
    try:
        with os.fdopen(write,'wb',buffering=0) as stream:yield stream
    finally:
        stopped.set()
        thread.join(timeout=2)
        save(path,lines)
        if errors:raise errors[0]
        if thread.is_alive():raise RuntimeError('E80')
