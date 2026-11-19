"""Reviewer rerun: the kit's N=32 path (price at n=32 on stored C64 geometry) against every kbox4 A0 train row.
Imports the kit's code read-only from sb_ktow3/code; writes only into this reviewer workspace."""
import os, sys, json, time, collections
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__);code_pins()
import kbox_hook
rows, binding = kbox_hook.evidence()
kbox_hook.evidence = lambda: (rows, binding)
from replay import price, load_selector
from evaluate import geometry, stored_tower
from policy import captures
OUT = ROOT/'out/fix_validation/a0_rerun.jsonl'
ref = collections.defaultdict(set)
for r in rows:
    ref[r['capture']].add(r['row_id'])
from exclusions import population
pop=population();selected=set(pop['allowed_row_ids']);subset=dict(rows=0,equal=0,captures=0,set_equal=0)
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
        if ref[c['canonical']] & selected:
            subset['captures']+=1;subset['set_equal']+=res['row_set_equal']
            for r in res.get('rows',[]):
                if r['row_id'] in selected:subset['rows']+=1;subset['equal']+=bool(r['equal'])
        tot['captures'] += 1; tot['set_equal'] += res['row_set_equal']
        for r in res.get('rows', []):
            tot['rows'] += 1; tot['equal'] += bool(r['equal'])
            if not r['equal']:
                tot['fail_rows'].append(dict(capture=c['canonical'], **{k: r[k] for k in ('row_id', 'prediction', 'reference', 'response', 'reference_response', 'members_equal', 'boxes_equal')}))
        f.write(json.dumps(clean({k: v for k, v in res.items() if k != 'rows'} | dict(n=len(res.get('rows', [])), n_equal=sum(bool(r['equal']) for r in res.get('rows', [])),input_sha256=dict(INPUTS)))) + '\n'); f.flush()
        print(c['canonical'], res['status'], res['row_set_equal'], round(time.monotonic() - start), flush=True)
tot['subset_1012']=subset;tot['command']='bash scripts/cpu.sh work/a0_rerun.py'
assert subset['rows']==subset['equal']==1012 and subset['captures']==subset['set_equal']==204
tot['seconds'] = time.monotonic() - start; tot['reference_captures'] = len(ref); tot['reference_rows'] = len(rows)
sha(__file__);code_pins()
write_json(ROOT/'out/fix_validation/a0_rerun_summary.json',tot)
assert tot['rows']==tot['equal']==1037 and tot['set_equal']==209 and not tot['fail_rows']
print(json.dumps({k: v for k, v in tot.items() if k != 'fail_rows'} | dict(n_fail=len(tot['fail_rows']))))
