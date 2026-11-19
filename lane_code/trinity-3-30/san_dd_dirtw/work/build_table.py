"""Per-item table of the 376 R0-dev toward items (steps 544, R1-100, R1-200) -> tw_items.tsv; prints class counts."""
import sys, json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
D = load(); c = D[200]
rows = []
for i, r in c.items():
    if r['subtype'] != 'toward': continue
    lv = LV[r['type']]; o = objs(r['question']); truth = opt(r, r['gt'])
    a = {st: opt(D[st][i], D[st][i]['pred']) for st in (544, 100, 200)}
    sc = {st: D[st][i]['score'] for st in (544, 100, 200)}
    ang = angle544(D[544][i]['text'])
    ans = a[200]
    if sc[200] == 0:
        stab = 'stable' if (sc[544] == 0 and sc[100] == 0 and a[544] == a[100] == a[200]) else ('wrong3diff' if (sc[544] == 0 and sc[100] == 0) else 'unstable')
        ax = axis(lv, truth, ans); L = sep_lines(lv, truth, ans)
        d = min(adist(ang, x) for x in L) if (L and ang is not None) else None
        g = 'd_gross' if ax == 'both' else ('a_boundary' if (d is not None and d <= 25) else ('b_mirror' if ax == 'side' else 'c_frontback'))
    else:
        stab = ax = g = ''; d = None
    rows.append(dict(id=i, lv=lv, room=r['room'], obs=o[0], faced=o[1], target=o[2], truth=truth, a544=a[544], a100=a[100], a200=ans,
                     s544=sc[544], s100=sc[100], s200=sc[200], ang544=(('?%g' % ang[1]) if isinstance(ang, tuple) else ang), stab=stab, axis=ax,
                     d=d, geo=g, fc200=D[200][i]['forced_close']))
cols = list(rows[0].keys())
with open('tw_items.tsv', 'w') as f:
    f.write('\t'.join(cols) + '\n')
    for x in rows: f.write('\t'.join(str(x[k]) for k in cols) + '\n')
W = [x for x in rows if x['s200'] == 0]
print('toward items', len(rows), 'wrong at 200', len(W), collections.Counter(x['lv'] for x in W))
print('stability', sorted(collections.Counter((x['lv'], x['stab']) for x in W).items()))
print('geo x level', sorted(collections.Counter((x['geo'], x['lv']) for x in W).items()))
print('geo x stab', sorted(collections.Counter((x['geo'], x['stab']) for x in W).items()))
print('truth->ans200', sorted(collections.Counter((x['lv'], x['truth'], x['a200']) for x in W).items()))
