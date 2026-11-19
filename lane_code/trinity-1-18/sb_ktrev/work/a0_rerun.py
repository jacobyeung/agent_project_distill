"""Reviewer rerun: the kit's N=32 path (price at n=32 on stored C64 geometry) against every kbox4 A0 train row.
Imports the kit's code read-only from sb_ktow3/code; writes only into this reviewer workspace."""
import os, sys, json, time, collections
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktow3/code')
from common import *
import kbox_hook
rows, binding = kbox_hook.evidence()
kbox_hook.evidence = lambda: (rows, binding)
from replay import price, load_selector
from evaluate import geometry, stored_tower
from policy import captures
OUT = Path('/scratch/jjyeung/orch_n30/sb_ktrev/work/a0_rerun.jsonl')
ref = collections.defaultdict(set)
for r in rows:
    ref[r['capture']].add(r['row_id'])
head = load_selector()
start = time.monotonic(); tot = dict(captures=0, rows=0, equal=0, set_equal=0, fail_rows=[])
with OUT.open('w') as f:
    for c in captures('train'):
        if c['canonical'] not in ref:
            continue
        try:
            own = npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe') / 'own.npz')
            g, _ = geometry(stored_tower(c), own)
            cache = read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'candidates.json')
            got = price(c, g, cache, 32, head=head)
            res = kbox_hook.compare(c, got)
            res['row_set_equal'] = {r['row_id'] for r in got} == ref[c['canonical']]
        except Exception as e:
            res = dict(capture=c['canonical'], status='ERROR', error=repr(e), rows=[], row_set_equal=False)
        tot['captures'] += 1; tot['set_equal'] += res['row_set_equal']
        for r in res.get('rows', []):
            tot['rows'] += 1; tot['equal'] += bool(r['equal'])
            if not r['equal']:
                tot['fail_rows'].append(dict(capture=c['canonical'], **{k: r[k] for k in ('row_id', 'prediction', 'reference', 'response', 'reference_response', 'members_equal', 'boxes_equal')}))
        f.write(json.dumps(clean({k: v for k, v in res.items() if k != 'rows'} | dict(n=len(res.get('rows', [])), n_equal=sum(bool(r['equal']) for r in res.get('rows', []))))) + '\n'); f.flush()
        print(c['canonical'], res['status'], res['row_set_equal'], round(time.monotonic() - start), flush=True)
tot['seconds'] = time.monotonic() - start; tot['reference_captures'] = len(ref); tot['reference_rows'] = len(rows)
Path('/scratch/jjyeung/orch_n30/sb_ktrev/work/a0_rerun_summary.json').write_text(json.dumps(clean(tot), indent=1))
print(json.dumps({k: v for k, v in tot.items() if k != 'fail_rows'} | dict(n_fail=len(tot['fail_rows']))))
