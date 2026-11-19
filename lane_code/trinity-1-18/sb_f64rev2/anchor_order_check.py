"""Adversarial fixture check, not a claim about the absent planned population."""
import copy
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
sys.path[:0] = [str(SRC / 'pkg/work/tree_f64'), str(ROOT.parent / 'sb_f64fix/kit/scripts')]
import nest_store
reads = {str(Path(__file__))}
def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        if (args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            if not p.is_relative_to(ROOT):
                raise RuntimeError('Write outside review: ' + str(p))
        elif p.is_relative_to(SRC) or p.is_relative_to(ROOT.parent / 'sb_f64fix'):
            reads.add(str(p))
sys.addaudithook(guard)
import torch
torch.set_num_threads(1)
from student_pilot import frame_input as F
from student_pilot.carrier_c1_data import layout_inputs

def first_row(layout):
    path = SRC / 'work/dryrun' / layout / 'a43/pose/rows.sqlite'
    reads.add(str(path))
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        return json.loads(db.execute('SELECT row FROM rows ORDER BY i LIMIT 1').fetchone()[0])

source, filled = first_row('n32'), first_row('f64')
source = copy.deepcopy(source)
# Reverse the complete source viewpoint order as an adversarial precondition test.
for key in ('frames', 'frame_indices', 'timestamps'):
    source['student_input'][key].reverse()
layout_inputs(source, 'duplicate', frame_count=32)
pins = dict(zip(filled['student_input']['frame_indices'], filled['student_input']['frames'], strict=True))
result = F.nest_row(source, pins)
F.check_row(result, F.NESTED)
before = source['student_input']['frame_indices']
after = [result['student_input']['frame_indices'][k] for k in result['student_input']['anchor_slots']]
try:
    nest_store.nest(source, pins, verify=lambda pin: None)
    boundary = dict(refused=False)
except ValueError as exc:
    boundary = dict(refused=True, reason=str(exc))
value = dict(converter_boundary=boundary, command='bash run_cpu.sh anchor_order_check.py',
    scope='Adversarial reversal of synthetic fixture input; not an authenticated planned-run example.',
    original_layout_gate_passed=True, nested_gate_passed=True,
    before_anchor_indices=before, after_anchor_indices=after,
    anchor_order_preserved=before == after,
    source_pose_record_unchanged=source['pose_sample'] == result['pose_sample'],
    input_sha256={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads) if Path(p).is_file()})
(ROOT / 'out/anchor_order_review.json').write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps({k: v for k, v in value.items() if k != 'input_sha256'}, indent=2))
