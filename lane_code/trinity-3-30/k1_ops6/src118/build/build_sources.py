"""Build a bounded, byte-preserving source bundle from explicit pin maps."""
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
NATIVE = Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2')
TREE = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
TOWER = Path('/scratch/jjyeung/k1/run_tower_sam_2/BINDING.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    pins = json.loads((KIT / 'out/DEPENDENCIES.json').read_text())
    paths = {Path(p): 'dependency pin' for p in pins}
    tree = json.loads((NATIVE / 'RUNTIME_TREE.json').read_text())['sources']
    paths.update({TREE / p: 'authenticated runtime tree' for p in tree})
    # Single-directory listings only; every recursive runtime dependency is named
    # by the authenticated map above, rather than found by a repository scan.
    paths.update({p: 'native reader module' for p in NATIVE.iterdir() if p.suffix == '.py'})
    paths[NATIVE / 'RUNTIME_TREE.json'] = 'runtime tree pin map'
    paths.update({NATIVE / 'mask_kit' / p: 'native import dependency' for p in (
        'kit_combo3.tar.gz', 'kitlib.py', 'variantlib.py', 'vendor/phrase.py')})
    paths.update({KIT / p: 'kit input' for p in (
        'out/DEPENDENCIES.json', 'out/CAPTURES.json', 'out/K1_RULES.json',
        'out/K1_RULES.sha256', 'native_kit/vendor_sam/vendor/SAM3_RECEIPT.json')})
    opened = json.loads((ROOT / 'evidence/OPENED.json').read_text())['files']
    for p in opened:
        if '__pycache__' not in p and 'REQUIRED_LOCAL_' not in p:
            paths[Path(p)] = paths.get(Path(p), 'recorded preflight input')
    paths[MANIFEST] = 'unaltered manifest'
    paths[TOWER] = 'reference phase binding'
    # The six eligibility files resolve through gate.ROOT, independently of kc.
    import sys
    sys.path.insert(0, str(KIT / 'work'))
    import gate
    for p in gate.INPUTS[:6]:
        paths[gate.ROOT / p] = 'eligibility authority'
    source_map, content = {}, {}
    total = 0
    for path, reason in sorted(paths.items(), key=lambda item: str(item[0])):
        if not path.is_absolute() or not str(path).startswith('/scratch/jjyeung/'):
            raise ValueError('Unexpected source path: ' + str(path))
        size = path.stat().st_size
        if size > 20_000_000 or total + size > 100_000_000:
            raise ValueError('Source bundle exceeds its small-file budget')
        data = path.read_bytes()
        digest = sha(data)
        expected = pins.get(str(path))
        if path.is_relative_to(TREE):
            expected = tree[str(path.relative_to(TREE))]
        if expected is not None and digest != expected:
            raise ValueError('Pinned source differs: ' + str(path))
        member = 'sj/' + str(path.relative_to('/scratch/jjyeung'))
        # Keep both logical and resolved aliases as regular copies. B.source_identity
        # resolves native_kit.__file__, so the namespace must reproduce kc symlinks.
        source_map[str(path)] = dict(sha256=digest, bytes=size, member=member,
                                     resolved=str(path.resolve()), reason=reason)
        content[member] = data
        total += size
    if sha(MANIFEST.read_bytes()) != '91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c':
        raise ValueError('Manifest byte pin differs')
    out = ROOT / 'payload'
    out.mkdir(exist_ok=True)
    manifest_bytes = (json.dumps(source_map, sort_keys=True, indent=2) + '\n').encode()
    (out / 'ABSOLUTE_SHA256.json').write_bytes(manifest_bytes)
    archive = out / 'd64c8e20.tar'
    with archive.open('xb') as raw, tarfile.open(fileobj=raw, mode='w') as tar:
        for name, data in sorted({**content, 'ABSOLUTE_SHA256.json': manifest_bytes}.items()):
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode, entry.mtime = len(data), 0o644, 0
            tar.addfile(entry, io.BytesIO(data))
    result = dict(archive=archive.name, sha256=sha(archive.read_bytes()),
                  bytes=archive.stat().st_size, files=len(source_map), source_bytes=total,
                  complete_gpu_import_closure=False,
                  note='Authenticated source/input closure; production preparation and GPU imports remain unproved.')
    (out / 'PACKAGE.json').write_text(json.dumps(result, indent=2) + '\n')
    # Compare each copied kit byte sequence to its source without invoking Git.
    changed = [p for p, row in source_map.items() if str(KIT) in p
               and sha(content[row['member']]) != sha(Path(p).read_bytes())]
    if changed:
        raise ValueError('Kit copy changed: ' + repr(changed))
    (ROOT / 'evidence/kit.diff').write_text('')
    (ROOT / 'evidence/kit_comparison.json').write_text(json.dumps(dict(
        files=sum(str(KIT) in p for p in source_map), changed=changed), indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
