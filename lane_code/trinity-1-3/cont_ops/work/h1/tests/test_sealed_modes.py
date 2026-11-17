"""Exercise full derivation with sealed permissions, using only local CPU fixtures."""
import copy, hashlib, importlib.util, json, os, shutil, stat, sys, subprocess
from pathlib import Path

H = Path(__file__).resolve().parents[1]
D = Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
sys.path.insert(0, str(H / 'tools'))
import derive_kit_h1 as dk

root = H / 'evidence/fix4_sealed_modes'
root.mkdir()
assert os.geteuid() != 0, 'Permission regression must run without root privileges'
def load_module(path):
    spec = importlib.util.spec_from_file_location('old_deriver', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod
old = load_module(H / 'evidence/fix3_before/tools/derive_kit_h1.py')
def snapshot(path):
    return {str(p.relative_to(path)): [stat.S_IMODE(p.stat().st_mode),
            dk.sha(p) if p.is_file() else None] for p in [path, *sorted(path.rglob('*'))]}
def seal(kit, all_members=False):
    for p in kit.rglob('*'):
        if all_members or (p == kit / 'b' or kit / 'b' in p.parents):
            p.chmod(0o500 if p.is_dir() else 0o400)
    kit.chmod(0o700)
def validate_files(out):
    for line in (out / 'SHA256SUMS.txt').read_text().splitlines():
        h, n = line.split('  ', 1)
        assert dk.sha(out / n) == h, n
def unchanged_modes(kit, out):
    before, after = snapshot(kit), snapshot(out)
    before = {n: v for n, v in before.items() if n in dk.mode_inventory(kit)}
    for n, (mode, digest) in before.items():
        if n in after and (digest is None or digest == after[n][1]):
            assert after[n][0] == mode, n
def contract(out):
    mod = load_module(out / 'b/d.py')
    la = json.loads((out / 'k/launch.json').read_text())
    cfg = json.loads((out / la['config']['file']).read_text())
    return dk.digest(mod.contract(la, cfg))

# Complete stand-in: only the two unavailable payload bytes and manifest pin differ.
# This does not claim reproduction of the unavailable complete production kit.
seed = root / 'seed'; shutil.copytree(D / 'kitfull', seed)
lines = (seed / 'SHA256SUMS.txt').read_text().splitlines(); synthetic = []
for i, line in enumerate(lines):
    h, n = line.split('  ', 1)
    if not (seed / n).exists():
        (seed / n).write_bytes(b'local unavailable-payload stand-in\n')
        lines[i] = dk.sha(seed / n) + '  ' + n; synthetic.append(n)
assert len(synthetic) == 2
(seed / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n')
dk.SEALED_MANIFEST = old.SEALED_MANIFEST = dk.sha(seed / 'SHA256SUMS.txt')
h1 = json.loads((H / 'build/over_local.json').read_text()); h1.pop('fixture', None)
d0 = json.loads((D / 'a2/v5b/over_fx.json').read_text().replace(
    '/scratch/jjyeung/orch_n30/cont_ops/work/d0', str(D)))
d0.pop('fixture', None)
for h, p in d0['content'].items():
    if not Path(p).is_absolute(): d0['content'][h] = str(D / 'a2' / p)
ids = json.loads((H / 'ids.json').read_text())
result = {'synthetic_missing_payloads': synthetic, 'cases': {}}
for label, all_members in [('orchard', False), ('fully_sealed', True)]:
    kit = root / label; shutil.copytree(seed, kit); seal(kit, all_members)
    before = snapshot(kit)
    historical = copy.deepcopy(h1)
    for n in ('4.json', 'review.json', 'staging.json'):
        p = H / 'evidence/fix6_before/payload' / n
        historical['add_k'][n] = dict(path=str(p), sha256=dk.sha(p))
    try: old.derive(kit, root / (label + '_round2'), historical)
    except PermissionError as e:
        assert str(e.filename).endswith('/b/r.sh') if not all_members else True
        result['cases'][label + '_round2'] = {'expected_failure': str(e)}
    else: raise AssertionError('round-2 code unexpectedly accepted sealed writes')
    for name, overrides in [('h1', h1), ('d0', d0), ('empty', {})]:
        out = root / (label + '_' + name)
        r = dk.derive(kit, out, copy.deepcopy(overrides)); validate_files(out)
        unchanged_modes(kit, out)
        for n in ('b/r.sh', 'b/h.py', 'b/i.py', 'b/c.sh', 'b/p0.sh', 'job.sh'):
            assert (out / n).stat().st_mode == (kit / n).stat().st_mode
        if name == 'empty':
            actual = snapshot(out)
            assert {n: actual[n] for n in dk.mode_inventory(out)} == {n: before[n] for n in dk.mode_inventory(kit)}
            assert (out / 'SHA256SUMS.txt').read_bytes() == (kit / 'SHA256SUMS.txt').read_bytes()
        elif name == 'h1':
            assert r['config_identity'] == ids['identity'] and contract(out) == ids['contract']
        else:
            assert r['config_identity'].startswith('80f4af94') and contract(out).startswith('aaf2d7b0')
        assert snapshot(kit) == before, 'source bytes or modes changed'
        result['cases'][label + '_' + name] = {'status': 'PASS', 'identity': r['config_identity'],
            'modes_sha256': dk.digest(dk.mode_inventory(out))}

# New files/directories, failure restoration and out-of-tree guards.
out = root / 'fully_sealed_h1'; fs = dk.SealedOutput(out)
parent = out / 'b/sa'; before = snapshot(parent)
fs.text(parent / 'new.json', '{}\n', 0o400)
fs.mkdir(parent / 'new', 0o500); fs.text(parent / 'new/data', 'new\n')
assert (parent / 'new.json').stat().st_mode & 0o777 == 0o400
assert (parent / 'new').stat().st_mode & 0o777 == 0o500
assert parent.stat().st_mode & 0o777 == 0o500
p = out / 'b/r.sh'; modes = dk.mode_inventory(out)
try:
    with fs.writable(p):
        assert p.stat().st_mode & 0o200 and p.parent.stat().st_mode & 0o200
        raise RuntimeError('injected write failure')
except RuntimeError: pass
assert dk.mode_inventory(out) == modes
external = root / 'external'; external.write_text('unchanged'); external.chmod(0o400)
outside = snapshot(external.parent)['external']
link = out / 'link'; link.symlink_to(external)
dirlink = out / 'dirlink'; dirlink.symlink_to(root, target_is_directory=True)
for target in [external, link, dirlink / 'external', out / '..' / 'external']:
    try: fs.text(target, 'bad')
    except ValueError: pass
    else: raise AssertionError('outside/link write admitted')
assert [stat.S_IMODE(external.stat().st_mode), dk.sha(external)] == outside
result['guards_and_restore'] = 'PASS'
# Run the shipped prepare entry with only physical paths and the synthetic pin relocated.
bundle = root / 'entry'; bundle.mkdir(mode=0o700)
base = bundle / 'x_07ca49df'; shutil.copytree(root / 'fully_sealed', base)
packet = bundle / 'i_1be16f28'; packet.mkdir(mode=0o700)
source = (H / 'tools/derive_kit_h1.py').read_text().replace(
    "SEALED_MANIFEST = 'de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'",
    'SEALED_MANIFEST = ' + repr(dk.SEALED_MANIFEST))
(packet / 'd.py').write_text(source)
record_source = (H / 'tools/orchard_records.py').read_text()
(packet / 'r.py').write_text(record_source.replace(
    "O=Path('/project/community/jjyeung/okh7')", 'O=Path(' + repr(str(bundle)) + ')'))
(packet / 'ids.json').write_text(json.dumps(ids))
(packet / 'over.json').write_text(json.dumps(h1))
rc = subprocess.run([sys.executable, '-B', str(packet / 'r.py'), 'prepare'], capture_output=True, text=True)
assert rc.returncode == 0, rc.stderr
assert json.loads((packet / 'e.json').read_text())['modes_sha256'] == dk.digest(dk.mode_inventory(base))
# Execute the exact final comparison block against a sealed candidate and final kit.
final = root / 'final'; final_over = dict(h1, fixture=True, status='BLOCKED')
dk.derive(base, final, final_over)
la = json.loads((final / 'k/launch.json').read_text()); la.update(status='READY', production_authorized=True)
dk.SealedOutput(final).write(final / 'k/launch.json', la)
def manifest(root):
    return dict(reversed(line.split('  ', 1)) for line in (root / 'SHA256SUMS.txt').read_text().splitlines())
man = manifest(final); man['k/launch.json'] = dk.sha(final / 'k/launch.json')
dk.SealedOutput(final).text(final / 'SHA256SUMS.txt', ''.join(h + '  ' + n + '\n' for n, h in sorted(man.items())))
start = record_source.index(' # Compare the complete'); end = record_source.index(' # Separate ANON', start)
block = '\n'.join(line[1:] for line in record_source[start:end].splitlines())
scope = dict(B=packet, o=h1, dk=dk, base=base, KH=final, manifest=manifest,
             load=lambda p: json.loads(p.read_text()))
exec(block, scope)
assert (packet / 'q/k/launch.json').stat().st_mode & 0o777 == 0o400
# A mode-only difference must fail the shipped final comparison despite equal byte manifests.
mode_line = next(line.strip() for line in block.splitlines() if 'assert dk.mode_inventory' in line)
(final / 'b/r.sh').chmod(0o600)
try: exec(mode_line, scope)
except AssertionError: pass
else: raise AssertionError('mode-only mismatch accepted')
(final / 'b/r.sh').chmod(0o400)
# Certification must also replace a sealed existing certificate without changing its mode.
cert_line = next(line.strip() for line in record_source.splitlines() if "dk.SealedOutput(KH).write" in line)
exec(cert_line, dict(dk=dk, KH=final, cert={'status': 'TEST'}))
assert (final / 'ANON_OK.json').stat().st_mode & 0o777 == 0o400
result['prepare_final_and_certify_writes'] = 'PASS'
(H / 'evidence/fix4_sealed_modes.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
