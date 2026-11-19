"""Production-shaped compose (routing_slice_declaration, camera_wording bound with the real fbp_cam rows).

Usage: s7_declaration.py build | run A|C absent|on OUT | check
"""
from pathlib import Path
import sys, json, gzip, sqlite3, hashlib, random
from unittest.mock import patch
W = Path(__file__).resolve().parent
RO = W.parents[1]/'ro/orch_n30'; CAM = RO/'fb_pack/cam/out'
D = W/'decl'; D.mkdir(exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
cmd = sys.argv[1]
tree = sys.argv[2] if cmd == 'run' else 'C'
sys.path.insert(0, str(W/('tree_'+tree))); sys.dont_write_bytecode = True
import torch; torch.set_num_threads(8)
from student_pilot.p3_provenance import file_pin
if cmd == 'build':
    from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
    forms = json.loads((CAM/'SOURCE_FORMS.json').read_text()); m = {r['source_qid']: r['training_qid'] for r in forms['records']}
    peers = {}
    with (CAM/'rows/camera_wording.jsonl').open() as f:
        for line in f:
            r = json.loads(line); peers[r['qid']] = line
    base, pick = [], []
    random.seed(7)
    with gzip.open(RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz', 'rt') as f:
        allrows = [json.loads(l) for l in f]
    by = {}
    for e in allrows:
        r = json.loads(e['row']); by.setdefault(r['routing']['question_type'], []).append((e, r))
    for t, items in by.items():
        for e, r in random.sample(items, 400):
            base.append((e['row'], e['target']))
            if m[r['qid']] in peers: pick.append(peers[m[r['qid']]])
    db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i, (r, t) in enumerate(base): db.execute('INSERT INTO rows VALUES(?,?,?)', (i, r, t))
    db.commit(); (D/'base.sqlite').write_bytes(db.serialize()); db.close()
    (D/'base.json').write_text(json.dumps(dict(schema=ROUTING_SCHEMA, scene_role='train', heldout_overlap=0, database=file_pin(D/'base.sqlite'), division=None)))
    (D/'slice.jsonl').write_text(''.join(pick))
    decl = dict(schema='r1-routing-slices-v1', bound=['camera_wording'],
                deferred={k: 'review fixture: not bound' for k in ('absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery')})
    (D/'decl.json').write_text(json.dumps(decl)); (D/'intake.json').write_text(json.dumps(dict(note='review fixture intake')))
    print(len(base), len(pick))
elif cmd == 'run':
    mode, out = sys.argv[3], Path(sys.argv[4])
    from student_pilot import r1_routing
    from student_pilot.r1_coverage import EXTRA_PINS
    src = file_pin(D/'slice.jsonl')
    items = [dict(row=json.loads(l), target={}) for l in (D/'slice.jsonl').read_text().splitlines()]
    r1 = dict(routing_slice_declaration=file_pin(D/'decl.json'))
    if mode == 'on': r1['camera_trace_form'] = file_pin(W/'tree_C/configs/r1_camera_trace_form_v1.json')
    with patch.dict(EXTRA_PINS, {'camera_wording': src['sha256']}), patch.object(r1_routing, 'Filters') as f:
        f.return_value.reason.return_value = None
        res = r1_routing.compose(file_pin(D/'base.json'), {'camera_wording': src}, [('camera_wording', src, items, file_pin(D/'intake.json'))], dict(r1_training=r1), out)
    print(json.dumps({k: v for k, v in res.items() if k in ('count', 'per_source', 'refused', 'camera_trace_form')})[:2500])
else:
    rows = lambda p: [(json.loads(r), t) for r, t in sqlite3.connect('file:'+str(p)+'?mode=ro', uri=True).execute('SELECT row,target FROM rows ORDER BY i')]
    res = {}
    for f in ('rows.sqlite', 'membership.json', 'receipt.json'):
        res['absent_'+f] = sha((D/'A_absent'/f).read_bytes()) == sha((D/'C_absent'/f).read_bytes())
    old, new = rows(D/'A_absent/rows.sqlite'), rows(D/'C_on/rows.sqlite')
    forms = json.loads((CAM/'SOURCE_FORMS.json').read_text()); m = {r['source_qid']: r['training_qid'] for r in forms['records']}
    slice_same = sum(a == b for (a, _), (b, _) in zip(old, new) if 'r1_source' in a)
    base_changed = sum(a != b for (a, _), (b, _) in zip(old, new) if 'r1_source' not in a)
    targets = {b['qid']: b['target'] for b, _ in new}
    pairs = [(b['qid'], m[b['qid']]) for b, _ in new if 'r1_source' not in b and m[b['qid']] in targets]
    res.update(rows=len(new), slice_rows=sum('r1_source' in a for a, _ in old), slice_rows_unchanged=slice_same, base_rows_changed=base_changed,
               base_slice_pairs=len(pairs), pairs_same_target_on=sum(targets[a] == targets[b] for a, b in pairs),
               pairs_same_target_absent=sum(dict((x['qid'], x['target']) for x, _ in old)[a] == dict((x['qid'], x['target']) for x, _ in old)[b] for a, b in pairs),
               receipt_on=json.loads((D/'C_on/receipt.json').read_text()).get('camera_trace_form', {}).get('rewritten_base_rows_by_type'),
               target_column_same=all(ta == tb for (_, ta), (_, tb) in zip(old, new)))
    (W/'S7_DECLARATION.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
