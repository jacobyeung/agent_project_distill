"""Self-check of a regenerated mode-r selection against the reviewed one (not the task-A verdict; n_review1l owns that).

Usage: python -I cmp_sel.py NEW_DIR [REF_DIR [REF_DISCOVERY_DIR]]
NEW_DIR: fetched X/o/<job> of the new CPU run (x2.tgz extracted beside it as x2/ if present).
REF_DIR: reviewed CPU run 173881 outputs; REF_DISCOVERY_DIR: discovery 173912 outputs (source and pool receipts).
A differing leaf is EXPECTED when it is the implementation entry of student_pilot/r1_training.py, or when its
reference value is the sha256 of a published file whose bytes changed (a derived digest), or the selection's
config_sha256 (digest of the in-job config, which pins k/7.json). Everything else is UNEXPECTED.
"""
import hashlib, json, sys, tarfile
from pathlib import Path

F = Path('/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22/in/work')
NEW = Path(sys.argv[1])
REF = Path(sys.argv[2]) if len(sys.argv) > 2 else F / 'd173881/173881'
DISC = Path(sys.argv[3]) if len(sys.argv) > 3 else F / 'd173912/173912'
R1 = 'student_pilot/r1_training.py'


def walk(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, p + '/' + k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, p + '[%d]' % i)
    else:
        yield p, x


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


if (NEW / 'x2.tgz').is_file() and not (NEW / 'x2').exists():
    with tarfile.open(NEW / 'x2.tgz') as t:
        t.extractall(NEW / 'x2', filter='data')
pairs = [(n, REF / n, NEW / n) for n in ('routing_selection.json', 'receipt.json', 'materialization.json', 'k_refresh.json',
                                        'k_b1r.json', 'k_b1m.json', 'k_b2r.json', 'k_b2m.json', 'k_b5r.json', 'db_bytes.json')]
pairs += [(n, DISC / n, NEW / n) for n in ('k_dr_p_q_sc_p_p_receipt.json', 'k_dr_p_q_selection_pool_receipt.json')]
changed_refs = {}
for name, a, b in pairs:
    if a.is_file() and b.is_file() and sha(a) != sha(b):
        changed_refs[sha(a)] = name
out = dict(files={}, unexpected=[], expected_counts={}, missing=[])
for name, a, b in pairs:
    if not (a.is_file() and b.is_file()):
        out['missing'].append(name)
        continue
    da, db = dict(walk(json.loads(a.read_bytes()))), dict(walk(json.loads(b.read_bytes())))
    diff = [k for k in sorted(set(da) | set(db)) if da.get(k) != db.get(k)]
    out['files'][name] = dict(ref=sha(a), new=sha(b), equal=sha(a) == sha(b), leaves=len(da), differing=len(diff))
    for k in diff:
        ov = da.get(k)
        if k.endswith('/' + R1) or (isinstance(ov, str) and ov in changed_refs) or k == '/inputs_pinned/config_sha256' or k == '/regenerated_sha256':
            why = 'r1_training' if k.endswith('/' + R1) else 'config' if k.endswith('config_sha256') else 'digest of ' + changed_refs.get(ov, 'receipt.json')
            out['expected_counts'][name + ' <- ' + why] = out['expected_counts'].get(name + ' <- ' + why, 0) + 1
        else:
            out['unexpected'].append(dict(file=name, path=k, ref=str(ov)[:120], new=str(db.get(k))[:120]))
db = json.loads((NEW / 'db_bytes.json').read_bytes()) if (NEW / 'db_bytes.json').is_file() else {}
sel = {f['path']: f for f in db.get('files', [])}
s = json.loads((NEW / 'routing_selection.json').read_bytes()) if (NEW / 'routing_selection.json').is_file() else {}
r = json.loads((REF / 'routing_selection.json').read_bytes())
out['checks'] = {
    'selection_db_5e35c3ce': sel.get('dr/p/q/selection/rows.sqlite', {}).get('sha256', '').startswith('5e35c3ce'),
    'selection_db_bytes_849543168': sel.get('dr/p/q/selection/rows.sqlite', {}).get('size') == 849543168,
    'p_db_equal_target_4e8e6c04': db.get('equal_target') is True and db.get('expected', '').startswith('4e8e6c04'),
    'rows_43101': s.get('rows') == 43101,
    'row_id_digest_equal': s.get('row_id_digest') == r['row_id_digest'],
    'row_bytes_sha256_equal': s.get('row_bytes_sha256') == r['row_bytes_sha256'],
    'p_regeneration_equal': s.get('p_regeneration') == r['p_regeneration'],
    'no_unexpected_leaf': not out['unexpected'],
}
out['new_pins'] = dict(routing_selection_sha256=sha(NEW / 'routing_selection.json') if s else None,
                       regenerated_sha256=s.get('regenerated_sha256'), receipt_sha256=out['files'].get('receipt.json', {}).get('new'),
                       materialization_sha256=out['files'].get('materialization.json', {}).get('new'))
out['status'] = 'PASS' if all(out['checks'].values()) and not out['missing'] else 'FAIL'
(NEW.parent / ('CMP_' + NEW.name + '.json')).write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(dict(status=out['status'], checks=out['checks'], missing=out['missing'], new_pins=out['new_pins'],
                      expected=out['expected_counts'], unexpected=out['unexpected'][:20]), indent=1))
