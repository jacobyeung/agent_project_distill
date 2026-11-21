import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading


def detail(exc):
    name = type(exc).__name__
    if name not in ('ValueError', 'TypeError', 'KeyError', 'RuntimeError', 'TimeoutError',
                    'OSError', 'FileNotFoundError', 'PermissionError', 'MemoryError',
                    'ImportError', 'ModuleNotFoundError', 'AssertionError'):
        name = 'x' + name.encode().hex()
    code = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ''
    if not re.fullmatch('E[0-9]{2}', code):
        code = 'E00'
    frames = []
    tb = exc.__traceback__
    while tb and len(frames) < 32:
        filename = tb.tb_frame.f_code.co_filename
        base = Path(filename).name
        if base not in ('0.py', '2.py', '9.py'):
            base = hashlib.sha256(filename.encode()).hexdigest()[:16] + '.py'
        frames.append(base + ':' + str(tb.tb_lineno))
        tb = tb.tb_next
    return dict(type=name[:160], code=code, files=frames)


def record(path, value):
    path = Path(path)
    raw = json.dumps(value, separators=(',', ':')).encode() + b'\n'
    if len(raw) > 4096:
        raise ValueError('E91')
    if not path.exists() or path.stat().st_size + len(raw) <= 16384:
        with path.open('ab') as f:
            f.write(raw)


# Child stderr classes (opaque codes; the text itself never leaves the job).
# B1 namespace source path missing, N1 interpreter not found, N2 script not found, P1 Python
# traceback, B2 other namespace error, W1 worker code only, S1 signal, Z0 empty, X0 other.
CLASSES = (('B1', b"Can't find source path"), ('N1', b'execvp'), ('P1', b'Traceback (most recent call last)'),
           ('N2', b"can't open file"), ('N1', b': not found'), ('N1', b'No such file or directory'),
           ('B2', b'bwrap:'), ('W1', b'E99'))


def classify(first, last, status):
    """Classify a child's stderr from its first and last bytes; returns an opaque code."""
    if status is not None and status < 0:
        return 'S1'
    text = first+b'\n'+last
    if not text.strip():
        return 'Z0'
    for code, mark in CLASSES:
        if mark in text:
            return code
    return 'X0'


def capture(argv, keep=0, **kw):
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, **kw)
    stats = [None, None]
    kept = [b'', b'']
    def drain(pipe, index):
        count = 0
        digest = hashlib.sha256()
        while True:
            block = pipe.read(65536)
            if not block:
                break
            count += len(block)
            digest.update(block)
            if keep and index == 1:
                if len(kept[0]) < keep:
                    kept[0] += block[:keep-len(kept[0])]
                kept[1] = (kept[1]+block)[-keep:]
        pipe.close()
        stats[index] = dict(bytes=count, sha256=digest.hexdigest())
    threads = [threading.Thread(target=drain, args=(pipe, i))
               for i, pipe in enumerate((proc.stdout, proc.stderr))]
    for thread in threads:
        thread.start()
    try:
        proc.wait()
    except BaseException:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise
    finally:
        for thread in threads:
            thread.join()
    for stream, stat in zip((sys.stdout, sys.stderr), stats):
        print(json.dumps(stat, separators=(',', ':')), file=stream, flush=True)
    proc.kept = dict(c=classify(kept[0], kept[1], proc.returncode), b=stats[1]['bytes']) if keep else None
    return proc


def log_name(mode, group):
    if mode == '0':
        return '4.err'
    if mode not in ('1', '2') or group not in ('0', '1'):
        raise ValueError('E93')
    return ('6' if mode == '2' else '5')+group+'.err'


def main():
    mode, root = sys.argv[1], Path(sys.argv[2])
    group = sys.argv[3] if len(sys.argv) > 3 else ''
    log = root / log_name(mode, group)
    log.touch(exist_ok=False)
    proc = capture([sys.executable, '-I', '-s', '-B', str(root/'0.py'), mode, str(root)]+([group] if group else []))
    if proc.returncode:
        record(log, dict(type='RuntimeError', code='E92', files=[], status=proc.returncode))
    if log.stat().st_size:
        print(log.read_text(), end='', file=sys.stderr, flush=True)
    return proc.returncode if proc.returncode >= 0 else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps(detail(exc), separators=(',', ':')), file=sys.stderr)
        raise SystemExit(1)
