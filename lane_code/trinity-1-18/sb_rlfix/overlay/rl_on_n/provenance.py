"""Local-only input hashing and output receipts."""
import hashlib
import json
import os
from pathlib import Path
import sys

INPUTS = {}
READS = set()

def _read_audit(event, args):
    if event == 'open' and args and isinstance(args[0], str):
        path = args[0]
        flags = args[2] if len(args) > 2 else 0
        local_input = ('/sb_f64/pkg/' in path or '/qwen35_9b_meta/' in path
                       or any('/'+lane+'/'+part+'/' in path for lane in ('sb_rlkit','sb_rlfix') for part in ('overlay','scripts','configs','in','tests')))
        if local_input and not (isinstance(flags,int) and flags & (os.O_WRONLY | os.O_RDWR)):
            READS.add(str(Path(path).resolve()))
    elif event == 'sqlite3.connect' and args and isinstance(args[0],str):
        path=args[0].removeprefix('file:').split('?')[0]
        if path.startswith('/scratch/'): READS.add(path)

sys.addaudithook(_read_audit)

def sha(path):
    path = Path(path).resolve()
    if str(path).startswith(('/home/', '/data', '/lustre/')):
        raise ValueError('Stage input on local scratch before reading: '+str(path))
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    INPUTS[str(path)] = h.hexdigest()
    return h.hexdigest()

def load(path):
    sha(path)
    return json.loads(Path(path).read_text())

def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}

def checked(value):
    if not value or sha(value['path']) != value['sha256']:
        raise ValueError('MISSING or changed pinned input: '+str(value))
    return Path(value['path'])

def tree(root):
    root = Path(root).resolve()
    if not (root/'student_pilot/r1_rooms.py').is_file():
        raise ValueError('MISSING N tree: '+str(root))
    sys.path.insert(0, str(root))
    return root

def capture_modules():
    for path in list(READS):
        if Path(path).is_file(): sha(path)
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and path.endswith('.py') and ('/tree_r1/' in path or '/rl_on_n/' in path):
            sha(path)

def write(path, value):
    capture_modules()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dependencies={k:v for k,v in INPUTS.items() if k!=str(path.resolve())}
    path.write_text(json.dumps({**value, 'input_sha256': dict(sorted(dependencies.items()))},
                               indent=2, sort_keys=True, allow_nan=False)+'\n')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
