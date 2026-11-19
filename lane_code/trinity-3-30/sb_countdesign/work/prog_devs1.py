"""Lane sb_countdesign: deployed counting program (SAM 3 default density + selector tau 0.15 + learned merge on G3T; lane b08_headrows
CHOICE.per_item.jsonl, mirrored trinity-1-18) against direct answers on dev-S1 counting, by truth bin. CPU, read-only."""
import json, collections, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt
K = cnt.K
rows = json.load(open('PROGRAM_PERITEM_devS1_counting.json'))
per = {}
for run, step in cnt.CK:
    for r in K.direct(run, step, 'dev-S1', types=['object_counting']):
        per.setdefault(r['id'], {})['%s_%d' % (run, step)] = r
byarm = collections.defaultdict(dict)
for r in rows: byarm[r['arm']][r['qid']] = r
P = byarm['step544_B2048']; C = byarm['cues_step544']
print('overlap', len(set(P) & set(per)), 'of', len(per))
def off_mra(pred, gt):
    # official rule without tolerance (reproduces the stored scores, incl. the boundary loss)
    p = float(pred); g = float(gt); rel = abs(p - g) / g
    return sum(1.0 for i in range(10) if rel <= 1 - (0.5 + 0.05 * i)) / 10.0
def tb(g):
    g = int(float(g)); return '2' if g <= 2 else '3' if g == 3 else '4' if g == 4 else '5+'
# does n_selected_total reproduce program score?
ok = 0; n = 0; ex = []
for i in P:
    g = per[i]['R1_200']['gt']; ns = C[i].get('n_selected_total')
    if ns is None: continue
    n += 1; s = off_mra(ns, g)
    if abs(s - P[i]['program']) < 1e-9: ok += 1
    elif len(ex) < 8: ex.append((i, g, ns, P[i]['program'], s, P[i]['no_answer']))
print('n_selected_total reproduces program score on', ok, 'of', n, ex)
out = {}
for b in ('2', '3', '4', '5+'):
    ids = [i for i in per if tb(per[i]['R1_200']['gt']) == b]
    d = dict(n=len(ids), program=100 * sum(P[i]['program'] for i in ids) / len(ids))
    for a in ('parent', 'step544', 'step544_B2048'):
        d['direct_' + a] = 100 * sum(byarm[a][i]['direct'] for i in ids) / len(ids)
    for k in ('S1_544', 'R1_100', 'R1_200'):
        d[k] = 100 * sum((per[i][k]['score'] or 0) for i in ids) / len(ids)
    d['prog_under'] = sum(1 for i in ids if C[i]['n_selected_total'] < float(per[i]['R1_200']['gt']))
    d['prog_over'] = sum(1 for i in ids if C[i]['n_selected_total'] > float(per[i]['R1_200']['gt']))
    d['prog_exact'] = sum(1 for i in ids if C[i]['n_selected_total'] == float(per[i]['R1_200']['gt']))
    out[b] = d
    print('truth', b, json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in d.items()}))
ids = sorted([i for i in per if float(per[i]['R1_200']['gt']) >= 5], key=lambda i: float(per[i]['R1_200']['gt']))
print('n5+', len(ids))
tab = []
for i in ids:
    r = per[i]['R1_200']; g = float(r['gt'])
    tab.append(dict(id=i, gt=g, dataset=P[i]['dataset'], cat=cnt.cats(r['question']), prog_n=C[i]['n_selected_total'], cand_n=C[i]['n_candidates_total'],
                    prog=P[i]['program'], s544=per[i]['S1_544']['score'], p544=per[i]['S1_544']['pred'], s200=r['score'], p200=r['pred'], fc200=r['forced_close']))
    t = tab[-1]
    print(i, 'gt %g' % g, t['dataset'], 'prog_n %g cand_n %g prog %.1f' % (t['prog_n'], t['cand_n'], t['prog']), '| 544: %s %.1f' % (t['p544'], t['s544']), '| 200: %s %.1f fc=%s' % (t['p200'], t['s200'], t['fc200']), t['cat'])
json.dump(dict(bins=out, items5=tab), open('PROGRAM_VS_DIRECT_devS1.json', 'w'), indent=1)
import statistics
print('5+: program %.2f  s544 %.2f  s200 %.2f' % tuple(100 * statistics.mean(t[k] for t in tab) for k in ('prog', 's544', 's200')))
print('5+: ratio prog_n/gt median %.2f; cand_n/gt median %.2f' % (statistics.median(t['prog_n'] / t['gt'] for t in tab), statistics.median(t['cand_n'] / t['gt'] for t in tab)))
for ds in sorted(set(t['dataset'] for t in tab)):
    L = [t for t in tab if t['dataset'] == ds]
    print(ds, len(L), 'program %.1f s544 %.1f s200 %.1f' % tuple(100 * statistics.mean(t[k] for t in L) for k in ('prog', 's544', 's200')))
# best of program count / candidates count rescale (diagnostic)
for name, f in (('prog_n', lambda t: t['prog_n']), ('cand_n', lambda t: t['cand_n']), ('max(prog_n,2)', lambda t: max(t['prog_n'], 2))):
    print(name, '%.2f' % (100 * statistics.mean(off_mra(f(t), t['gt']) for t in tab)))
# paired difference with room bootstrap
import random
random.seed(20261119)
rooms = collections.defaultdict(list)
for t in tab: rooms[per[t['id']]['R1_200']['room']].append(t)
rk = list(rooms)
def boot(key):
    ds = []
    for _ in range(10000):
        S = [x for r in random.choices(rk, k=len(rk)) for x in rooms[r]]
        ds.append(100 * statistics.mean(x['prog'] - x[key] for x in S))
    ds.sort(); return ds[250], ds[9750]
for key in ('s200', 's544'):
    d = 100 * statistics.mean(t['prog'] - t[key] for t in tab); lo, hi = boot(key)
    print('program minus %s on 5+: %+.2f [%+.2f, %+.2f] rooms %d' % (key, d, lo, hi, len(rk)))
