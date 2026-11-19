"""ORCH ORDER 0422Z item 4: held-out evaluation set on unexposed rooms. Each of R0-dev's 290 routed absolute-distance items
(R0_QUESTIONS_dev_f32.jsonl b4e278f2; all in the routed wording, metres) gets one HELD-OUT wording (SPLIT_V2.json) and one unit
by a seeded rule (units balanced 73/73/72/72 by sha256 rank; wordings cycled within each unit, about 9 per wording and unit);
the ground truth is converted exactly from gt.distance_m (Decimal; m x1, ft /0.3048, in /0.0254, cm x100); the original item
is kept as its twin. Output follows the routed read's R0 item fields (as in room134.json). Evaluation only."""
import json, hashlib, sys
from decimal import Decimal, getcontext
getcontext().prec = 40
SRC = '/scratch/jjyeung/orch_n30/cont_ops20_b/hd400/validation/d_finish_dzss590z/test2/B5src/inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl'
split = json.load(open(sys.argv[1])); held = split['held_out']
UNITS = [('m', 'meters', Decimal(1)), ('ft', 'feet', 1 / Decimal('0.3048')), ('in', 'inches', 1 / Decimal('0.0254')), ('cm', 'centimeters', Decimal(100))]
raw = open(SRC, 'rb').read(); src_sha = hashlib.sha256(raw).hexdigest()
rows = []
for n, line in enumerate(raw.decode().splitlines(), 1):
    r = json.loads(line)
    if r.get('question_type') == 'object_abs_distance': rows.append((n, r))
assert len(rows) == 290 and src_sha.startswith('b4e278f2')
h = lambda tag, q: hashlib.sha256(('dist_diag|r0ho|%s|%s' % (tag, q)).encode()).hexdigest()
order = sorted(rows, key=lambda x: h('unit', x[1]['qid']))
groups = {u[0]: [] for u in UNITS}
for i, x in enumerate(order): groups[UNITS[i % 4][0]].append(x)
items, re_ids, twin_ids = [], [], []
def base(r, line):
    ds, sc = r['dataset'], r['scene']
    return dict(answer_type='numeric', dataset=ds, development_only=True, fps=r['fps'], frame_indices=r['frame_indices'],
                gen_version=r['gen_version'], native='%s/%s' % (ds, sc), num_frames=r['num_frames'], options=[], question_type='object_abs_distance',
                r0_split=r['r0_split'], room='%s/%s' % (ds, sc), room_key='%s/%s' % (ds, sc), scene=sc, scorer='official_vsi_mra',
                source_frame_indices=r['frame_indices'], subtype=r['subtype'], total_num_frames=r['total_num_frames'],
                label_provenance=dict(label_field='gt.distance_m', line=line, source='inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl', source_qid=r['qid'], source_sha256=src_sha))
for code, word, fac in UNITS:
    for k, (line, r) in enumerate(sorted(groups[code], key=lambda x: h('wording', x[1]['qid']))):
        a, b = r['gt']['pair']; q0 = r['question']
        assert q0 == 'Measuring from the closest point of each object, what is the distance between the %s and the %s (in meters)?' % (a, b), q0
        wid = k % len(held); q = held[wid].format(a=a, b=b, u=word)
        gt_m = Decimal(repr(r['gt']['distance_m'])); gt_u = gt_m * fac
        it = base(r, line); it.update(id=r['qid'] + '_ho', qid=r['qid'] + '_ho', question=q, unit=code, ground_truth=float(gt_u),
            answer=str(gt_u.quantize(Decimal('0.01'))), gt=dict(r['gt'], converted=str(gt_u), unit_factor=str(fac), unit=code),
            twin_id=r['qid'], heldout_wording_id=wid, heldout_wording=held[wid])
        items.append(it); re_ids.append(it['id'])
        tw = base(r, line); tw.update(id=r['qid'], qid=r['qid'], question=q0, unit='m', ground_truth=r['gt']['distance_m'], answer=r['answer'], gt=r['gt'], twin_id=r['qid'] + '_ho')
        items.append(tw); twin_ids.append(tw['id'])
items.sort(key=lambda x: x['id'])
body = dict(name='r0dev_distance_heldout_v1', schema='dist-diag-heldout-items-v1', development_only=True, fitting_permitted=False,
            source=dict(path=SRC, sha256=src_sha), split=dict(rule=split['rule'], held_out=held),
            sets={'r0_heldout_reworded': sorted(re_ids), 'r0_routed_twins': sorted(twin_ids)}, count=len(items),
            per_unit_reworded={u[0]: len(groups[u[0]]) for u in UNITS}, items=items)
body['item_set_sha256'] = hashlib.sha256(json.dumps(sorted(i['id'] for i in items)).encode()).hexdigest()
blob = json.dumps(body, indent=1, sort_keys=True).encode()
open(sys.argv[2], 'wb').write(blob)
from collections import Counter
print('items', len(items), 'reworded', len(re_ids), 'twins', len(twin_ids), 'per unit', body['per_unit_reworded'],
      'wording x unit', sorted(Counter((i['heldout_wording_id'], i['unit']) for i in items if i['id'].endswith('_ho')).values())[:3], '...',
      'sha', hashlib.sha256(blob).hexdigest())
