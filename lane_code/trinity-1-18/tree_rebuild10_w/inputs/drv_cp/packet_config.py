"""Authenticate Cprime archive and expose operator pins."""
import hashlib,io,json,re,tarfile
from pathlib import Path
W=Path(__file__).resolve().parent
PINS=json.loads((W/'PACKET_PINS.json').read_text())
SNAP=Path('/scratch/jjyeung/orch_n30/r1_pkt/out')
ARCHIVE=(SNAP/PINS['archive']).read_bytes()
assert hashlib.sha256(ARCHIVE).hexdigest()==PINS['outer']
with tarfile.open(fileobj=io.BytesIO(ARCHIVE)) as tf:
 MEMBERS={}
 for m in tf:
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and m.name not in MEMBERS
  MEMBERS[m.name]=tf.extractfile(m).read()
SUMS={n:h for h,n in (line.split('  ',1) for line in MEMBERS['sums.txt'].decode().splitlines())}
assert set(SUMS)==set(MEMBERS)-{'sums.txt'}
assert all(hashlib.sha256(MEMBERS[n]).hexdigest()==h for n,h in SUMS.items())
BINDING=json.loads(MEMBERS['BINDING.json'])
assert BINDING['config_identity']==PINS['identity']
def pending_script(name):
    return '#!/bin/bash\nset +x\n# C_PACKET_PENDING '+name+'\necho "PENDING: packet C requires '+name+'" >&2\nexit 4\n'

def install_script(path, text, mode=0o700):
    if path.is_symlink():raise ValueError('Linked script: '+str(path))
    if path.exists() and path.read_text() not in (text, pending_script(path.name)):
        raise ValueError('Existing script differs: '+str(path))
    path.write_text(text);path.chmod(mode)

def render(text):
    for name, value in PINS.items():
        text = text.replace('@'+name.upper()+'@', str(value))
    assert not re.search(r'@[A-Z_]+@', text), 'Unresolved packet placeholder'
    return text

def fixture():
    dest = W/'fixture_cp'
    dest.mkdir(mode=0o700, exist_ok=True)
    for name, raw in MEMBERS.items():
        path = dest/name
        parent = dest
        for component in Path(name).parts[:-1]:
            parent = parent/component
            assert not parent.is_symlink()
            parent.mkdir(mode=0o700, exist_ok=True)
            parent.chmod(0o700)
        assert not path.is_symlink()
        if path.exists():
            assert path.read_bytes() == raw, 'Final fixture differs: '+name
        else:
            with path.open('xb') as stream:
                stream.write(raw)
            path.chmod(0o600)
    return dest
