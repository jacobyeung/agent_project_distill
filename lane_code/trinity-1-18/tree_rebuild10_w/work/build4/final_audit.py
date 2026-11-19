"""Record final artifact identity and bounded proof results without new stores."""
import hashlib
import json
from pathlib import Path
import sys

L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory

def read(name):
    return json.loads((L/name).read_text())

def sha(name):
    return hashlib.sha256((L/name).read_bytes()).hexdigest()

pins={
    'student_pilot/trace_grammar.py':
        'a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268',
    'student_pilot/r2_dev_merged.json':
        'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5',
}
for name,expected in pins.items():
    assert sha('work/tree_r1/'+name)==expected,name
current=inventory(L/'work/tree_r1')
assert current==read('out/TREE_SEAL.json')['files']
assert all(r['tree_matches'] for r in read('work/build4/FINAL_IDENTITY.json'))
rows=read('work/build4/rows_final_source/RESULTS.json')
old=read('work/build4/rows_complete/RESULTS.json')
assert len(rows)==len(old)
assert all(r['seen']==r['admitted']+r['refused'] for r in rows)
assert all(sum(r['reasons'].values())==r['refused'] for r in rows)
mutations=read('work/build4/review_current/MUTATIONS.json')
assert not any(r['admitted'] for r in mutations)
review=read('work/build4/review_current/SOURCE.json')
assert review==current
delta=read('work/build4/package_final_delta/results.json')
assert not delta['fatal'] and not delta['errors'] and not delta['failures']
record={
    'status':'NOT READY',
    'tree_sha256':read('out/TREE_SEAL.json')['tree_sha256'],
    'tree_inventory_matches':True,
    'kit_tree_identity':'work/build4/FINAL_IDENTITY.json',
    'required_pins':pins,
    'fixture_bytes':sum(p.stat().st_size for p in (L/'fixtures').rglob('*') if p.is_file()),
    'row_families':len(rows),
    'row_totals':{k:sum(r[k] for r in rows) for k in ('seen','admitted','refused','eval_rooms')},
    'row_source':'work/build4/rows_final_source/RESULTS.json',
    'replay_counts_equal':all(all(a[k]==b[k] for k in ('seen','admitted','refused','eval_rooms')) for a,b in zip(rows,old)),
    'review_mutations':len(mutations),
    'review_mutations_all_refused':True,
    'review_source_differences':[name for name in sorted(set(current)|set(review)) if current.get(name)!=review.get(name)],
    'review_source':'work/build4/review_current/SOURCE.json',
    'final_package_delta_tests':delta['tests'],
    'final_package_delta_source':'work/build4/package_final_delta/results.json',
}
(L/'work/build4/FINAL_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
