"""Reproduce the real Orchard listing; keep every operation local and CPU-only."""
import hashlib, importlib.util, json, os, runpy, stat, subprocess, sys
from pathlib import Path
from unittest.mock import patch

H = Path(__file__).resolve().parents[1]
D = Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0/kitfull')
sys.path.insert(0, str(H / 'tools'))
import derive_kit_h1 as dk

root = H / 'evidence/fix4_listing'
root.mkdir(mode=0o700)
listing = (H / 'evidence_orchard_q7_2157Z.txt').read_text()
sections = {}
for line in listing.splitlines():
    if line.startswith('### '):
        section = line[4:]; sections[section] = {}
    elif section != 'SRC sizes' and line.strip():
        mode, kind, name = line.split(' ', 2)
        sections[section][name or '.'] = (int(mode, 8), kind)
src, empty, provisional = (sections[n] for n in ('SRC x_07ca49df', 'E', 'P'))
runtime = set(src) - set(empty)
assert len(src) == 193 and len(empty) == 103 and len(runtime) == 90
assert not runtime & set(provisional)
assert all(src[n] == empty[n] for n in set(src) & set(empty))

base = root / 'x_07ca49df'
base.mkdir(mode=0o700)
members = dk.manifest_members(D)
synthetic = []
# Retain required sealed JSON and executable bytes; unavailable payloads and runtime
# files use small stand-ins. No real runtime-state content is available or opened.
for name, (mode, kind) in sorted(src.items(), key=lambda row: (len(Path(row[0]).parts), row[0])):
    if name == '.': continue
    p = base / name
    if kind == 'd': p.mkdir(mode=0o700)
    else:
        assert kind == 'f'
        if name in members and (D / name).is_file(): p.write_bytes((D / name).read_bytes())
        else:
            p.write_bytes(b'local listing fixture\n')
            if name in members: synthetic.append(name)
(base / 'SHA256SUMS.txt').write_text(''.join(dk.sha(base / n) + '  ' + n + '\n' for n in members))
for name, (mode, kind) in sorted(src.items(), key=lambda row: -len(Path(row[0]).parts)):
    (base / name).chmod(mode)
pin = dk.sha(base / 'SHA256SUMS.txt')
dk.SEALED_MANIFEST = pin
assert len(synthetic) == 2

def metadata(tree):
    return {str(p.relative_to(tree)): (stat.S_IMODE(p.lstat().st_mode),
            'd' if p.is_dir() else 'f') for p in [tree, *tree.rglob('*')]}

assert metadata(base) == src
before_modes = metadata(base)
before_sealed = {n: dk.sha(base / n) for n in members}
ids = json.loads((H / 'ids.json').read_text())
over = json.loads((H / 'build/over_local.json').read_text())
over.pop('fixture', None)
result = dict(source_entries=len(src), runtime_entries=len(runtime),
              runtime_names=sorted(runtime), synthetic_payloads=synthetic,
              listing_sha256=dk.sha(H / 'evidence_orchard_q7_2157Z.txt'))

def bundle(name, prior=False):
    b = root / name; b.mkdir(mode=0o700)
    tree = H / 'evidence/fix4_before' if prior else H
    source = (tree / 'tools/derive_kit_h1.py').read_text().replace(
        "SEALED_MANIFEST = 'de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'",
        'SEALED_MANIFEST = ' + repr(pin))
    (b / 'd.py').write_text(source)
    (b / 'r.py').write_text((tree / 'tools/orchard_records.py').read_text().replace(
        "O=Path('/project/community/jjyeung/okh7')", 'O=Path(' + repr(str(root)) + ')'))
    bundle_ids, bundle_over = ids, json.loads(json.dumps(over))
    if prior:
        bundle_ids = json.loads((H/'evidence/fix6_before/ids.json').read_text())
        for n in ('4.json', 'review.json', 'staging.json'):
            p = H/'evidence/fix6_before/payload'/n
            bundle_over['add_k'][n] = dict(path=str(p), sha256=dk.sha(p))
    (b / 'ids.json').write_text(json.dumps(bundle_ids))
    (b / 'over.json').write_text(json.dumps(bundle_over))
    return b

old = bundle('old', prior=True)
rc = subprocess.run([sys.executable, '-B', str(old / 'r.py'), 'prepare'], capture_output=True, text=True)
assert rc.returncode != 0 and 'member modes differ' in rc.stderr, rc.stderr
assert (old / 'p.json').is_file() and (old / 'e/SHA256SUMS.txt').is_file()
(root / 'fix3_failure.log').write_text(rc.stdout + rc.stderr)
result['fix3_prepare'] = 'EXPECTED FAILURE: member modes differ'

# Deny source access outside the manifest boundary, including recursive listing.
# This also prevents accidental reads/copies of the unmanifested certificate.
allowed = set(members) | dk.member_directories(members) | {'SHA256SUMS.txt'}
original_open, original_stat, original_iterdir = Path.open, Path.stat, Path.iterdir
def guard(p):
    try: name = str(p.relative_to(base))
    except ValueError: return
    assert name in allowed, 'unlisted source access: ' + name
def guarded_open(p, *a, **kw):
    guard(p); return original_open(p, *a, **kw)
def guarded_stat(p, *a, **kw):
    guard(p); return original_stat(p, *a, **kw)
