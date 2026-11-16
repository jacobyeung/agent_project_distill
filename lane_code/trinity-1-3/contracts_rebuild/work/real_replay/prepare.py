"""Prepare fresh scratch inputs for the G3T tower-gravity replay after I/O approval."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import collections
import datetime

L = Path('/scratch/jjyeung/orch_n30/contracts_rebuild')
W = L / 'work/real_replay'
O = L / 'out/real_replay'
O.mkdir(exist_ok=True)

def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

archive = L / 'work/real/geometry_8c58df1547371bdb.tar'
base = L / 'work/base/work/base/tree_b01ce449'
before = size(L)
tree_size = size(base)
assert before + 3 * tree_size < 3_000_000_000
assert sha(archive) == '8c58df1547371bdb4169856031892a921adaa08f3aae39b15ab509a63c06d895'
dest = L / 'work/real/x_geo'
created, retained = [], []
with tarfile.open(archive, 'r|') as tar:
    for member in tar:
        target = dest / member.name
        assert target.resolve().is_relative_to(dest.resolve())
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        assert member.isfile(), member.name
        target.parent.mkdir(parents=True, exist_ok=True)
        incoming = tar.extractfile(member)
        if target.exists():
            h = hashlib.sha256()
            for block in iter(lambda: incoming.read(1024 * 1024), b''):
                h.update(block)
            assert h.hexdigest() == sha(target), str(target)
            retained.append(str(target))
        else:
            assert before + sum(p.stat().st_size for p in map(Path, created)) + member.size + 3 * tree_size < 3_000_000_000
            with target.open('xb') as f:
                shutil.copyfileobj(incoming, f, length=1024 * 1024)
            created.append(str(target))
npzs = sorted(dest.glob('*/g3t/*.npz'))
metas = sorted(dest.glob('*/g3t/*__*.json'))
inventory = dict(gravity_source='G3T tower gravity, not student-head gravity',
    source=str(dest), archive_source=str(archive),
    npz_count=len(npzs), capture_json_count=len(metas),
    npz_by_dataset=dict(collections.Counter(p.stem.split('__')[0] for p in npzs)),
    json_by_dataset=dict(collections.Counter(p.stem.split('__')[0] for p in metas)),
    missing_npz=[dict(capture=p.stem, source=str(p)) for p in metas if not p.with_suffix('.npz').exists()],
    missing_json=[str(p) for p in npzs if not p.with_suffix('.json').exists()],
    noncapture_json=[str(p) for p in dest.rglob('*.json') if '__' not in p.name],
    paths=[str(p) for p in npzs],
    max_npz_bytes=max(p.stat().st_size for p in npzs))
with (O/'CAPTURE_INVENTORY.json').open('x') as f:
    json.dump(inventory, f, indent=2)
print(json.dumps(inventory), flush=True)
for name in ('real_base', 'real_patched'):
    target = L / 'work/trees' / name
    if not target.exists():
        shutil.copytree(base, target)
    else:
        originals = {str(p.relative_to(base)): sha(p) for p in base.rglob('*') if p.is_file()}
        copied = {str(p.relative_to(target)): sha(p) for p in target.rglob('*') if p.is_file()}
        assert originals == copied, 'Existing fresh tree differs from sealed base: ' + name
# Directory moves update the copied root's parent entry; the sealed root is read-only.
target = L / 'work/trees/real_patched'
target.chmod(target.stat().st_mode | 0o200)
bin_dir = W / 'bin'
bin_dir.mkdir(exist_ok=True)
transactions = W / 'transactions'
transactions.mkdir(exist_ok=True)
wrapper = bin_dir / 'mktemp'
if not wrapper.exists():
    wrapper.write_text('#!/usr/bin/env bash\nset -eu\nexec /usr/bin/mktemp -d '+str(transactions)+'/contracts-XXXXXXXX\n')
    wrapper.chmod(0o755)
env = dict(os.environ, PATH=str(bin_dir)+':'+os.environ['PATH'])
result = subprocess.run(['bash', str(L/'out/apply_contract_patches.sh'),
    str(L/'work/trees/real_patched')], env=env, text=True, capture_output=True)
with (O/('apply_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.log')).open('x') as f:
    f.write('Gravity source: G3T tower gravity, not student-head gravity.\n')
    f.write(result.stdout + result.stderr)
assert result.returncode == 0, result.stdout + result.stderr
receipt = dict(gravity_source='G3T tower gravity, not student-head gravity',
    archive=str(archive), archive_sha256=sha(archive), bytes_before=before,
    bytes_after=size(L), tree_source=str(base), created=created, retained=retained,
    transaction_redirection=str(wrapper), patch_application=result.stdout)
assert receipt['bytes_after'] < 3_000_000_000
with (O/'PREPARATION.json').open('x') as f:
    json.dump(receipt, f, indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k not in ('created','retained')}), flush=True)
