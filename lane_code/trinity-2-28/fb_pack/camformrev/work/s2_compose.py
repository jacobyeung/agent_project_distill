"""Run r1_routing.compose from one tree. Usage: s2_compose.py A|C extract|mixed absent|on OUTDIR

Filters is replaced (no production division/exclusion pins exist locally); the
replacement records the digest of every row it sees so the caller can prove
Filters judges the unrewritten row.
"""
from pathlib import Path
import sys, json, os, hashlib
from unittest.mock import patch
W = Path(__file__).resolve().parent
tree, name, mode, out = sys.argv[1:5]
sys.path.insert(0, str(W/('tree_'+tree))); sys.dont_write_bytecode = True
import torch; torch.set_num_threads(8)
from student_pilot import r1_routing
from student_pilot.p3_provenance import file_pin, digest
assert Path(r1_routing.__file__).resolve().is_relative_to(W/('tree_'+tree))
base_path = W/'compose'/(name+'_base.json')
base_pin = file_pin(base_path)
r1 = dict(routing_slices='deferred_first_boundary')
if mode == 'on':
    r1['camera_trace_form'] = file_pin(W/'tree_C/configs/r1_camera_trace_form_v1.json')
cfg = dict(r1_training=r1)
seen = {}
def reason(row, stream):
    seen[row['qid']] = digest(row)
    return None
with patch.object(r1_routing, 'Filters') as filters:
    filters.return_value.reason.side_effect = reason
    result = r1_routing.compose(base_pin, {}, (), cfg, Path(out))
Path(str(out)+'.filters_seen.json').write_text(json.dumps(seen))
print(json.dumps({k: v for k, v in result.items() if k not in ('database',)}, sort_keys=True)[:3000])
