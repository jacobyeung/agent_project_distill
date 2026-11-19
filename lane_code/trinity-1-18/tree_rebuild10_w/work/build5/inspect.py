import json
import os
from pathlib import Path
L = Path(__file__).resolve().parents[2]
def size(root):
    total = 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in files:
            p = Path(parent)/name
            if not p.is_symlink():
                total += p.stat().st_size
    return total
parts = {p.name: size(p) for p in L.iterdir() if p.is_dir()}
record = dict(lane_bytes=sum(parts.values())+sum(p.stat().st_size for p in L.iterdir() if p.is_file()),
              parts=parts, tmp_bytes=size(L/'work/tmp'))
(L/'work/build5/INITIAL_STORAGE.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record))
data = json.loads((L/'work/build4/CHANGED_COVERAGE.json').read_text())
gaps = {}
for s in data['statements']:
    if not s['executed']:
        gaps.setdefault(s['file'], []).append((s['line'], s['text']))
(L/'work/build5/INITIAL_GAPS.json').write_text(json.dumps(gaps, indent=2)+'\n')
print(json.dumps({p:len(v) for p,v in gaps.items()}))
