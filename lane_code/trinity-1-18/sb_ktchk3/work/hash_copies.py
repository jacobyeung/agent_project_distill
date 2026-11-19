import json
from pathlib import Path
W = Path(__file__).resolve().parent
src = (W/'verify_members.py').read_text().split('t = tarfile.open')[0].replace('Path(__file__)', 'Path(%r)' % str(W/'verify_members.py'))
g = {}; exec(src, g)
res = {n: g['dg'](g['pins'](p)) for n, p in [('live_sb_ktfix2', Path('/scratch/jjyeung/orch_n30/sb_ktfix2')), ('ex4', W/'ex4'), ('plant4', W/'plant4'), ('run4', W/'run4')]}
print(json.dumps(res, indent=1)); (W/'copy_hashes.json').write_text(json.dumps(res, indent=1))
