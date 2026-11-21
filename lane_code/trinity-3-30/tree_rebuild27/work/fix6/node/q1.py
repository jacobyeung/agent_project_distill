"""Read-only questions about the job's prepared state: stream order, the target-filter comparison,
and where the rows of the third stream fall in the two scene lists."""
import importlib, json, os, sqlite3, sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); DS = hx('64617461736574')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREP = sorted((OQ / 'p').glob('prepare_*'))[0]


def scan(args):
    label, db, a1t, a1h, a3t, a3h = args
    conn = sqlite3.connect('file:' + str(db) + '?mode=ro&immutable=1', uri=True)
    counts, scenes, sets, examples = Counter(), defaultdict(set), Counter(), defaultdict(Counter)
    for (row,) in conn.execute('SELECT row FROM rows ORDER BY i'):
        r = json.loads(row); s = r[DS] + '/' + r['scene']
        k = ('in_run_heldout' if s in a3h else 'in_receipt_list_train' if s in a1t else 'in_run_train_only' if s in a3t
             else 'in_receipt_list_heldout' if s in a1h else 'in_neither')
        counts[k] += 1; scenes[k].add(s); sets[(k, r[DS])] += 1
        if k in ('in_run_train_only', 'in_neither'):
            examples[k][s] += 1
    conn.close()
    return label, dict(counts), {k: len(v) for k, v in scenes.items()}, {k[0] + '|' + k[1]: v for k, v in sets.items()}, {k: dict(v.most_common(400)) for k, v in examples.items()}


with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    print('== A. order of the stream names as prepare() walks them (cfg[streams] of c.json, same order in the selected copy):', list(cfg['streams']))
    print('   the job raised at line 542 on the last of them; the ones before it had passed lines 536-561 and their row loop')
    gtf = mod(PK + '.ground_target_filter')
    expected = gtf.TargetFilter(cfg.get('remove_files', ()), shape_filter=True).settings()
    print('== B. lines 543-547: cfg ground_target_filter =', cfg.get('ground_target_filter'), '| remove_files', len(cfg.get('remove_files', ())))
    print('   expected side (TargetFilter(remove_files, shape_filter=True).settings()):', json.dumps(expected, sort_keys=True)[:2500])
    for label, r in (('receipt prepare() compares = rebuilt first-stream receipt ' + str(PREP / 'pointing/receipt.json'), load(PREP / 'pointing/receipt.json')),
                     ('receipt before the rebuild (config pin)', load(pinned(cfg['streams']['pointing'])))):
        got = r.get('target_filter', {}).get('settings')
        print('  ', label); print('      has target_filter:', 'target_filter' in r, '| settings equal expected:', got == expected)
        print('      receipt side:', json.dumps(got, sort_keys=True)[:2500])
    third = load(PREP / 'vqa/receipt.json'); spec = load(pinned(cfg['streams']['pose']))
    a1 = load(pinned(third['division'])); a3 = load(pinned(spec['division']))
    a1t, a1h, a3t, a3h = (set(a1['train_scenes']), set(a1['heldout_scenes']), set(a3['train_scenes']), set(a3['heldout_scenes']))
    print('== C. scene lists: receipt list', third['division']['sha256'][:8], 'train', len(a1t), 'heldout', len(a1h), '| run list', spec['division']['sha256'][:8],
          'train', len(a3t), 'heldout', len(a3h), '| receipt train within run train:', a1t <= a3t, '| run train only:', len(a3t - a1t))
    store = pinned(load(pinned(cfg['r1_training']['store_parameter']))['database'])
    jobs = [('source store named by the config receipt (rows before the added rows)', store, a1t, a1h, a3t, a3h),
            ('store after the added rows (what the stream build read)', OQ / 'twins/rows.sqlite', a1t, a1h, a3t, a3h),
            ('rows the job kept after its filters', PREP / 'vqa/rows.sqlite', a1t, a1h, a3t, a3h)]
    with Pool(3) as pool:
        for label, counts, scenes, per, examples in pool.map(scan, jobs):
            print('  ', label); print('      rows by class:', json.dumps(counts, sort_keys=True)); print('      scenes by class:', json.dumps(scenes, sort_keys=True))
            print('      rows by class and set:', json.dumps(per, sort_keys=True))
            for k, v in examples.items():
                print('      scenes of class', k, '(' + str(len(v)) + ', rows each):', json.dumps(v, sort_keys=True)[:6000])
print('DONE')
