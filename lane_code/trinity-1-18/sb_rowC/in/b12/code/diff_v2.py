"""v2 -> vN preservation check: vN must equal v2 minus the rows the review drop rules select, with shared rows equal except
provenance.generator_sha256. Rules are re-derived here from the check files and d0_sets.json, not read from DROPPED.jsonl.
Usage: diff_v2.py ROWS_V2 ROWS_VN -> ROWS_VN/DIFF_V2.json"""
import json, sys, os, glob, collections
W = '/scratch/jjyeung/orch_n30/b12_cntapp/work/'
v2, vn = sys.argv[1:3]
TS = collections.defaultdict(list)
for f in ('ARK_PIN_TS_CHECK.json', 'ARK_PIN_TS_CHECK_K1.json'):
    for a, v in json.load(open(W + f)).items(): TS[a].append(v)
D0 = json.load(open(W + 'd0_sets.json'))
def rule(r):
    a = r['dataset'] + '/' + r['scene']; out = []
    if r['dataset'] == 'd3' and (not TS.get(a) or any(v != 'ok' for v in TS[a])): out.append('alignment')
    if r.get('count_kind') == 'total' and sorted(x['name'] for x in r['provenance']['total_categories']) in D0['total'].get(a, []): out.append('d0_total')
    if r['question_type'] == 'obj_appearance_order' and sorted(r['provenance']['first_seen']) in D0['app'].get(a, []): out.append('d0_app')
    return out
def load(d, sub=''):
    R = {}
    for p in sorted(glob.glob(os.path.join(d, sub, '*.jsonl'))):
        if os.path.basename(p) == 'DROPPED.jsonl': continue
        for l in open(p): r = json.loads(l); R[r['qid']] = (os.path.basename(p)[:-6], r)
    return R
rep = {}
for name, sub in (('packet', ''), ('k1_heldout', 'filtered_k1_heldout')):
    A, B = load(v2, sub), load(vn, sub)
    want = {q: rule(r) for q, (f, r) in A.items() if rule(r)}
    removed, added = set(A) - set(B), set(B) - set(A)
    diffs = collections.Counter(); bad = []
    for q in set(A) & set(B):
        (fa, ra), (fb, rb) = A[q], B[q]
        ra = json.loads(json.dumps(ra)); rb = json.loads(json.dumps(rb))
        ga, gb = ra['provenance'].pop('generator_sha256'), rb['provenance'].pop('generator_sha256'); diffs[(ga[:8], gb[:8])] += 1
        if ra != rb or fa != fb: bad.append(q)
    rep[name] = dict(v2_rows=len(A), vn_rows=len(B), removed=len(removed), added=len(added), rule_rows=len(want),
                     removed_by_rule=dict(collections.Counter('+'.join(want[q]) for q in removed if q in want)),
                     removed_by_family=dict(collections.Counter(A[q][0] for q in removed)),
                     removed_without_rule=sorted(removed - set(want)), rule_rows_kept=sorted(set(want) - removed), added_qids=sorted(added),
                     shared=len(set(A) & set(B)), shared_differing_beyond_generator_sha=sorted(bad),
                     generator_sha_pairs={f'{a}->{b}': n for (a, b), n in diffs.items()},
                     exact=not (removed ^ set(want)) and not added and not bad)
rep['PASS'] = all(v['exact'] for v in rep.values() if isinstance(v, dict))
json.dump(rep, open(os.path.join(vn, 'DIFF_V2.json'), 'w'), indent=1)
print(json.dumps({k: (v if not isinstance(v, dict) else {x: y for x, y in v.items() if not isinstance(y, list) or len(y) < 6}) for k, v in rep.items()}, indent=1))
