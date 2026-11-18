import json
from cd_load import load, as_num, mra
from collections import Counter
D, shas = load()
json.dump(shas, open('SOURCE_SHAS.json','w'), indent=1)
for s in ['dev-S1','R0-dev']:
    base = set(D['S544'][s])
    for ex in D:
        if s not in D[ex]: continue
        ids = set(D[ex][s])
        d = D[ex][s]
        # recompute MRA from extracted answer vs GT
        mism = 0; toolmis = 0; gtdiff = 0
        for i, r in d.items():
            gt = as_num(r['ground_truth']); p = as_num(r['extracted_answer'])
            m = mra(p, gt)
            if abs(m - (r['score'] or 0)) > 1e-9: mism += 1
            if r.get('tool_score') is not None and abs((r['tool_score'] or 0) - (r['score'] or 0)) > 1e-9: toolmis += 1
            if r['released_answer'] is not None and str(r['released_answer']) != str(r['ground_truth']): gtdiff += 1
        print(s, ex, 'n', len(ids), 'same_as_544', ids == base, 'rooms', len({r['room'] for r in d.values()}),
              'mra_recompute_mismatch', mism, 'tool_vs_item_mismatch', toolmis, 'gt!=released', gtdiff,
              'mean', round(100*sum(r['score'] for r in d.values())/len(d), 2),
              'kinds', dict(Counter(r.get('count_kind') for r in d.values())), 'scorer', dict(Counter(r['scorer'] for r in d.values())))
