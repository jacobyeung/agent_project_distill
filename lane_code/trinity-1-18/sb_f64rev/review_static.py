"""Read-only inventory and source comparison; all products stay in this workspace."""
import difflib
import hashlib
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
OUT = ROOT / 'out'
inputs = {}
def read(path):
    path = Path(path)
    value = path.read_bytes()
    inputs[str(path)] = hashlib.sha256(value).hexdigest()
    return value
def save(name, value):
    (OUT / name).write_text(json.dumps(dict(input_sha256=inputs, **value), indent=2) + '\n')

archive = SRC / 'in/tree_rebuild_b18_60e6ea72.tar'
digest = hashlib.sha256()
with archive.open('rb') as f:
    for block in iter(lambda: f.read(1024 * 1024), b''):
        digest.update(block)
inputs[str(archive)] = digest.hexdigest()
assert digest.hexdigest() == 'caa09d0c6aa79f55ee7ddf0dbe4580145a1e483a164226678539f554e8af6a36'
base, new = [SRC / 'pkg/work' / x for x in ('tree_r1', 'tree_f64')]
def files(tree):
    return {p.relative_to(tree): p for p in tree.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc'}
a, b = files(base), files(new)
diffs, changed = [], []
for rel in sorted(a.keys() | b.keys()):
    old = read(a[rel]) if rel in a else b''
    fresh = read(b[rel]) if rel in b else b''
    if old != fresh:
        text = ''.join(difflib.unified_diff(old.decode().splitlines(True), fresh.decode().splitlines(True),
                                          fromfile='tree_r1/' + str(rel), tofile='tree_f64/' + str(rel)))
        changed.append(dict(file=str(rel), hunks=re.findall(r'^@@.*@@', text, re.M)))
        diffs.append(text)
(OUT / 'INDEPENDENT_TREE_DIFF.patch').write_text(''.join(diffs))
patch = read(SRC / 'out/kit/patches/tree_r1_to_f64.patch').decode()
declared = re.findall(r'^\+\+\+ tree_f64/(\S+)', patch, re.M)
assert set(declared) == {x['file'] for x in changed}
sealed_mismatch = []
with tarfile.open(archive) as tar:
    members = tar.getmembers()
    for member in members:
        if member.name.startswith('work/tree_r1/') and member.isfile():
            rel = Path(member.name).relative_to('work/tree_r1')
            if rel not in a or hashlib.sha256(tar.extractfile(member).read()).hexdigest() != inputs[str(a[rel])]:
                sealed_mismatch.append(member.name)
    # Retain an isolated copy so the original regression harness cannot write in another lane.
    dest = ROOT / 'sealed_pkg'
    dest.mkdir(exist_ok=True)
    for member in members:
        target = dest / member.name
        assert target.resolve().is_relative_to(dest.resolve())
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
        elif member.isfile():
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(tar.extractfile(member).read())
        else:
            raise ValueError('Archive contains a non-regular member: ' + member.name)

evidence = {}
for path in sorted((SRC / 'out/evidence').glob('*.json')):
    value = json.loads(read(path))
    evidence[path.name] = dict(mode=value.get('mode'), layers=value.get('layers', value.get('parameters', {}).get('lm_layers')),
                              records=len(value.get('records', [])),
                              full_forward_ranks=sorted({r['rank'] for r in value.get('records', []) if r.get('stream') == 'pose' and 'rank' in r}),
                              all_finite=all(r.get('finite', True) for r in value.get('records', [])),
                              input_hashes_recorded='input_sha256' in value)
for folder in ('scripts', 'read', 'configs', 'tests'):
    for path in (SRC / 'out/kit' / folder).glob('*'):
        if path.is_file(): read(path)
logs = {}
for name in ('baseline_focused_serial', 'patched_focused2', 'f64_focused'):
    text = read(SRC / 'work/logs' / (name + '.log')).decode()
    logs[name] = dict(summary=re.findall(r'^(?:Ran .*|FAILED.*|EXIT.*|FileNotFoundError.*)$', text, re.M),
                      error_tests=re.findall(r'^ERROR: (.*)$', text, re.M))
save('static_review.json', dict(command='python review_static.py', archive_sha256=digest.hexdigest(),
    sealed_baseline_mismatches=sealed_mismatch, changed=changed, evidence=evidence, logs=logs))
(ROOT / 'STATUS.md').write_text('Source audit complete: the sealed archive hash matches the task. The independent tree diff and source hashes are in out/static_review.json and out/INDEPENDENT_TREE_DIFF.patch. CPU fixture runs omit the bound training receipt and sampler; planned-run validation remains missing. Regression and contract checks are next.\n')
print(json.dumps(dict(changed=changed, sealed_baseline_mismatches=sealed_mismatch, evidence=evidence, logs=logs), indent=2))
