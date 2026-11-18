"""Read and verify operator pins from the frozen R1 continuation C packet."""
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

W = Path(__file__).resolve().parent
SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_c60b9015/out')
FINAL_ARCHIVE_SHA = 'c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c'
FINAL_IDENTITY = '6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74'

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

# The outer SHA256SUMS belongs to A. Authenticate C with the supplied archive
# digest, CONT2_INVENTORY's after pins, OPERATOR, and the archive's sums.txt.
CONT2_INVENTORY = json.loads((SNAP/'CONT2_INVENTORY.json').read_bytes())
op_raw = (SNAP/'OPERATOR.json').read_bytes()
assert sha(op_raw) == CONT2_INVENTORY['out/OPERATOR.json']['after']
OPERATOR = json.loads(op_raw)
assert OPERATOR['sha256'] == FINAL_ARCHIVE_SHA
ARCHIVE = (SNAP/OPERATOR['archive']).read_bytes()
assert sha(ARCHIVE) == FINAL_ARCHIVE_SHA
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
SUMS = dict(INNER)
SUMS.update({'units/'+n: INNER[n] for n in ('u.json','u.gz','i.json','m.json')})
def sealed(name):
    raw = (SNAP/name).read_bytes()
    assert sha(raw) == SUMS[name], 'Frozen packet checksum differs: '+name
    return raw
BINDING = json.loads(sealed('BINDING.json'))
assert BINDING['config_identity'] == FINAL_IDENTITY
assert OPERATOR['job_name'] == BINDING['job_name'] == 'a15_cot_ap'+BINDING['run_key']
assert BINDING['run_key'] == '05b8ac69' and BINDING['store_key'] == '7f1589c1'
assert json.loads(MEMBERS['ids.json'])['identity'] == FINAL_IDENTITY
assert MEMBERS['config.json'] == sealed('config.json')
for name in ('d.py','p.py','p_05b8ac69.sh','sums.txt'):
    assert sha(MEMBERS[name]) == CONT2_INVENTORY['out/operator/'+name]['after']
result=json.loads((SNAP/'CONT2_RESULT.json').read_bytes())
assert result['sha256']==FINAL_ARCHIVE_SHA and result['identity']==FINAL_IDENTITY
PACKET = (SNAP/'CONT2.md').read_text()
CONFIG = json.loads(MEMBERS['config.json'])
assert CONFIG['h1']['routing_pose_targets'] is True
assert CONFIG['h1']['faithful_own_camera_rows'] is False
for schedule in (CONFIG['scheduled_sampling'], CONFIG['recipe']['scheduled_sampling']):
    value = schedule['max_own_probability']
    assert type(value) in (int, float) and value == 0
assert BINDING['launch_switches'] == dict(S1=False, S2=True, max_own_probability=0)
assert CONFIG['continuation'] == BINDING['continuation']
assert CONFIG['continuation']['run']=='673bc60f' and CONFIG['continuation']['step']==200
assert CONFIG['h1']['stop_after_step']==600 and CONFIG['milestones']==[400,600]
assert BINDING['time_limit']=='24:00:00' and BINDING['record_key']=='69d2930d'
UNIT=json.loads(MEMBERS['u.json'])
assert MEMBERS['u.json']==sealed('units/u.json')
assert UNIT['artifacts']==BINDING['unit_binding']['artifacts']
for name,pin in UNIT['artifacts'].items():
    assert sha(MEMBERS[name])==pin['sha256'] and MEMBERS[name]==sealed('units/'+name)
assert UNIT['counts']['eligible']==747 and BINDING['unit_binding']['sampling_eligible']==683
REMOVE_SHA = '02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'
REMOVE_PATH = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json'
assert MEMBERS['n.json'] == MEMBERS['records/n.json'] == sealed('records/n.json')
assert sha(MEMBERS['n.json']) == REMOVE_SHA == BINDING['division_removal']['sha256']
assert BINDING['division_removal']['rows'] == len(MEMBERS['n.json'].splitlines()) == 601
assert 'n.json' in BINDING['record_files']
assert len(CONFIG['remove_files']) == 7
assert CONFIG['remove_files'][-1] == dict(path=REMOVE_PATH, sha256=REMOVE_SHA)
assert CONFIG['type_mix']['streams']['vqa']['cells']['room']['cents'] == 170
assert CONFIG['type_mix']['streams']['vqa']['cells']['direction']['cents'] == 3119
PINS = dict(bundle=OPERATOR['bundle'], kit=OPERATOR['kit'],
            store=BINDING['store_key'], run=BINDING['run_key'],
            identity=BINDING['config_identity'], tree=BINDING['tree_sha256'],
            outer=OPERATOR['sha256'], archive=OPERATOR['archive'],
            archive_bytes=len(ARCHIVE), members=len(MEMBERS),
            deriver=INNER['d.py'], selection=BINDING['selection_sha256'],
            source='/project/community/jjyeung/okh7/x_3fdda0fb',
            source_manifest='661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3',
            remove_sha256=REMOVE_SHA, remove_path=REMOVE_PATH,
            unit_rows=UNIT['counts']['eligible'], unit_ft_eligible=BINDING['unit_binding']['sampling_eligible'],
            unit_source_sha256=UNIT['source']['sha256'], unit_manifest_sha256=UNIT['manifest']['sha256'],
            unit_indices_sha256=UNIT['index']['sha256'],
            cpu_python='/project/community/jjyeung/latency/envs/fit/bin/python3')
assert PINS['bundle'].endswith('/i_'+PINS['store'])
assert PINS['kit'].endswith('/x_'+PINS['store'])

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
    dest = W/'fixture_c1'
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
