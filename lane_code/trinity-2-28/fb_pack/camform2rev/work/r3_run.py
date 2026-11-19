"""Run one declaration-mode composition in a fresh process.

Usage: r3_run.py TREE(A|C|A2|C2) MODE(absent|on) KIND(prod|mixed) OUT
Filters are mocked to admit (they need production exclusion files); Rows.row reader checks run natively.
EXTRA_PINS['camera_wording'] is bound to the delivered e8cbda99 source, as in the build's harness.
"""
from pathlib import Path
import sys, json, hashlib
from unittest.mock import patch
W = Path(__file__).resolve().parent
RO = W.parents[1]/'ro/orch_n30'
tree, mode, kind, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(W/('tree_'+tree))); sys.dont_write_bytecode = True
import torch; torch.set_num_threads(8)
from student_pilot import r1_routing
from student_pilot.r1_coverage import EXTRA_PINS, deferred
from student_pilot.p3_provenance import file_pin
D = W/'compose'
src = file_pin(RO/'fb_pack/cam/out/rows/camera_wording.jsonl' if kind == 'prod' else D/'empty.jsonl')
items = [dict(row=json.loads(l), target={}) for l in Path(src['path']).read_text().splitlines()]
r1 = dict(routing_slice_declaration=file_pin(D/'decl.json'))
if mode == 'on':
    r1['camera_trace_form'] = file_pin(W/('tree_'+tree)/'configs/r1_camera_trace_form_v1.json')
cfg = dict(r1_training=r1)
assert deferred(cfg) is False
seen = []
def reason(row, stream):
    if 'r1_source' not in row: seen.append(hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest())
    return None
with patch.dict(EXTRA_PINS, {'camera_wording': src['sha256']}), patch.object(r1_routing, 'Filters') as f:
    f.return_value.reason.side_effect = reason
    res = r1_routing.compose(file_pin(D/(kind+'_base.json')), {'camera_wording': src},
                             [('camera_wording', src, items, file_pin(D/'intake.json'))], cfg, out)
Path(str(out)+'.filters.json').write_text(json.dumps(seen))
print(json.dumps({k: v for k, v in res.items() if k in ('count', 'per_source', 'refused', 'camera_trace_form')})[:3000])
