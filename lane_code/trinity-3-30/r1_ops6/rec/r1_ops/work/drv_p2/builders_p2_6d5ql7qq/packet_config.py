"""Read and verify operator pins from the frozen final R1-P packet."""
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

W = Path(__file__).resolve().parent
SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_2c67f1f2/out')
FINAL_ARCHIVE_SHA = 'def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f'
FINAL_IDENTITY = '2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def inventory(raw):
    result = {}
    for line in raw.decode().splitlines():
        digest, name = line.split('  ', 1)
        assert re.fullmatch('[0-9a-f]{64}', digest)
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert name not in result
        result[name] = digest
    return result

SUMS = inventory((SNAP/'SHA256SUMS').read_bytes())
def sealed(name):
    raw = (SNAP/name).read_bytes()
    assert sha(raw) == SUMS[name], 'Frozen packet checksum differs: '+name
    return raw

BINDING = json.loads(sealed('BINDING.json'))
OPERATOR = json.loads(sealed('OPERATOR.json'))
PACKET = sealed('R1P_PACKET.md').decode()
assert BINDING['config_identity'] == FINAL_IDENTITY
assert OPERATOR['sha256'] == FINAL_ARCHIVE_SHA
ARCHIVE = sealed(OPERATOR['archive'])
assert sha(ARCHIVE) == FINAL_ARCHIVE_SHA
assert OPERATOR['job_name'] == BINDING['job_name'] == 'a15_cot_ap'+BINDING['run_key']
MEMBERS = {}
with tarfile.open(fileobj=io.BytesIO(ARCHIVE)) as tf:
    for member in tf:
        name = member.name
        assert member.isfile() and not Path(name).is_absolute()
        assert '..' not in Path(name).parts and name not in MEMBERS
        assert member.size < 32000000
        MEMBERS[name] = tf.extractfile(member).read()
INNER = inventory(MEMBERS['sums.txt'])
assert set(INNER) == set(MEMBERS)-{'sums.txt'}
assert all(sha(MEMBERS[n]) == digest for n, digest in INNER.items())
assert json.loads(MEMBERS['BINDING.json']) == BINDING
assert json.loads(MEMBERS['ids.json'])['identity'] == FINAL_IDENTITY
source = re.search(r'Set `H=([^`]+)`; its `SHA256SUMS.txt` must hash to `([0-9a-f]{64})`', PACKET)
assert source, 'Frozen packet does not specify the source manifest'
PINS = dict(bundle=OPERATOR['bundle'], kit=OPERATOR['kit'],
            store=BINDING['store_key'], run=BINDING['run_key'],
            identity=BINDING['config_identity'], tree=BINDING['tree_sha256'],
            outer=OPERATOR['sha256'], archive=OPERATOR['archive'],
            archive_bytes=len(ARCHIVE), members=len(MEMBERS),
            deriver=INNER['d.py'], selection=BINDING['selection_sha256'],
            source=source.group(1), source_manifest=source.group(2))
assert PINS['bundle'].endswith('/i_'+PINS['store'])
assert PINS['kit'].endswith('/x_'+PINS['store'])

def pending_script(name):
    return '#!/bin/bash\nset +x\n# PROOF2_PENDING '+name+'\necho "PENDING: proof 2 requires '+name+'" >&2\nexit 4\n'

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
    dest = W/'fixture_p2'
    dest.mkdir(mode=0o700, exist_ok=True)
    for name, raw in MEMBERS.items():
        path = dest/name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        assert not path.is_symlink()
        if path.exists():
            assert path.read_bytes() == raw, 'Final fixture differs: '+name
        else:
            with path.open('xb') as stream:
                stream.write(raw)
            path.chmod(0o600)
    return dest
