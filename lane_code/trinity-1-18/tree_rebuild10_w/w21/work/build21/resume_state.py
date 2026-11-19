from pathlib import Path
import json, datetime, shutil, subprocess
B = Path(__file__).resolve().parent
L = B.parents[1]
def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
value = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             workspace=size(L), temporary=size(L/'work/tmp'),
             capacity=size(B/'proofs/capacity'), free=shutil.disk_usage('/scratch').free)
subprocess.run(['df', '-BG', '--output=avail', '/scratch'], check=True)
assert value['temporary'] <= 200_000_000
assert value['capacity'] <= 3_000_000_000
assert value['free'] >= 85*1024**3
(B/'RESUME_STORAGE.json').write_text(json.dumps(value, indent=2)+'\n')
print(json.dumps(value))
