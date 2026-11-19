"""Second D@544 remainder: full parent minus (completed IDs of partial 1, recorded in REM544.json) minus (completed IDs of partial 2 = job 173053 of remainder package d09f959256d87).
Uses dresume's own authenticators (unpack, load) on partial 2 and dbuild.make_items_d.subset on the full parent. Usage: python3 make_rem2.py OUT.json"""
import json, sys
sys.path[:0] = ['/scratch/jjyeung/orch_n30/cont_ops18/dresume']
from pathlib import Path
from dbuild.make_items_d import subset
from return_tools import read, unpack, load, validate_manifest
from fetch_validation import digest
P2 = '/dev/shm/c19r/pkg2/a15_cot_apd09f959256d87'; ITEMS2 = '/dev/shm/c19r/rem1_dist580.json'
rem1, expected2 = validate_manifest(ITEMS2, P2)
assert rem1.get('remainder') and digest(ITEMS2) == digest('/scratch/jjyeung/orch_n30/cont_ops18/dresume/REM544.json')
ex = unpack(P2 + '/a/f/0.tgz', P2 + '/a/f/EXIT.json', P2 + '/a/f/RETURN_RECEIPT.json', P2, '/dev/shm/c19r/unpack2')
rows2, _ = load('/dev/shm/c19r/unpack2', ITEMS2, P2)
assert not ex['complete'] and len(rows2) < rem1['count']
done1 = rem1['remainder']['completed_ids']; done2 = sorted(rows2)
assert not set(done1) & set(done2) and set(done2) <= {r['id'] for r in rem1['items']}
parent = rem1['parent_manifest']
prov = dict(rem1['remainder']); prov = {k: v for k, v in prov.items() if k not in ('completed_ids', 'parent_item_set_sha256')}
prov['second_partial'] = dict(plan=expected2['plan'], token=expected2['token'], items_sha256=digest(ITEMS2),
                              partial_archive_sha256=digest(P2 + '/a/f/0.tgz'), partial_return_token=ex['token'], completed=len(done2))
m = subset(parent, sorted(set(done1) | set(done2)), prov)
with Path(sys.argv[1]).open('x') as f:
    json.dump(m, f, sort_keys=True, indent=1, allow_nan=False); f.write('\n')
print(json.dumps(dict(done1=len(done1), done2=len(done2), remaining=m['count'], sets={k: len(v) for k, v in m['sets'].items()}, sha256=digest(sys.argv[1]))))
