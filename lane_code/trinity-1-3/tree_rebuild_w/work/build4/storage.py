from pathlib import Path
import json
import shutil
L=Path(__file__).resolve().parents[2]
def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
v=dict(lane_bytes=size(L),tmp_bytes=size(L/'work/tmp'),free_bytes=shutil.disk_usage('/scratch').free)
print(json.dumps(v))
assert v['lane_bytes']<4_000_000_000 and v['tmp_bytes']<=200_000_000 and v['free_bytes']>=190*1024**3
