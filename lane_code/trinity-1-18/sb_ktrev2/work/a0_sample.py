"""Reviewer sample of the N=32 A0 reproduction: every 4th kbox4 reference capture (offset 1).
Imports the delivered code read-only from sb_ktfix/code; writes only into this workspace."""
import os, sys, json, time, collections
from pathlib import Path
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktfix/code')
from common import *
import kbox_hook
rows, binding = kbox_hook.evidence()
kbox_hook.evidence = lambda: (rows, binding)
from replay import price, load_selector
from evaluate import geometry, stored_tower
from policy import captures
W = Path('/scratch/jjyeung/orch_n30/sb_ktrev2/work')
ref = collections.defaultdict(set)
for r in rows:
    ref[r['capture']].add(r['row_id'])
pool = [c for c in captures('train') if c['canonical'] in ref]
sample = pool[1::4]
head = load_selector()
start = time.monotonic(); tot = dict(pool_captures=len(pool), captures=0, rows=0, equal=0, set_equal=0, errors=[], fail_rows=[])
with (W / 'a0_sample.jsonl').open('w') as f:
    for c in sample:
        try:
            own = npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe') / 'own.npz')
            g, _ = geometry(stored_tower(c), own)
            cache = read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'candidates.json')
            got = price(c, g, cache, 32, head=head)
            res = kbox_hook.compare(c, got)
            res['row_set_equal'] = {r['row_id'] for r in got} == ref[c['canonical']]
        except Exception as e:
            res = dict(capture=c['canonical'], status='ERROR', error=repr(e), rows=[], row_set_equal=False); tot['errors'].append(res['error'])
        tot['captures'] += 1; tot['set_equal'] += res['row_set_equal']
        for r in res.get('rows', []):
            tot['rows'] += 1; tot['equal'] += bool(r['equal'])
            if not r['equal']:
                tot['fail_rows'].append(dict(capture=c['canonical'], row_id=r['row_id'], prediction=r['prediction'], reference=r['reference']))
        f.write(json.dumps(clean({k: v for k, v in res.items() if k != 'rows'} | dict(n=len(res.get('rows', [])), n_equal=sum(bool(r['equal']) for r in res.get('rows', []))))) + '\n'); f.flush()
        print(c['canonical'], res['status'], res['row_set_equal'], round(time.monotonic() - start), flush=True)
tot['seconds'] = time.monotonic() - start
tot['sample_reference_rows'] = sum(len(ref[c['canonical']]) for c in sample)
(W / 'a0_sample_summary.json').write_text(json.dumps(clean(tot), indent=1))
print(json.dumps({k: v for k, v in tot.items() if k not in ('fail_rows',)}))
