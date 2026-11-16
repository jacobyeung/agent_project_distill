"""Shared deterministic files and path checks for the LEG-S1 read tools."""
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT/'work/vendor'
TREE = ROOT/'work/tree_final'
PARENT_SHA = 'c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67'
BASE_SHA = 'ae9247f7c316e7661bfbe4301c28d75b6871db7427d675b8e1cc4c0c41b4b252'

def local(path):
    p=Path(path).resolve()
    if p.parts[1:2] == ('home',) or (len(p.parts)>1 and p.parts[1].startswith('data')):
        raise ValueError('Forbidden shared-filesystem path: '+str(p))
    return p

def sha(path):
    with local(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def load(path): return json.loads(local(path).read_text())
def rows(path): return [json.loads(s) for s in local(path).read_text().splitlines() if s.strip()]
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def dump(path,x):
    p=local(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')
def pin(path): return dict(path=str(local(path)),sha256=sha(path))
def checked(p):
    if sha(p['path'])!=p['sha256']: raise ValueError('Pin mismatch: '+str(p['path']))
    return local(p['path'])

def vendor():
    # The r5 modules intentionally import one another by their original names.
    sys.path.insert(0,str(VENDOR/'r5'))
    import adapter, report
    return adapter, report

def install_tree():
    sys.path.insert(0,str(TREE))

