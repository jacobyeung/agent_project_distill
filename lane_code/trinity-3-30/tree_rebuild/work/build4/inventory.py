from pathlib import Path
import json
root = Path(__file__).resolve().parents[2]
tmp = root / 'work/tmp'
tmp.mkdir(exist_ok=True)
assert not any(tmp.iterdir()), 'temporary directory must start empty'
sizes = {}
total = 0
for p in root.rglob('*'):
    if p.is_file() and not p.is_symlink():
        n = p.stat().st_size
        total += n
        key = '/'.join(p.relative_to(root).parts[:2])
        sizes[key] = sizes.get(key, 0) + n
result = {'total_bytes': total, 'groups': sizes}
(root / 'work/build4/INITIAL_STORAGE.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'total_bytes': total, 'largest_groups': sorted(sizes.items(), key=lambda x: -x[1])[:15]}))
assert total < 4_000_000_000
