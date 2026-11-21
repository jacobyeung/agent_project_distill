"""Read-only: which of the job's two row filters drops the rows of the third stream that lie outside
the receipt's train list. Uses the tree's own filter classes on the store the stream build read."""
import importlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); DS = hx('64617461736574'); BSE = hx('62656e63686d61726b') + '_scene_exclusions'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREP = sorted((OQ / 'p').glob('prepare_*'))[0]
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    Exclusions = mod(PK + '.s1_exclusions').Exclusions; Removals = mod(PK + '.row_removals').Removals
    gate = mod(PK + '.scene_division_gate')
    third = load(PREP / 'vqa/receipt.json'); spec = load(pinned(cfg['streams']['pose']))
    a1 = load(pinned(third['division'])); a3 = load(pinned(spec['division']))
    a1t, a3t, a3h = set(a1['train_scenes']), set(a3['train_scenes']), set(a3['heldout_scenes'])
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg[BSE]); removals = Removals(cfg.get('remove_files', []))
    rule2 = Exclusions(cfg['dev_scene_exclusions'], cfg[BSE]); removals2 = Removals(cfg.get('remove_files', []))
    tally, per_scene = Counter(), {}
    conn = sqlite3.connect('file:' + str(OQ / 'twins/rows.sqlite') + '?mode=ro&immutable=1', uri=True)
    for (raw,) in conn.execute('SELECT row FROM rows ORDER BY i'):
        row = json.loads(raw); s = row[DS] + '/' + row['scene']
        k = 'in_run_heldout' if s in a3h else 'in_receipt_list_train' if s in a1t else 'in_run_train_only' if s in a3t else 'in_neither'
        if not rule.keep(row, 'vqa'):
            fate = 'dropped by the scene rule'
        elif not removals.keep(row):
            fate = 'dropped by the removal files'
        else:
            fate = 'kept'
        tally[k + ' | ' + fate] += 1
        if k in ('in_run_train_only', 'in_neither'):
            per_scene.setdefault(k, {}).setdefault(s, Counter())[fate] += 1
            if rule2.keep(row, 'vqa'):
                removals2.keep(row)
    conn.close()
    print('rows the stream build read, by scene class and fate under the job filters:')
    for key in sorted(tally):
        print('   %-55s %d' % (key, tally[key]))
    for k, scenes in per_scene.items():
        print('scenes of class', k, ':', json.dumps({s: dict(c) for s, c in sorted(scenes.items())}))
    for name, obj in (('scene rule report over the outside rows only', rule2), ('removal files report over the outside rows only', removals2)):
        try:
            print(name, ':', json.dumps(obj.report(), sort_keys=True, default=str)[:5000])
        except Exception as error:
            print(name, 'not available:', repr(error))
    print('config scene list pin (the pre-admit gate reads this one):', json.dumps(cfg.get('scene_division')))
print('DONE')
