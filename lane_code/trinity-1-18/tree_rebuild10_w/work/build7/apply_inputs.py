"""Apply reviewed input hunks only when their full context matches uniquely."""
import hashlib
import json
from pathlib import Path
import re

L = Path(__file__).resolve().parents[2]
B = L / 'work/build7'
T = L / 'work/tree_r1'
records = []
for filename, expected in (
    ('gf1_cache_on_b5_ba346bd9.patch', '3610e972cddcf25e7ceb345e3c761759b0d24408bc0a66cc412162db971267af'),
    ('h1_faithful_b5/faithful_own_rows.patch', 'cdc6c9f72fed4c0b9b107e8b2f105a2284a32b32075e650c99b8a8012ad47fbf'),
):
    raw = (L / 'work/design' / filename).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    lines = raw.decode().splitlines(keepends=True)
    i = 0
    while i < len(lines):
        if not lines[i].startswith('+++ b/'):
            i += 1
            continue
        name = lines[i][6:].split()[0]
        path = T / name
        original = path.read_text() if path.exists() else ''
        saved = B / 'before' / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        if not saved.exists():
            saved.write_text(original)
        content = original
        i += 1
        while i < len(lines) and lines[i].startswith('@@'):
            header = lines[i].strip()
            i += 1
            old, new = [], []
            while i < len(lines) and not lines[i].startswith(('@@', '--- ')):
                line = lines[i]
                if line.startswith((' ', '-')):
                    old.append(line[1:])
                if line.startswith((' ', '+')):
                    new.append(line[1:])
                i += 1
            old, new = ''.join(old), ''.join(new)
            hits = content.count(old) if old else int(not content)
            row = dict(patch=filename, file=name, hunk=header, matches=hits)
            if hits == 1:
                content = content.replace(old, new, 1) if old else new
                row.update(status='exact', reason='Full hunk context matches current tree')
            else:
                row.update(status='conflict', reason='Full context differs; requires manual adaptation', old=old, new=new)
            records.append(row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
(B / 'PATCH_HUNKS.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps({s: sum(r['status'] == s for r in records) for s in ('exact', 'conflict')}))
