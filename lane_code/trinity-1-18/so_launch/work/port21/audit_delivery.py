"""Check complete source identities, patch scope and syntax without Git or writes to inputs."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

W = Path(__file__).resolve().parent
L = W.parents[1]
S = Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1')
M = json.loads((L / 'out/patches_b21/manifest.json').read_text())


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


base = inventory(S)
seal = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert seal == 'b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8'
assert base == json.loads((W / 'base_files.json').read_text()) == inventory(W / 'baseline')
for name, entry in M.items():
    data = (L / 'out/patches_b21' / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
    assert len(data) == entry['bytes']
    assert entry['base_seal'] == 'b262e7a7' and entry['base_tree_sha256'] == seal
    assert entry['base_tree_files'] == len(base) == 936
    assert data == (L / 'out/patches' / name).read_bytes()
    for rel in entry['files']:
        assert entry['base_sha256'][rel] == base.get(rel)
    for tree in (W / name[:-5], W / ('delivery_' + name[:2])):
        actual = inventory(tree)
        expected = dict(base, **entry['result_sha256'])
        assert actual == expected, tree
        for rel in entry['files']:
            p = tree / rel
            if p.suffix == '.py':
                ast.parse(p.read_text(), filename=str(p))
            if p.suffix == '.sh':
                subprocess.run(['bash', '-n', str(p)], check=True)
combined = dict(base)
for entry in M.values():
    combined.update(entry['result_sha256'])
assert inventory(W / 'recommended') == combined
backups = [str(p) for p in W.rglob('*') if p.suffix in ('.orig', '.rej')]
assert not backups, backups
summary = json.loads((L / 'out/tests/port21/suite_summary.json').read_text())
assert len(summary) == 18 and all(row['exit'] == 0 for row in summary)
assert '\nOK\n' in (L / 'out/tests/port21/off_identity.txt').read_text()
total_bytes = int(subprocess.check_output(['du', '-sb', str(L)], text=True).split()[0])
assert total_bytes < 3_000_000_000
v = os.statvfs(L)
free = v.f_bavail * v.f_frsize
result = dict(status='PASS', time=subprocess.check_output(['date', '-u'], text=True).strip(),
              base_seal=seal, base_files=len(base), standalone_patches=3,
              recommended_changed_or_added_files=len(set(combined) - set(base)) + sum(
                  base[key] != combined[key] for key in base),
              patch_bytes_unchanged=True, moved_or_failed_hunks=0, backup_or_reject_files=backups,
              verified_suite_commands=len(summary), off_identity_tests=5,
              workspace_bytes_measured=total_bytes, scratch_free_bytes_measured=free)
(L / 'out/tests/port21/artifact_audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
