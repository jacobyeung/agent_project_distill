import hashlib,json
from pathlib import Path
from types import SimpleNamespace
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def checked(pin):
 if sha(pin['path'])!=pin['sha256']:raise ValueError('pin')
 return Path(pin['path'])
def write(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
common=SimpleNamespace(move_batch=lambda b,d:b)
TREE=Path('/nonexistent')
