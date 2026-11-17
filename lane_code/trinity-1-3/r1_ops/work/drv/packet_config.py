"""Read and verify operator pins from the frozen final R1-P packet."""
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

W = Path(__file__).resolve().parent
SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_d8b03fd1/out')
FINAL_ARCHIVE_SHA = '888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029'
FINAL_IDENTITY = 'd8b03fd14db01af4def4a0cfd9a49d16ec492d9a3c6b0c56977f7f22b79f705a'

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

def render(text):
    for name, value in PINS.items():
        text = text.replace('@'+name.upper()+'@', str(value))
    assert not re.search(r'@[A-Z_]+@', text), 'Unresolved packet placeholder'
    return text

def fixture():
    dest = W/'fixture_final'
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
