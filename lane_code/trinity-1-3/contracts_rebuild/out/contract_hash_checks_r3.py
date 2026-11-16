"""Hash verification and hash-selected patch plan; no tree mutations."""
import hashlib,json,sys
from pathlib import Path
packet=Path(__file__).resolve().parent
manifest=json.loads((packet/'PATCH_MANIFEST_R3.json').read_text())
root=Path(sys.argv[2]).resolve()
def sha(path):
    if path.is_symlink():raise SystemExit('Refuse symbolic link: '+str(path))
    if not path.exists():return None
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def check(path,expected):
    actual=sha(path)
    if actual!=expected:raise SystemExit(f'Hash mismatch: {path}: expected {expected}, got {actual}')
if sys.argv[1]=='writable':
    import os, stat
    for p in (root, root.parent):
        if not stat.S_IMODE(p.stat().st_mode) & 0o222 or not os.access(p, os.W_OK | os.X_OK):
            raise SystemExit('target_not_writable: '+str(p)+'; staging not created')
    for p in root.rglob('*'):
        if p.is_symlink():
            raise SystemExit('target_symbolic_link: '+str(p)+'; staging not created')
        if not stat.S_IMODE(p.stat().st_mode) & 0o222 or not os.access(p, os.W_OK):
            raise SystemExit('target_not_writable: '+str(p)+'; staging not created')
elif sys.argv[1]=='pre':
    selected={g:f'PATCH_{g}_r3.diff' for g in ('geometry','candidates','box')}
    for rel,e in manifest['files'].items():
        p=root/rel
        if not p.resolve().is_relative_to(root):raise SystemExit('Unsafe path: '+rel)
        actual=sha(p)
        if actual==e['base_sha256']:continue
        accepted=next((a for a in e.get('accepted_integration_bases',[]) if actual==a['base_sha256']),None)
        if accepted is None:raise SystemExit(f'Hash mismatch: {rel}: {actual}; refuses changed or already patched file')
        selected[e['patch']]=accepted['patch_file']
    for name in selected.values():
        check(packet/name,manifest['patch_sha256'][name]);print(name)
elif sys.argv[1]=='stage-changed':
    import shutil
    stage=Path(sys.argv[3]); stage.mkdir()
    for rel in manifest['files']:
        source=root/rel
        if source.exists():
            dest=stage/rel; dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
elif sys.argv[1]=='post':
    selected=Path(sys.argv[3]).read_text().splitlines()
    for rel,e in manifest['files'].items():
        expected=e['patched_sha256']
        for a in e.get('accepted_integration_bases',[]):
            if a['patch_file'] in selected:expected=a['patched_sha256']
        check(root/rel,expected)
elif sys.argv[1]=='inventory':
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise SystemExit('Refuse symbolic link: '+str(p))
        if p.is_file():print(sha(p)+'  '+p.relative_to(root).as_posix())
else:raise SystemExit('Unknown hash check')
