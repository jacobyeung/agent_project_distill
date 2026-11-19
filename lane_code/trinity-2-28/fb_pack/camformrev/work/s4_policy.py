"""(6) policy-pin refusals and (7) receipt counts with reader refusals, against tree_C."""
from pathlib import Path
import sys, json, gzip, sqlite3, hashlib, copy
from unittest.mock import patch
W = Path(__file__).resolve().parent
sys.path.insert(0, str(W/'tree_C')); sys.dont_write_bytecode = True
import torch; torch.set_num_threads(8)
from student_pilot.r1_camera_trace_form import CameraTraceForm
from student_pilot.p3_provenance import file_pin
from student_pilot import r1_routing
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
T = W/'policy_cases'; T.mkdir(exist_ok=True)
POL = W/'tree_C/configs/r1_camera_trace_form_v1.json'
good = file_pin(POL); raw = POL.read_bytes(); val = json.loads(raw)
def put(name, data):
    p = T/name
    if not p.exists(): p.write_bytes(data)
    return file_pin(p)
def attempt(pin):
    try:
        CameraTraceForm(pin); return 'ACCEPTED'
    except Exception as e:
        return 'refused:'+type(e).__name__+':'+str(e)[:70]
cases = {
 'good': good,
 'none': None, 'false': False, 'empty': {}, 'string': 'v1', 'list': [good['path'], good['sha256']],
 'extra_key': {**good, 'bytes': len(raw)}, 'missing_sha': {'path': good['path']},
 'wrong_sha': {**good, 'sha256': '0'*64}, 'relative_path': {'path': 'configs/r1_camera_trace_form_v1.json', 'sha256': good['sha256']},
 'missing_file': {'path': str(T/'nope.json'), 'sha256': good['sha256']},
 'stale_pin_changed_bytes': {'path': put('changed_stale.json', raw+b' ')['path'], 'sha256': good['sha256']},
 'rule_order_swapped': put('swap.json', json.dumps({**val, 'rule_ids': val['rule_ids'][::-1]}).encode()),
 'extra_rule': put('extra.json', json.dumps({**val, 'rule_ids': val['rule_ids']+['X']}).encode()),
 'input_hash_changed': put('inhash.json', json.dumps({**val, 'input_sha256': {**val['input_sha256'], 'fbp_cam/work/common.py': '1'*64}}).encode()),
 'extra_field': put('extrafield.json', json.dumps({**val, 'note': 'x'}).encode()),
 'duplicate_key': put('dup.json', raw.replace(b'"schema"', b'"schema": "x", "schema"', 1)),
 'reformatted_same_json': put('reformat.json', json.dumps(val, separators=(',', ':')).encode()),
 'key_reordered_same_json': put('reorder.json', json.dumps(dict(reversed(list(val.items()))), indent=4).encode()),
}
res = {k: attempt(v) for k, v in cases.items()}
res['reformatted_sha'] = cases['reformatted_same_json']['sha256']
# Refusal through compose leaves no output directory.
def compose(rows, cfg, out, refuse_qid=None):
    db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i, r in enumerate(rows): db.execute('INSERT INTO rows VALUES(?,?,?)', (i, json.dumps(r), '{}'))
    db.commit(); p = T/(out+'.sqlite'); p.write_bytes(db.serialize()); db.close()
    bp = T/(out+'_base.json'); bp.write_text(json.dumps(dict(schema=ROUTING_SCHEMA, scene_role='train', heldout_overlap=0, database=file_pin(p), division=None)))
    with patch.object(r1_routing, 'Filters') as f:
        f.return_value.reason.side_effect = lambda row, s: 'test_excluded' if row['qid'] == refuse_qid else None
        return r1_routing.compose(file_pin(bp), {}, (), cfg, T/out)
src = []
with gzip.open(W.parents[1]/'ro/orch_n30/sb_rowA/out/CAMERA_SOURCES.jsonl.gz', 'rt') as f:
    for line in f:
        r = json.loads(json.loads(line)['row'])
        t = r['routing']['question_type']
        if sum(x['routing']['question_type'] == t for x in src) < 3: src.append(r)
        if len(src) == 9: break
try:
    compose(src, dict(r1_training=dict(routing_slices='deferred_first_boundary', camera_trace_form=cases['wrong_sha'])), 'bad_pin_out')
    res['compose_bad_pin'] = 'ACCEPTED'
except ValueError as e:
    res['compose_bad_pin'] = 'refused:'+str(e)[:60]
res['compose_bad_pin_output_exists'] = (T/'bad_pin_out').exists()
# One rotation and one direction row refused by the native reader (row_text_audit pattern in the question text
# is not read; put it in a non-camera field the audit reads: the target's answer suffix is fixed, so use the qid filter
# for one row and a reader refusal for another via a gravity_guard token in a plan event of an unchanged type).
rows = copy.deepcopy(src)
rot = [r for r in rows if r['routing']['question_type'] == 'camera_rotation']
dirs = [r for r in rows if r['routing']['question_type'] == 'camera_movement_direction']
from student_pilot.carrier_c1_routing import render
bad = rot[1]; bad['routing']['events'][0]['text'] += ' gravity guard'
bad['target'], sp = render(bad['routing']['events'], bad['routing']['answer'])
for s, n in zip(bad['routing']['tool_output_spans'], sp): s.update(start=n['start'], end=n['end'])
out = compose(rows, dict(r1_training=dict(routing_slices='deferred_first_boundary', camera_trace_form=good)), 'refusal_counts', refuse_qid=dirs[0]['qid'])
res['refusal_receipt'] = dict(count=out['count'], refused=out['refused'], camera=out['camera_trace_form'])
c = sqlite3.connect('file:'+out['database']['path']+'?mode=ro', uri=True)
res['refusal_db_qids'] = [json.loads(r)['qid'] for (r,) in c.execute('SELECT row FROM rows ORDER BY i')]
res['refused_qids'] = [bad['qid'], dirs[0]['qid']]
(W/'S4_POLICY.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
