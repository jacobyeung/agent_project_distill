"""Apply each independent patch and both patches to fresh copies of the sealed base."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess

L = Path(__file__).resolve().parents[1]
manifest = json.loads((L/'out/patches/manifest.json').read_text())
B = Path(manifest['base_tree'])
sha = lambda value: hashlib.sha256(value).hexdigest()

def inventory(root):
    files = {}
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(n for n in dirs if n not in ('.git', '__pycache__', 'artifacts'))
        for name in sorted(names):
            path = Path(directory)/name
            assert not path.is_symlink()
            files[str(path.relative_to(root))] = sha(path.read_bytes())
    return files

base = inventory(B)
seal = sha(json.dumps(base, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
assert seal == manifest['base_seal_full'], seal
for entry in manifest['patches']:
    assert sha((L/'out/patches'/entry['file']).read_bytes()) == entry['sha256']
    for file in entry['files']:
        assert base.get(file['path']) == file['base_sha256']
        assert sha((L/'work/tree'/file['path']).read_bytes()) == file['patched_sha256']

# Keep the complete prior delivery; no cleanup or deletion occurs.
(L/'work/delivery_tree').rename(L/'work/delivery_tree_initial')
results = []
for name, patches in [('review1_patch01', manifest['patches'][:1]),
                      ('review1_patch02', manifest['patches'][1:]),
                      ('delivery_tree', manifest['patches'])]:
    tree = L/'work'/name
    shutil.copytree(B, tree)
    expected = dict(base)
    for entry in patches:
        command = ['patch', '--batch', '--fuzz=0', '--no-backup-if-mismatch', '-p1',
                   '-i', str(L/'out/patches'/entry['file'])]
        result = subprocess.run(command, cwd=tree, capture_output=True, text=True)
        assert result.returncode == 0, result
        assert not any(word in result.stdout.lower() for word in ('offset', 'fuzz', 'reject'))
        results.append(dict(tree=name, patch=entry['file'], returncode=result.returncode,
                            stdout=result.stdout, stderr=result.stderr, command=command))
        expected.update({file['path']: file['patched_sha256'] for file in entry['files']})
    assert inventory(tree) == expected, name
    print('PATCH_APPLICATION '+name+' OK', flush=True)
assert inventory(L/'work/tree') == inventory(L/'work/delivery_tree')
changed = sorted(file['path'] for entry in manifest['patches'] for file in entry['files'])
report = dict(base_seal=seal, base_files=len(base), delivered_files=len(expected), changed=changed,
              native_parity_source_matches_delivery=True, no_backups_or_rejects=True)
(L/'out/tests/review1_patch_application.json').write_text(json.dumps(results, indent=2)+'\n')
(L/'out/tests/review1_delivery_verification.json').write_text(json.dumps(report, indent=2)+'\n')
print('PACKAGE_VERIFIED '+json.dumps(report, sort_keys=True), flush=True)
