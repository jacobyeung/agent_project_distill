"""Lane sb_countdesign: the trivial reference for any gated large-set head: when the model's own answer signals a large set
(answer >= 4, or a runaway), answer a constant; otherwise keep the direct answer. All 535 dev counting items. CPU, read-only."""
import json, sys, collections, random
sys.path.insert(0, '../files'); import score_count_pricing as S
items = [json.loads(l) for l in open('../files/COUNT_ITEMS_535.jsonl')]
def num(p):
    try: return float(p)
    except Exception: return None
out = {}
for k in ('S1_544', 'R1_200'):
    for s in ('dev-S1', 'R0-dev'):
        L = [x for x in items if x['set'] == s]
        gate = lambda x: bool(x['direct'][k]['forced_close']) or (num(x['direct'][k]['pred']) is not None and num(x['direct'][k]['pred']) >= 4)
        d = dict(direct=round(100 * sum(x['direct'][k]['score'] for x in L) / len(L), 2), fired=sum(gate(x) for x in L))
        for c in (5, 6, 7):
            sc = [S.mra(c, x['truth']) if gate(x) else x['direct'][k]['score'] for x in L]
            by = collections.defaultdict(list)
            for x, v in zip(L, sc): by[x['room']].append(100 * (v - x['direct'][k]['score']))
            lo, hi = S.boot(by)
            d['const%d_when_large' % c] = [round(100 * sum(sc) / len(sc), 2), round(100 * sum(sc) / len(sc) - d['direct'], 2), round(lo, 2), round(hi, 2)]
            big = [x for x in L if x['truth'] >= 5]
            d['const%d_on_truth5plus' % c] = round(100 * sum(S.mra(c, x['truth']) if gate(x) else x['direct'][k]['score'] for x in big) / len(big), 2)
        # the model's own number on fired large items, for reference
        out['%s|%s' % (k, s)] = d; print(k, s, json.dumps(d))
json.dump(out, open('PRIOR_GATE.json', 'w'), indent=1)
