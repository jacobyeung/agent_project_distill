import json, hashlib
from pathlib import Path
W = Path(__file__).resolve().parent
src = (W/'verify_members.py').read_text().split('t = tarfile.open')[0].replace("Path(__file__)", "Path(%r)" % str(W/'verify_members.py'))
g = {}; exec(src, g)
res = {n: g['dg'](g['pins'](W/n)) for n in ('ex3', 'plant3', 'run3', 'fixtry')}
print(json.dumps(res, indent=1)); (W/'copy_hashes.json').write_text(json.dumps(res, indent=1))
