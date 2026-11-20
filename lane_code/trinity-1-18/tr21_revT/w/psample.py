import json, re, collections, sys
from pathlib import Path
D = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/work/build24m4v')
sys.path[:0] = ['/scratch/jjyeung/orch_n30/tr21_revT/w/patched']
from student_pilot.extent_receipt import Extents, required, content
from student_pilot.p3_provenance import file_pin, digest
P = json.loads((D/'published/p_sample.json').read_text())
print('p_sample keys', list(P.keys())[:20])
rows = [json.loads(x['row']) for x in P['rows']]
names = json.loads((D/'SOURCES.json').read_text())['names']
pin = file_pin(D/'c072905b.json')
g = Extents(pin, names)
c = collections.Counter()
for r in rows:
    v = {**r, **r['routing']} if isinstance(r.get('routing'), dict) else r
    q = r['qid']; pat = re.sub(r'[0-9]+', 'N', q)
    s1 = r.get('s1_source'); nm = s1.get('name') if isinstance(s1, dict) else None
    e = g.receipt['rows'].get(q)
    try:
        Extents(pin).check(r, 'routing'); before = 'PASS'
    except ValueError as x: before = str(x)
    c[(pat, v.get('question_type'), nm in names if nm else None, bool(r.get('r1_source')), required(r, 'routing'), g.exempt(r, 'routing'), e is not None, e is not None and e.get('content_sha256') == digest(content(r)), before)] += 1
print('pattern, qtype, s1 in list, r1_source, required, exempt, has_entry, entry_matches, C\'\' outcome')
for k, n in sorted(c.items(), key=str): print(n, k)
print('receipt keys', list(g.receipt.keys()), 'rows', len(g.receipt['rows']))
print('receipt sources', json.dumps(g.receipt.get('sources'))[:600])
pats = collections.Counter(re.sub(r'[0-9]+', 'N', q) for q in g.receipt['rows'])
print('receipt qid patterns', pats.most_common(20))
