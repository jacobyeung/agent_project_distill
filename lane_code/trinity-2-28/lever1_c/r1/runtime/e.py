"""Bounded exception and child-process diagnostics in opaque storage."""
from collections import deque
from contextlib import contextmanager
import os
from pathlib import Path
import threading
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
    read,write=os.pipe();lines=deque(maxlen=LIMIT)
    def drain():
        pending=b''
        try:
            while True:
                block=os.read(read,8192)
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
        finally:os.close(read)
    thread=threading.Thread(target=drain,daemon=True);thread.start()
    try:
        with os.fdopen(write,'wb',buffering=0) as stream:yield stream
    finally:
        thread.join(timeout=2)
        if lines:save(path,lines)
