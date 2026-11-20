"""Build a full 242-key hardlinked copy of the producer-format tree with the first frozen capture's served_depth_sha256
corrupted, for an end-to-end real-mode refusal run of build3 (run via run_real.py)."""
import json, os
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
FULL = W / 'tree/in/own_544_fov/native/probe'
DST = W / 'tree_refuse/native/probe'
first = json.loads(Path('/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json').read_text())['captures'][0]['key']
for d in sorted(FULL.iterdir()):
    (DST / d.name).mkdir(parents=True)
    for f in d.iterdir():
        if d.name == first and f.name == 'FOV_RECEIPT.json':
            r = json.loads(f.read_text()); r['served_depth_sha256'] = '0' * 64
            (DST / d.name / f.name).write_text(json.dumps(r, indent=2) + '\n')
        else:
            os.link(f, DST / d.name / f.name)
print('mutated', first, 'dirs', len(list(DST.iterdir())))
