"""Exercise both shipped authority checks with bounded local metadata."""
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from packet_config import PINS, MEMBERS

W = Path(__file__).resolve().parent
ready = Path(sys.argv[1]).resolve()
assert ready.is_relative_to(W)
original = json.loads((ready/'k/4.json').read_bytes())
T = Path(tempfile.mkdtemp(prefix='authority_c2_', dir=W))
bodies = {}
for name in ('pr1.sh', 'dvp1.sh'):
    body, = re.findall(r"<<'PYCODE'\n(.*?)^PYCODE$", (W/name).read_text(), re.M | re.S)
    assert MEMBERS['r4.py'].decode() in body
    bodies[name] = body
mutations = []
for key in ('modes', 'new_gpus', 'partition', 'allowed_partitions', 'wall_seconds',
            'nodes', 'resume', 'arm', 'gpu_cap', 'other_running_and_pending_gpus',
            'max_parallel_jobs', 'production_go_granted',
            'production_go_required_separately', 'mode_resources'):
    auth = copy.deepcopy(original)
    auth.pop(key)
    mutations.append(('missing_'+key, auth, True))
for mode in ('p', 't', 'u'):
    for key, value in (('gpus', 1), ('nodes', 2), ('wall_seconds', 1), ('partitions', ['other'])):
        auth = copy.deepcopy(original)
        auth['mode_resources'][mode][key] = value
        mutations.append((mode+'_'+key, auth, True))
for key, value in (('nodes', True), ('production_go_granted', 0),
                   ('config_sha256', '0'*64), ('source_revision', 'sha256:'+'0'*64),
                   ('admission_contract_sha256', '0'*64), ('modes', ['p'])):
    auth = copy.deepcopy(original)
    auth[key] = value
    mutations.append(('wrong_'+key, auth, True))
auth = copy.deepcopy(original)
auth['scope'] += ' changed without resealing'
mutations.append(('digest_mismatch', auth, False))
cases = [('valid', original, True)] + mutations
for name, auth, reseal in cases:
    root = T/name
    (root/'k').mkdir(parents=True)
    raw = json.dumps(auth, sort_keys=True).encode()
    (root/'k/4.json').write_bytes(raw)
    digest = hashlib.sha256(raw if reseal else b'original sealed bytes').hexdigest()
    (root/'SHA256SUMS.txt').write_text(digest+'  k/4.json\n')
    for driver, body in bodies.items():
        prefix = body.split('k,b=map(Path,sys.argv[1:3])')[0] if driver=='pr1.sh' else body.split("k=Path('")[0]
        scope = {}
        exec(compile(prefix, driver, 'exec'), scope)
        try:
            scope['check_authority'](root)
        except (ValueError, KeyError):
            assert name != 'valid', driver
        else:
            assert name == 'valid', (driver, name)
print('PASS both embedded drivers: exact authority accepted; '+str(len(mutations))+' authority/hash mutations refused each')

# Run the entire dvp1 Python body, including directory inspection.
for label, allowed in (('valid', True), ('top_shadow', False), ('root_writable', False),
                       ('subdir_writable', False), ('bytecode', False), ('linked_code', False)):
    root = T/('permissions_'+label)
    (root/'k').mkdir(parents=True)
    for name in ('k/4.json', 'SHA256SUMS.txt'):
        (root/name).write_bytes((T/'valid'/name).read_bytes())
    if label=='top_shadow':(root/'json.py').write_text('untrusted')
    code = root/'b'
    code.mkdir()
    (code/'sa').mkdir()
    if label=='bytecode':
        (code/'sa/__pycache__').mkdir(mode=0o500)
    if label=='linked_code':
        (code/'alias').symlink_to(root/'k/4.json')
    (code/'sa').chmod(0o700 if label=='subdir_writable' else 0o500)
    code.chmod(0o700 if label=='root_writable' else 0o500)
    body = bodies['dvp1.sh'].replace(PINS['kit'], str(root))
    result = subprocess.run([sys.executable, '-B', '-c', body], capture_output=True, text=True)
    assert (result.returncode==0)==allowed, (label, result.stdout, result.stderr)
    print('PASS dvp1', label, 'accept' if allowed else 'refuse')
print('Test artifacts:', T)
