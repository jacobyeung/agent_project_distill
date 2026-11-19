"""Real-data run of the kit's selection.select (unpatched converter, kernel, bootstrap) on the two K1-train
captures that already have 32-anchor CPU forwards (sb_rkfix out/s1/k1_32), against their stored dense-64 GPU
predictions. Only training_set is narrowed to those two rows. Writes only under ./kit/tmp and ./out."""
import json, shutil, sys, tempfile
from pathlib import Path
from unittest.mock import patch
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'kit/scripts'))
import common, gates, selection
from common import read, write, sha
W = common.W; assert W == H / 'kit'
SRC = Path('/scratch/jjyeung/orch_n30/sb_rkfix/out/s1/k1_32')
code = gates.run_code_hashes(); rows, caps, ins = selection.training_set()
pick = [r for r in rows if r['capture'] in ('scannetpp/067e2e4e61', 'scannetpp/036bce3393')]
assert len(pick) == 2, pick
root = Path(tempfile.mkdtemp(dir=W / 'tmp')) / 'out/room_pricing'
for r in pick:
    c = caps[r['capture']]; name = r['capture'].replace('/', '__'); src = SRC / name / 'pred.npz'
    dest = root / 'pred/k1_f32' / name; dest.mkdir(parents=True); shutil.copyfile(src, dest / 'pred.npz')
    binding = dict(frames=list(c['anchor_indices']), item_slots=list(range(32)), code_sha256=code)
    write(dest / 'DONE.json', dict(binding=binding, pred_sha256=sha(dest / 'pred.npz')), {str(src): sha(src)})
with patch.object(selection, 'training_set', lambda: (pick, caps, ins)):
    s = selection.select(root)
res = dict(arm_on_two_rows=s['arm'], interval=s['dense64_minus_f32'], rows=[
    dict(capture=r['capture'], gt=r['gt'], f32=r['f32']['area_m2'], f64=r['f64']['area_m2'], delta=r['delta']) for r in s['rows']],
    selection_input_files=len(s['input_sha256']))
print(json.dumps(res, indent=1)); json.dump(res, open(H / 'out/RK_S1C_REAL.json', 'w'), indent=1)
