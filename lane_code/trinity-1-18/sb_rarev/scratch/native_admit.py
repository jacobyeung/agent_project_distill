"""CPU-only native admission: h1eval.items.load_manifest + parity_adapter.map_items, then measure() on a stub output."""
import json, sys, traceback
sys.dont_write_bytecode = True
SRC = '/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src'
ROW = '/scratch/jjyeung/orch_n30/sb_rowA/out'
for p in (SRC + '/b', SRC):
    sys.path.insert(0, p)
from collections import Counter
from h1eval.items import load_manifest
m = load_manifest(ROW + '/HELDOUT_CAMERA_ITEMS.json')
print('load_manifest OK', m['name'], m['count'], m['per_type'], m['r0_check'])

for name in [n for n in sys.modules if n == 'e2e_reader' or n.startswith('e2e_reader.')]:
    del sys.modules[name]
sys.path.insert(0, SRC + '/b')
from h1eval.h10.parity_adapter import map_items
settings = dict(tasks=[ROW + '/HELDOUT_NATIVE_TASKS.jsonl'], frames_root='/scratch/jjyeung/devs1_frames')
try:
    mapped, mapping = map_items(m['items'], settings, name=m['name'])
    print('map_items OK', len(mapped), 'mapping', len(mapping['items']), 'unique keys', len({r['key'] for r in mapping['items']}))
except Exception as e:
    traceback.print_exc(); print('map_items FAIL', type(e).__name__, e)

# Scoring path used by h1eval/h10/merge.py -> runner.measure on a perfect stub output.
from h1eval import runner
res = Counter(); first_err = {}
for x in m['items']:
    i, j = x['display_frame_pair']
    name = 'turn' if x['question_type'] == 'camera_rotation' else 'move'
    call = f'<{name} from={i} to={j}>'
    resp = 'turn = +10 deg' if name == 'turn' else 'dx = +1.00 m, dy = +0.00 m, dz = +0.10 m, distance = 1.00 m'
    out = dict(text=f'<think>{call}</think><answer>{x["answer"]}</answer>', finish='eos',
               calls=[dict(call=call, response=resp, at_token=5, served=True)], tokens=[])
    rew = '-sbca-' in x['id']
    try:
        r = runner.measure(out, x)
        res[(rew, x['question_type'], 'ok', r['M1']['exact'])] += 1
    except Exception as e:
        res[(rew, x['question_type'], type(e).__name__ + ':' + str(e)[:60])] += 1
        first_err.setdefault(type(e).__name__, x['id'])
for k, v in sorted(res.items(), key=str): print(k, v)
print(first_err)
