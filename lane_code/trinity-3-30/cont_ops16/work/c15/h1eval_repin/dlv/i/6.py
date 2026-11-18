"""Subset merge of an H1-0 return for the complete types only, using the package's own scorers.
Same checks as h1eval.h10.merge.merge(..., _types=ORDER) except: only the given type prefix must be present,
and the plan/union check is restricted to items of those types. Analysis only; not part of the package."""
import json, sys
from pathlib import Path
P = Path('/scratch/jjyeung/b01ec87a6f29b/p'); sys.path[:0] = [str(P/'b'), str(P/'tree'), str(P)]
from h1eval.h10.launch import read_records, shard
from h1eval.items import load_manifest, sha, K
from h1eval.cli import code_hash, export_hash, write_curve, modes
from h1eval.modes import mode_key, plan, DEFAULT_MODES
from h1eval.runner import measure, table
from orchard_h10.common import ORDER
journals, out, ntypes = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
T = list(ORDER[:ntypes])
roots = [journals/str(t)/'0' for t in range(ntypes)]
envs = [json.loads((p/'environment.json').read_text()) for p in roots]
first = envs[0]; binding = first['binding']
comparable = lambda b: {k: v for k, v in b.items() if k not in ('shard', 'ids', 'device')}
assert all(comparable(e['binding']) == comparable(binding) for e in envs), 'Shard bindings differ'
assert binding['arms'] == ['own'] and binding['modes'] == [{'name': 'none'}, *modes(DEFAULT_MODES)], 'Type plan differs'
ident = json.loads((journals.parent/'IDENTITY.json').read_text())
assert ident['cards'] == 1 and ident['order'][:ntypes] == T and ident['arms'] == binding['arms'], 'Identity differs'
manifest = load_manifest(P/'items/devs1_routed.json')
assert manifest['item_set_sha256'] == binding['item_set_sha256'], 'Items differ'
assert code_hash() == binding['evaluator_code_sha256'], 'Evaluator changed'
assert sha(K/'rows/expected_calls.py') == binding['expected_calls_sha256'] and sha(K/'tree/student_pilot/h1_r0.py') == binding['r0_code_sha256']
by_id = {r['id']: r for r in manifest['items']}; all_rows = {}
for t, (root, env) in enumerate(zip(roots, envs)):
    b = env['binding']; i, n = shard(b['shard'])
    members = [r['id'] for r in manifest['items'][i::n] if r['question_type'] == T[t]]
    assert b['ids'] == members, 'Shard membership differs'
    expected = plan([by_id[k] for k in b['ids']], b['arms'], b['modes'])
    rows = read_records(root/'items.jsonl'); actual = {(r['id'], r['arm'], r['mode']) for r in rows}
    assert actual == expected, f'Incomplete shard {t}: {len(actual)} vs {len(expected)}'
    for r in rows:
        assert r['intervention'] == next(m for m in b['modes'] if mode_key(m) == r['mode'])
        assert r['room_key'] == by_id[r['id']]['room_key'] and r['type'] == by_id[r['id']]['question_type']
        key = (r['id'], r['arm'], r['mode']); assert key not in all_rows; all_rows[key] = r
sub = [r for r in manifest['items'] if r['question_type'] in T]
assert set(all_rows) == plan(sub, binding['arms'], binding['modes']), 'Union differs from subset plan'
measured = []
for key, r in sorted(all_rows.items()):
    base = all_rows[(r['id'], r['arm'], 'none')]['output'] if r['mode'] != 'none' else None
    measured.append({**r, 'item_set': manifest['name'], 'measurements': measure(r['output'], by_id[r['id']], base)})
out.mkdir(parents=True, exist_ok=False)
(out/'items.jsonl').write_text(''.join(json.dumps(r, allow_nan=False)+'\n' for r in measured))
settings = dict(lineage=binding['lineage'], step=binding['step'], fixture=binding['fixture'], loader_sha256=binding['maker_sha256'])
sub_manifest = {**manifest, 'items': sub, 'count': len(sub)}
curve = write_curve(out, measured, sub_manifest, first['export'], settings, 32, binding['arms'], binding['modes'][1:])
print('export_hash_match', curve['export_sha256'] == binding['export_sha256'], flush=True)
(out/'report.md').write_text(table(measured, manifest.get('constants')))
print(json.dumps(dict(records=len(measured), items=len(sub), types=T)))
print((out/'report.md').read_text())
