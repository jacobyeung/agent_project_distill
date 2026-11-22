"""The rehearsal planner's writer (pc.py runs it as a test writer: <python> -I -s -B sw.py <mode> SESSIONS KEY FILE 4 4).
It runs the kit's own b/gc.py main (its part names, byte ranges, prior-receipt skip and receipts file) with
one change: gc.py's HTTPS PUT is replaced by a local recorder that reads the byte range, takes its sha256 and
writes one small record under $A15_UPSINK. No byte leaves the node and no connection is opened (an audit
hook refuses any connect or name lookup and logs it to $A15_UPSINK/audit_<pid>.jsonl). Session URLs must be
the planner's local labels under the scratch run folder, else the part fails."""
import hashlib, json, os, runpy, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NOUPLOAD = 'https://a15-local-sink.invalid'
NET = {'socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr', 'socket.sendto',
       'socket.sendmsg', 'http.client.connect', 'urllib.Request'}
up = Path(os.environ['A15_UPSINK']); run = os.environ['A15_RUN'].rstrip('/')
audit = up / f'audit_{os.getpid()}.jsonl'


def note(row):
    with open(audit, 'a') as f:
        f.write(json.dumps(row) + '\n')


def hook(name, args):
    if name in NET:
        note(dict(event=name, args=repr(args)[:300], refused=True))
        raise RuntimeError('A15: network refused in the rehearsal writer: ' + name)
    if name.startswith('socket.'):
        note(dict(event=name, args=repr(args)[:300]))


sys.addaudithook(hook)
note(dict(event='start', argv=sys.argv[1:], pid=os.getpid()))
gc = runpy.run_path(os.environ['Q_KIT'] + '/b/gc.py', run_name='gc_runtime')
g = gc['main'].__globals__


def local(uri, path, offset, length, name):
    if not uri.startswith(NOUPLOAD + run + '/'):
        raise ValueError('A15: session outside the local sink for ' + name)
    t = time.time(); h = hashlib.sha256(); left = length
    with open(path, 'rb') as f:
        f.seek(offset)
        while left:
            b = f.read(min(1 << 24, left))
            if not b:
                raise IOError('short read')
            h.update(b); left -= len(b)
    row = dict(name=name, bytes=length, offset=offset, md5=None, sha256=h.hexdigest(), generation='a15-local-sink',
               seconds=round(time.time() - t, 1), local_sink=str(up / (name + '.json')), uri=uri)
    rec = up / (name + '.json')            # object names carry folders (q9/<kit>/...): the record mirrors them
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps(row, sort_keys=True) + '\n')
    return row


g['upload'] = local
g['ProcessPoolExecutor'] = ThreadPoolExecutor
sys.exit(gc['main'](sys.argv[1:]))