def guarded_iterdir(p):
    assert p != base and base not in p.parents, 'source traversal: ' + str(p)
    return original_iterdir(p)

new = bundle('new')
with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
        patch.object(Path, 'iterdir', guarded_iterdir), patch.object(sys, 'argv', [str(new / 'r.py'), 'prepare']):
    runpy.run_path(str(new / 'r.py'), run_name='__main__')
assert json.loads((new / 'e.json').read_text())['status'] == 'PASS'
assert (new / 'e/SHA256SUMS.txt').read_bytes() == (base / 'SHA256SUMS.txt').read_bytes()
assert dk.mode_inventory(new / 'e') == dk.mode_inventory(base)
assert set(dk.mode_inventory(base)) == set(members) | dk.member_directories(members)
for out in (new / 'p', new / 'e'):
    assert not runtime & set(metadata(out))
    for n in dk.manifest_members(out):
        want = dict(reversed(line.split('  ', 1)) for line in (out / 'SHA256SUMS.txt').read_text().splitlines())[n]
        assert dk.sha(out / n) == want
assert all(not list((new / 'p' / n).iterdir()) for n in ('o', 'runs'))
assert json.loads((new / 'p/ANON_OK.json').read_text())['status'] == 'UNREVIEWED'
result['prepare_and_empty_reproduction'] = 'PASS'
result['source_access_guard'] = 'PASS'

# Poison unlisted files under executable/record directories and add a dangling link.
# They must neither be inspected nor enter the generated executable inventory.
fs = dk.SealedOutput(base)
fs.text(base / 'b/unlisted.py', 'raise RuntimeError("unlisted")\n')
fs.text(base / 'k/unlisted.json', 'not JSON\n')
(base / 'unlisted_link').symlink_to(root / 'absent')
with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
        patch.object(Path, 'iterdir', guarded_iterdir):
    dk.derive(base, root / 'poison_empty', {})
    dk.derive(base, root / 'poison_h1', over)
for out in (root / 'poison_empty', root / 'poison_h1'):
    assert not any((out / n).exists() for n in ('b/unlisted.py', 'k/unlisted.json', 'unlisted_link'))
result['unlisted_files_and_link_ignored'] = 'PASS'

# Execute the shipped final comparison against a candidate with real permissions.
final = root / 'final'
dk.derive(base, final, dict(over, fixture=True, status='BLOCKED'))
la = json.loads((final / 'k/launch.json').read_text()); la.update(status='READY', production_authorized=True)
dk.SealedOutput(final).write(final / 'k/launch.json', la)
def manifest(tree):
    return dict(reversed(line.split('  ', 1)) for line in (tree / 'SHA256SUMS.txt').read_text().splitlines())
man = manifest(final); man['k/launch.json'] = dk.sha(final / 'k/launch.json')
dk.SealedOutput(final).text(final / 'SHA256SUMS.txt', ''.join(h + '  ' + n + '\n' for n, h in sorted(man.items())))
source = (H / 'payload/r.py').read_text()
start = source.index(' # Compare the complete'); end = source.index(' # Separate ANON', start)
block = '\n'.join(line[1:] for line in source[start:end].splitlines())
scope = dict(B=new, o=over, dk=dk, base=base, KH=final, manifest=manifest,
             load=lambda p: json.loads(p.read_text()))
with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
        patch.object(Path, 'iterdir', guarded_iterdir):
    exec(block, scope)
# Runtime mode changes do not affect comparison; member and ancestor changes do.
(final / 'o/runtime').write_text('not a member\n'); (final / 'o').chmod(0o500)
mode_line = next(line.strip() for line in block.splitlines() if 'assert dk.mode_inventory' in line)
exec(mode_line, scope)
for name in ('b/r.sh', 'b/sa', 'k/4.json', 'job.sh', '.'):
    p = final / name; mode = stat.S_IMODE(p.stat().st_mode); p.chmod(mode ^ 0o200)
    try:
        try: exec(mode_line, scope)
        except AssertionError: pass
        else: raise AssertionError('member mode mismatch accepted: ' + name)
    finally: p.chmod(mode)
assert before_sealed == {n: dk.sha(base / n) for n in members}
assert all(metadata(base)[n] == v for n, v in before_modes.items())
result['final_comparison_and_mode_negatives'] = 'PASS'
result['source_sealed_bytes_and_modes_unchanged'] = 'PASS'
# Exercise the real certify entry and native exact-executable-inventory check.
# This certificate is test data in the fixture, never an operator attestation.
kh = root / ('x_' + ids['tokens']['kit']); final.rename(kh)
cert_mode = stat.S_IMODE((kh / 'ANON_OK.json').stat().st_mode)
(new / 'anon.json').write_text(json.dumps(dict(status='CLEAN', hits=0,
    manifest_sha256=dk.sha(kh / 'SHA256SUMS.txt'), external=[])))
rc = subprocess.run([sys.executable, '-B', str(new / 'r.py'), 'certify'], capture_output=True, text=True)
assert rc.returncode == 0, rc.stderr
assert stat.S_IMODE((kh / 'ANON_OK.json').stat().st_mode) == cert_mode
assert json.loads((kh / 'ANON_OK.json').read_text())['status'] == 'CLEAN'
result['certify_and_native_inventory_with_test_certificate'] = 'PASS'
result['status'] = 'PASS'
(H / 'evidence/fix4_listing.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
