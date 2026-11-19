"""Apply each delivered patch and the ordered series to fresh, retained input copies."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'in/tree/work/tree_r1'
DEST = ROOT / 'work' / (sys.argv[1] if len(sys.argv) > 1 else 'verified')
PATCHES = sorted((ROOT / 'out/patches').glob('*.diff'))


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print('$ ' + ' '.join(map(str, args)), flush=True)
    print(result.stdout, end='', flush=True)
    print('EXIT_CODE: ' + str(result.returncode), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    command(['date', '-u'])
    DEST.mkdir()
    manifest = json.loads((ROOT / 'out/patches/manifest.json').read_text())
    for patch in PATCHES:
        payload = patch.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == manifest[patch.name]['sha256'], patch
        assert len(payload) == manifest[patch.name]['bytes'], patch
        tree = DEST / patch.stem
        shutil.copytree(SOURCE, tree, symlinks=True)
        command(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], tree)
    tree = DEST / 'combined'
    shutil.copytree(SOURCE, tree, symlinks=True)
    for patch in PATCHES:
        command(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], tree)
    count = 0
    for path in (ROOT / 'work/tree').rglob('*'):
        if path.is_file():
            relative = path.relative_to(ROOT / 'work/tree')
            assert path.read_bytes() == (tree / relative).read_bytes(), relative
            count += 1
    print(f'PATCH_PROOF: 3 independent clean applications; ordered series exact; {count} files match work/tree', flush=True)
    command(['date', '-u'])
